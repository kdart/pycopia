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
Objects for constructing, parsing, and editing rfc 2822 compliant messages
(plus extensions).

"""

from pycopia.inet.ABNF import *
from pycopia.fsm import FSM, ANY
from pycopia.aid import IF, Enums

SPECIALS = '()<>@,:;."[]'
LWS = WSP

EXTRA = "!#$%&'*+-/=?^_`{|}~"
ATEXT = ALPHA+DIGIT+EXTRA

HEADBREAK = CRLF+CRLF

FOLDED   = sre.compile(r'%s([%s]+)' % (CRLF, WSP))


class RFC2822Error(Exception):
    pass

class RFC2822SyntaxError(RFC2822Error):
    pass

class _RFC2822FSM(FSM):
    def reset(self):
        self._reset()
        self.arg = ''
        self.cl_name = None
        self.cl_params = {}
        self.cl_value = None


def unfold(s):
    """Unfold a folded string, keeping line breaks and other white space."""
    return FOLDED.sub(r"\1", s)

def headerlines(bigstring):
    """Yield unfolded lines from a chunk of text."""
    bigstring = unfold(bigstring)
    for line in bigstring.split(CRLF):
        yield line


def get_headers(fo):
    s = []
    b = 4
    while 1:
        data = fo.read(80)
        if not data:
            break
        i = data.find(HEADBREAK)
        if i == -1:
            # catch HEADBREAK split across chunks
            if data.startswith("\r"):
                if s[-1].endswith("\r\n"):
                    b = 2
                    break
            elif data.startswith("\n"):
                if s[-1].endswith("\r\n\r"):
                    b = 1
                    break
            else:
                s.append(data)
                continue
        else:
            s.append(data[:i+4])
            break
    rv = []
    for line in headerlines("".join(s)):
        if line:
            rv.append(getHeader(line))
    return rv, data[i+b:]


def getHeader(line):
    [name, val] = line.split(":", 1)
    return Header(name.strip(), val.lstrip())

def get_headers_dict(fo):
    headers, left = get_headers(fo)
    rv = Headers()
    for h in headers:
        rv[h.name] = h.value
    return rv, left

class Header(object):
    """base class for header objects."""
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s: %s" % (self.name, self.value)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.value)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name.upper() ==  other.name.upper()
    def __ne__(self, other):
        return self.name.upper() !=  other.name.upper()
    def __lt__(self, other):
        return self.name.upper() <  other.name.upper()
    def __gt__(self, other):
        return self.name.upper() >  other.name.upper()
    def __le__(self, other):
        return self.name.upper() <=  other.name.upper()
    def __ge__(self, other):
        return self.name.upper() >=  other.name.upper()



# concrete header fields. These encapsulate any special rules for methods for
# its kind. The names of these are significant... the actual heading value is
# taken from it with some translation applied.
class Return_Path(Header):
    def __str__(self):
        return "%s: %s" % (self.NAME, IF(self.data, self.value, "<>"))

class Date(Header):
    def __init__(self, timevalue=None):
        Header.__init__(self)
        self.value = timevalue

    def __str__(self):
        return "%s: %s" % (self.name, formatdate(self.value) )

class From(Header):
    pass

class Sender(Header):
    pass

class Reply_To(Header):
    pass

class To(Header):
    pass

class Cc(Header):
    pass

class Bcc(Header):
    pass

class Message_ID(Header):
    pass

class In_Reply_To(Header):
    pass

class References(Header):
    pass

class Subject(Header):
    pass

class Comments(Header):
    pass

class Keywords(Header):
    pass

class Resent_Date(Header):
    pass

class Resent_From(Header):
    pass

class Resent_Sender(Header):
    pass

class Resent_To(Header):
    pass

class Resent_Cc(Header):
    pass

class Resent_Bcc(Header):
    pass

class Resent_Message_ID(Header):
    pass

class Return_Path(Header):
    pass

class Recieved(Header):
    pass



##### message parts #####

class Headers(dict):
    """A Collection of headers. No duplicates allowed here."""

    def __setitem__(self, name, ho):
        dict.__setitem__(self, name.lower(), ho)

    def __delitem__(self, name):
        dict.__delitem__(self, name.lower())

    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name.lower())
        except KeyError:
            return None
    
    def get(self, key, default=None):
        return dict.get(self, key.lower(), default)

    def emit(self, fo):
        for h in self.values():
            fo.write(str(h))


class Body(object):
    def __init__(self, text=""):
        self.text = str(text)
    
    def __str__(self):
        return self.text
    
    def emit(self, fo):
        fo.write(self.text)

class Message(object):
    """Represents an email message."""
    def __init__(self, header, body=None):
        self.header = header
        self.body = body or Body()

    def __str__(self):
        return str(self.header)+"\n\n"+str(self.body)
    
    def emit(self, fo):
        self.header.emit(fo)
        fo.write("\n\n")
        self.body.emit(fo)


class QuotedString(object):
    """QuotedString(data)
    Represents an quoted string. Automatically encodes the value.
    """
    def __init__(self, val):
        self.data = val
    def __str__(self):
        return quote(str(self.data))
    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.data)
    def parse(self, data):
        self.data = unquote(data)


class Comment(object):
    """A header comment. """
    def __init__(self, item):
        self.data = item
    def __str__(self):
        return "( %s )" % (self.item)

class Address(object):
    def __init__(self, address, name=None):
        self.address = address
        self.name = name

    def __str__(self):
        if self.name:
            return '"%s" <%s>' % (self.name, self.address)
        else:
            return str(self.address)

    def __len__(self):
        return len(str(self))

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.address, self.name)

    def __eq__(self, other):
        try:
            return self.address == other.address and self.name == other.name
        except AttributeError:
            return str(self) == str(other) # other might just be a string

    def __ne__(self, other):
        try:
            return self.address != other.address or self.name != other.name
        except AttributeError:
            return str(self) != str(other) # other might just be a string


class AddressList(list):

    def append(self, address, name=None):
        super(AddressList, self).append(Address(address, name))
    add = append

    def insert(self, i, address, name=None):
        super(AddressList, self).insert(i, Address(address, name))

    def __str__(self):
        return ", ".join(map(str, self))


def formatdate(timeval=None):
    """Returns time format preferred for Internet standards.

    Sun, 06 Nov 1994 08:49:37 GMT  ; RFC 822, updated by RFC 1123

    According to RFC 1123, day and month names must always be in
    English.  If not for that, this code could use strftime().  It
    can't because strftime() honors the locale and could generated
    non-English names.
    """
    from pycopia import timelib
    if timeval is None:
        timeval = timelib.time()
    timeval = timelib.gmtime(timeval)
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][timeval[6]],
            timeval[2],
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][timeval[1]-1],
                                timeval[0], timeval[3], timeval[4], timeval[5])





class RFC2822Parser(object):
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

    # XXX
    def _initfsm(self):
        # state names:
        [NAME,   SLASH,   QUOTE,   SLASHQUOTE,   PARAM,   PARAMNAME,   VALUE,
         ENDLINE,   PARAMVAL,   PARAMQUOTE,   VSLASH,
        ] = Enums(
        "NAME", "SLASH", "QUOTE", "SLASHQUOTE", "PARAM", "PARAMNAME", "VALUE",
        "ENDLINE", "PARAMVAL", "PARAMQUOTE", "VSLASH",
              )
        f = _RFC2822FSM(NAME)
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
            raise RFC2822SyntaxError, 'Syntax error: %s\n%r' % (c, fsm.stack)

    def _addtext(self, c, fsm):
        fsm.arg += c

    _SPECIAL = {"r":"\r", "n":"\n", "t":"\t", "N":"\n"}
    def _slashescape(self, c, fsm):
        fsm.arg += self._SPECIAL.get(c, c)

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



class _HandlerBase(object):

    def handleLine(self, name, paramdict, value):
        pass

    def startDocument(self):
        pass

    def endDocument(self):
        pass
    


class TestHandler(_HandlerBase):
    def handleLine(self, name, paramdict, value):
        print "%r %r %r" % (name, paramdict, value)

    def startDocument(self):
        print "*** startDocument"

    def endDocument(self):
        print "*** endDocument"
    


class BufferedFile(object):
    def __init__(self):
        # The last partial line pushed into this object.
        self._partial = ''
        # The list of full, pushed lines, in reverse order
        self._lines = []
        # A flag indicating whether the file has been closed or not.
        self._closed = False

    def close(self):
        # Don't forget any trailing partial line.
        self._lines.append(self._partial)
        self._partial = ''
        self._closed = True

    def readline(self):
        return '' # XXX
        pass

    def unreadline(self, line):
        self._lines.append(line)

    def push(self, data):
        pass

    def pushlines(self, lines):
        # Reverse and insert at the front of the lines.
        self._lines[:0] = lines[::-1]

    def is_closed(self):
        return self._closed

    def __iter__(self):
        return self

    def next(self):
        line = self.readline()
        if line == '':
            raise StopIteration
        return line


