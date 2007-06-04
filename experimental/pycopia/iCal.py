#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Create and parse iCalendar (.ics) files.

Implements RFC 2445.

"""

import sys, os
import sre as re
import datetime
from time import time

import guid
from fsm import FSM, ANY
import inet.ABNF as ABNF

CR     = ABNF.CR
LF     = ABNF.LF
CRLF   = ABNF.CRLF
WSP    = ABNF.WSP
DQUOTE = ABNF.DQUOTE
DIGIT  = ABNF.DIGIT
ALPHA  = ABNF.ALPHA
HTAB   = ABNF.HTAB

# control chars
CTL    = ABNF.CharRange(0x00,0x08) + ABNF.CharRange(0x0A,0x1F) + chr(0x7F)

# Use restricted by charset parameter
# on outer MIME object (UTF-8 preferred)
NON_US_ASCII    = ABNF.CharRange(0x80, 0xf8)

# Any character except CTLs and DQUOTE
QSAFE_CHAR = WSP + chr(0x21) + ABNF.CharRange(0x23, 0x7E) + NON_US_ASCII

# Any character except CTLs, DQUOTE, ";", ":", ","
SAFE_CHAR  = WSP + chr(0x21) + ABNF.CharRange(0x23,0x2B) + \
            ABNF.CharRange(0x2D,0x39) + ABNF.CharRange(0x3C,0x7E) + \
            NON_US_ASCII

# Any character except CTLs not needed by the current
# character set, DQUOTE, ";", ":", "\", ","
TSAFE_CHAR = ABNF.CharRange(0x20,0x21) + ABNF.CharRange(0x23,0x2B) + \
             ABNF.CharRange(0x2D,0x39) + ABNF.CharRange(0x3C,0x5B) + \
             ABNF.CharRange(0x5D,0x7E) + NON_US_ASCII

# \\ encodes \, \N or \n encodes newline
# \; encodes ;, \, encodes ,
ESCAPED_CHAR = "\\;,\n" #  / "\;" / "\," / "\N" / "\n")

TEXT       = TSAFE_CHAR + ":" + DQUOTE + ESCAPED_CHAR

# Any textual character
VALUE_CHAR = WSP + ABNF.CharRange(0x21,0x7E) + NON_US_ASCII

IANA_TOKEN = ALPHA + DIGIT + "-" # subsumes x-token also


SECONDS_PER_DAY=24*60*60
DEFAULTFOLDER = os.path.expanduser("~/Calendars")

class iCalError(Exception):
    pass

class iCalSyntaxError(iCalError):
    pass
add_exception(iCalSyntaxError)

class _iCalFSM(FSM):
    def reset(self):
        self._reset()
        self.arg = ''
        self.cl_name = None
        self.cl_params = {}
        self.cl_value = None


class ICalReader(object):
    def __init__(self):
        self._contenthandler = None
        self._errorhandler = None
        self._initfsm()

    def setContentHandler(self, handler):
        assert isinstance(handler, _HandlerBase), "must be handler object."
        self._contenthandler = handler
    
    def getContentHandler(self):
        return self._contenthandler

    def setErrorHandler(self, handler):
        self._errorhandler = handler
    
    def getErrorHandler(self):
        return self._errorhandler

    def parse(self, url):
        import urllib2
        fo = urllib2.urlopen(url)
        try:
            self.parseFile(fo)
        finally:
            fo.close()
    
    # parser unfolds folded strings
    def parseFile(self, fo):
        self._contenthandler.startDocument()
        lastline = ''
        savedlines = []
        while 1:
            line = fo.readline()
            if not line:
                if lastline:
                    line = "".join(savedlines)+lastline
                    self._process_line(line)
                break
            if not lastline:
                lastline = line
                continue
            if line[0] in WSP:
                savedlines.append(lastline.rstrip())
                lastline = line[1:]
                continue
            if savedlines:
                newline = "".join(savedlines)+lastline
                savedlines = []
                self._process_line(newline)
                lastline = line
            else:
                self._process_line(lastline)
                lastline = line
        self._contenthandler.endDocument()

    def _process_line(self, line):
        self._fsm.process_string(line)
        self._fsm.reset()

    # construct the iCalendar parser per rfc2445.
    def _initfsm(self):
        # state names:
        [NAME,   SLASH,   QUOTE,   SLASHQUOTE,   PARAM,   PARAMNAME,   VALUE,
         ENDLINE,   PARAMVAL,   PARAMQUOTE,   VSLASH,
        ] = Enums(
        "NAME", "SLASH", "QUOTE", "SLASHQUOTE", "PARAM", "PARAMNAME", "VALUE",
        "ENDLINE", "PARAMVAL", "PARAMQUOTE", "VSLASH",
              )
        f = _iCalFSM(NAME)
        f.add_default_transition(self._error, NAME)
        # 
        f.add_transition_list(IANA_TOKEN, NAME, self._addtext, NAME)
        f.add_transition(":", NAME, self._endname, VALUE)
        f.add_transition(";", NAME, self._endname, PARAMNAME)
        f.add_transition_list(VALUE_CHAR, VALUE, self._addtext, VALUE)
        f.add_transition(CR, VALUE, None, ENDLINE)
        f.add_transition(LF, ENDLINE, self._doline, NAME)
        # parameters
        f.add_transition_list(IANA_TOKEN, PARAMNAME, self._addtext, PARAMNAME)
        f.add_transition("=", PARAMNAME, self._endparamname, PARAMVAL)

        f.add_transition_list(SAFE_CHAR, PARAMVAL, self._addtext, PARAMVAL)
        f.add_transition(",", PARAMVAL, self._nextparam, PARAMVAL)
        f.add_transition(";", PARAMVAL, self._nextparam, PARAMNAME)

        f.add_transition(DQUOTE, PARAMVAL, self._startquote, PARAMQUOTE)
        f.add_transition_list(QSAFE_CHAR, PARAMQUOTE, self._addtext, PARAMQUOTE)
        f.add_transition(DQUOTE, PARAMQUOTE, self._endquote, PARAMVAL)

        f.add_transition(":", PARAMVAL, self._nextparam, VALUE)

        # slashes
        f.add_transition("\\", VALUE, None, VSLASH)
        f.add_transition(ANY, VSLASH, self._slashescape, VALUE)
#       f.add_transition("\\", QUOTE, None, SLASHQUOTE)
#       f.add_transition(ANY, SLASHQUOTE, self._slashescape, QUOTE)
#       # double quotes 
#       f.add_transition(DQUOTE, xxx, None, QUOTE)
#       f.add_transition(DQUOTE, QUOTE, self._doublequote, xxx)
#       f.add_transition(ANY, QUOTE, self._addtext, QUOTE)
        f.reset()
        self._fsm = f

    def _error(self, c, fsm):
        if self._errorhandler:
            self._errorhandler(c, fsm)
        else:
            fsm.reset()
            raise iCalSyntaxError, 'Syntax error: %s\n%r' % (c, fsm.stack)

    def _addtext(self, c, fsm):
        fsm.arg += c

    _SPECIAL = {"r":"\r", "n":"\n", "t":"\t", "N":"\n"}
    def _slashescape(self, c, fsm):
        fsm.arg += ICalReader._SPECIAL.get(c, c)

#   def _doublequote(self, c, fsm):
#       self.arg_list.append(fsm.arg)
#       fsm.arg = ''

    def _startquote(self, c, fsm):
        fsm.arg = ''

    def _endquote(self, c, fsm):
        paramval = fsm.arg
        fsm.arg = ''
        fsm.cl_params[fsm.cl_paramname].append(paramval)

    def _endname(self, c, fsm):
        fsm.cl_name = ABNF.Literal(fsm.arg)
        fsm.arg = ''

    def _endparamname(self, c, fsm):
        name = ABNF.Literal(fsm.arg)
        fsm.cl_params[name] = []
        fsm.cl_paramname = name
        fsm.arg = ''

    def _nextparam(self, c, fsm):
        paramval = fsm.arg
        fsm.arg = ''
        fsm.cl_params[fsm.cl_paramname].append(paramval)

    def _doline(self, c, fsm):
        value = fsm.arg
        fsm.arg = ''
        self._contenthandler.handleLine(fsm.cl_name, fsm.cl_params, value)


#class ContentLine(object):
#   def __init__(self, name, parameters, value):
#       self.name = name
#       self.parameters = parameters
#       self.value = value
#
#   def __repr__(self):
#       cl = self.__class__
#       return "%s.%s(%r, %r, %r)" % (cl.__module__, cl.__name__, 
#                   self.name, self.parameters, self.value)


#class Paramter(object):
#   def __init__(self, name, *values):
#       self.name = name
#       self.values = list(values)
#   
#   def __str__(self):
#       return "%s=%s" % (self.name, ",".join(map(icalquote, self.values)))




class _HandlerBase(object):

    def handleLine(self, name, paramdict, value):
        pass

    def startDocument(self):
        pass

    def endDocument(self):
        pass
    
    def startVevent(self):
        pass
    
    def endVevent(self):
        pass
    
    def startVTodo(self):
        pass
    
    def endVTodo(self):
        pass

    def startVJournal(self):
        pass
    
    def endVJournal(self):
        pass
    
    def startVFreebusy(self):
        pass
    
    def endVFreebusy(self):
        pass


class TestHandler(_HandlerBase):
    def handleLine(self, name, paramdict, value):
        print "%r %r %r" % (name, paramdict, value)

    def startDocument(self):
        print "*** startDocument"

    def endDocument(self):
        print "*** endDocument"
    
    def startVevent(self):
        print "*** startVevent"
    
    def endVevent(self):
        print "*** startVevent"
    
    def startVTodo(self):
        print "*** startVTodo"
    
    def endVTodo(self):
        print "*** endVTodo"

    def startVJournal(self):
        print "*** startVJournal"
    
    def endVJournal(self):
        print "*** endVJournal"
    
    def startVFreebusy(self):
        print "*** startVFreebusy"
    
    def endVFreebusy(self):
        print "*** endVFreebusy"


class ICalHandler(_HandlerBase):
    pass


#### iCal objects #####

# Value types
class _iCalTypeBase(object):
    _name = None
    def __init__(self, val=None):
        if val is not None:
            self.value = self._coerce(val)
        else:
            self.value = None

    def __str__(self):
        return "VALUE=%s" % self._name

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.value)
    
    def parse(self, text):
        raise NotImplementedError, "override 'parse' in subclass."
    

class TypeBinary(_iCalTypeBase):
    _name = "BINARY"

class TypeBoolean(_iCalTypeBase):
    _name = "BOOLEAN"

class TypeCalAddress(_iCalTypeBase):
    _name = "CAL-ADDRESS"

class TypeDate(_iCalTypeBase):
    _name = "DATE"

class TypeDateTime(_iCalTypeBase):
    _name = "DATE-TIME"

class TypeDuration(_iCalTypeBase):
    _name = "DURATION"

class TypeFloat(_iCalTypeBase):
    _name = "FLOAT"

class TypeInteger(_iCalTypeBase):
    _name = "INTEGER"

class TypePeriod(_iCalTypeBase):
    _name = "PERIOD"

class TypeRecur(_iCalTypeBase):
    _name = "RECUR"

class TypeText(_iCalTypeBase):
    _name = "TEXT"

class TypeTime(_iCalTypeBase):
    _name = "TIME"

class TypeURI(_iCalTypeBase):
    _name = "URI"

class TypeUTCOffset(_iCalTypeBase):
    _name = "UTC-OFFSET"


# parameters of properties
class _ParameterBase(object):
    def __init__(self, name, values):
        self.name = name
        self.values = values



# properties of components
class _PropertyBase(object):
    _defaulttype = None
    _name = None
    def __init__(self, parameters=None, value=None):
        self.parameters = parameters
        self.value = value
    

class Value(_PropertyBase):
    _defaulttype = None
    _name = "VALUE"



# top level iCal componenets
class _ComponentBase(object):
    _name = None
    def __init__(self):
        self.properties = []
    
    def __str__(self):
        s = ["START:%s" % self._name]
        for prop in self.properties:
            s.append(str(prop))
        s.append("END:%s" % self._name)
        return "\r\n".join(s)
    
    def emit(self, fo):
        fo.write("START:%s\r\n" % self._name)
        for prop in self.properties:
            fo.write(str(prop))
        fo.write("END:%s\r\n" % self._name)

class VEvent(_ComponentBase):
    _name = "VEVENT"

class VTodo(_ComponentBase):
    _name = "VTODO"

class VJournal(_ComponentBase):
    _name = "VJOURNAL"

class VFreebusy(_ComponentBase):
    _name = "VFREEBUSY"

class VTimezone(_ComponentBase):
    _name = "VTIMEZONE"


class ICalDocument(object):
    def __init__(self, encoding=None):
        self._components = []
        self.encoding = encoding

    def append(self, comp):
        self._components.append(comp)
    
    def __str__(self):
        s = []
        for comp in self._components:
            s.append(str(comp))
        return "".join(s)
    
    def emit(self, fo):
        for comp in self._components:
            comp.emit(fo)


def icalquote(s):
    s = s.replace('\\', '\\\\')
    s = s.replace(":", "\\:")
    s = s.replace(";", "\\;")
    s = s.replace('"', '\\"')
    s = s.replace(',', '\\,')
    return s



##### XXXX legacy: ####
class ICalEvent(object):
    def __init__(self):
        self.exceptionDates = []
        self.dateSet = None

    def __str__(self):
        return self.summary

    def __eq__(self, otherEvent):
        return self.startDate == otherEvent.startDate

    def addExceptionDate(self, date):
        self.exceptionDates.append(date)

    def addRecurrenceRule(self, rule):
        self.dateSet = DateSet(self.startDate, self.endDate, rule)

    def startsToday(self):
        return self.startsOn(datetime.datetime.today())

    def startsTomorrow(self):
        tomorrow = datetime.datetime.fromtimestamp(time() + SECONDS_PER_DAY)
        return self.startsOn(tomorrow)

    def startsOn(self, date):
        return (self.startDate.year == date.year and
                self.startDate.month == date.month and
                self.startDate.day == date.day or
                (self.dateSet and self.dateSet.includes(date)))

    def startTime(self):
        return self.startDate



_re_freq     = re.compile("FREQ=(.*?);", re.I)
_re_count    = re.compile("COUNT=(\d*)", re.I)
_re_until    = re.compile("UNTIL=(.*?);", re.I)
_re_interval = re.compile("INTERVAL=(\d*)", re.I)
_re_bymonth  = re.compile("BYMONTH=(.*?);", re.I)
_re_byday    = re.compile("BYDAY=(.*?);", re.I)


class DateSet(object):
    def __init__(self, startDate, endDate, rule):
        self.startDate = startDate
        self.endDate = endDate
        self.frequency = None
        self.count = None
        self.untilDate = None
        self.byMonth = None
        self.byDate = None
        self.parseRecurrenceRule(rule)
    
    def parseRecurrenceRule(self, rule):
        mo = _re_freq.match(rule)
        if mo:
            self.frequency = mo.group(1)
        
        mo = _re_count.match(rule)
        if mo:
            self.count = int(mo.group(1))

        mo = _re_until.match(rule)
        if mo:
            self.untilDate = DateParser.parse(mo.group(1))

        mo = _re_interval.match(rule)
        if mo:
            self.interval = int(mo.group(1))

        mo = _re_bymonth.match(rule)
        if mo:
            self.byMonth = mo.group(1)

        mo = _re_byday.match(rule)
        if mo:
            self.byDay = mo.group(1)


    def includes(self, date):
        if date == self.startDate:
            return True

        if self.untilDate and date > self.untilDate:
            return False

        if self.frequency == 'DAILY':
            increment = 1
            if self.interval:
                increment = self.interval
            d = self.startDate
            counter = 0
            while(d < date):
                if self.count:
                    counter += 1
                    if counter >= self.count:
                        return False

                d = d.replace(day=d.day+1)

                if (d.day == date.day and
                    d.year == date.year and
                    d.month == date.month):
                    return True
            
        elif self.frequency == 'WEEKLY':
            if self.startDate.weekday() == date.weekday():
                return True
            else:
                if self.endDate:
                    for n in range(0, self.endDate.day - self.startDate.day):
                        newDate = self.startDate.replace(day=self.startDate.day+n)
                        if newDate.weekday() == date.weekday():
                            return True

        elif self.frequency == 'MONTHLY':
            pass

        elif self.frequency == 'YEARLY':
            pass

        return False

##### end XXXX legacy ####


if __name__ == '__main__':
    ics = sys.argv[1]
    reader = ICalReader()
    handler = TestHandler()
    reader.setContentHandler(handler)
    fo = file(ics)
    try:
        reader.parseFile(fo)
    finally:
        fo.close()

