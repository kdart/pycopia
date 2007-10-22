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
Various test reports and formatters are defined here. These are used for
unit test and test framework reporting.

Generally, you don't use this package in the normal way. Instead, you call
the 'get_report' function in this module with a particular pattern of
paramters and it will return a report object according to that. Any
necessary report objects and modules are specified there, and imported as
necessary.

e.g.:

     get_report( ("StandardReport", "reportfile", "text/plain") )

Note that the argument is a single tuple. A list of these may be supplied
for a "stacked" report. 

The first argument is a report object name (plus module, if necessary).
Any remaining argumments in the tuple are passed to the specified reports
constructor.

"""

__all__ = ['ANSI', 'Eventlog', 'Curses', 'Html', 'Email']

import sys, os
from pycopia import UserFile
from pycopia import timelib

NO_MESSAGE = "no message"

# map mime type to formatter class name and file extension
_FORMATTERS = {
    None: ("StandardFormatter", "txt"), # default
    "text/plain": ("StandardFormatter", "txt"), # plain text
    "text/ascii": ("StandardFormatter", "asc"), # plain text
    "text/html": ("pycopia.reports.Html.XHTMLFormatter", "html"), # HTML 
    "text/ansi": ("pycopia.reports.ANSI.ANSIFormatter", "ansi"), # text with ANSI-term color escapes
    "text/ansi; charset=utf8": ("pycopia.reports.utf8ANSI.UTF8Formatter", "ansi"),
}

# register another formatter object that adheres to the NullFormatter
# interface.
def register_formatter(mimetype, classpath, fileextension):
    global _FORMATTERS
    _FORMATTERS[mimetype] = (classpath, fileextension)

class ReportError(Exception):
    pass

class ReportFindError(ReportError):
    pass

class BadReportError(ReportError):
    pass

class NullFormatter(object):
    def title(self, title):
        return ""
    def heading(self, text, level=1):
        return ""
    def paragraph(self, text, level=1):
        return ""
    def summaryline(self, line):
        return ""
    def message(self, msgtype, msg, level=1):
        return ""
    def passed(self, msg=NO_MESSAGE, level=1):
        return self.message("PASSED", msg, level)
    def failed(self, msg=NO_MESSAGE, level=1):
        return self.message("FAILED", msg, level)
    def expectedfail(self, msg=NO_MESSAGE, level=1):
        return self.message("EXPECTED_FAIL", msg, level)
    def incomplete(self, msg=NO_MESSAGE, level=1):
        return self.message("INCOMPLETE", msg, level)
    def abort(self, msg=NO_MESSAGE, level=1):
        return self.message("ABORT", msg, level)
    def info(self, msg, level=1):
        return self.message("INFO", msg, level)
    def diagnostic(self, msg, level=1):
        return self.message("DIAGNOSTIC", msg, level)
    def text(self, text):
        return text
    def url(self, text, url):
        return ""
    def page(self):
        return ""
    def endpage(self):
        return ""
    def section(self):
        return ""
    def endsection(self):
        return ""
    def initialize(self, *args):
        return ""
    def finalize(self):
        return ""

class NullReport(object):
    """NullReport defines the interface for report objects. It is the base
    class for all Report objects."""
    # overrideable methods
    def write(self, text):
        raise NotImplementedError, "override me!"
    def writeline(self, text=""):
        raise NotImplementedError, "override me!"
    def writelines(self, lines):
        raise NotImplementedError, "override me!"
    filename = property(lambda s: None)
    filenames = property(lambda s: [])
    def initialize(self, config=None): pass
    def logfile(self, filename): pass
    def finalize(self): pass
    def add_title(self, title): pass
    def add_heading(self, text, level=1): pass
    def add_message(self, msgtype, msg, level=1): pass
    def add_summary(self, entries): pass
    def add_text(self, text): pass
    def add_data(self, data, datatype, note=None): pass
    def add_url(self, text, url): pass
    def passed(self, msg=NO_MESSAGE, level=1): pass
    def failed(self, msg=NO_MESSAGE, level=1): pass
    def expectedfail(self, msg=NO_MESSAGE, level=1): pass
    def incomplete(self, msg=NO_MESSAGE, level=1): pass
    def abort(self, msg=NO_MESSAGE, level=1): pass
    def info(self, msg, level=1): pass
    def diagnostic(self, msg, level=1): pass
    def newpage(self): pass
    def newsection(self): pass

class DebugReport(NullReport):
    """Used for debugging tests and reports. Just emits plain messages.
    """
    # overrideable methods
    def write(self, text):
        raise NotImplementedError, "override me!"
    def writeline(self, text=""):
        raise NotImplementedError, "override me!"
    def writelines(self, lines):
        raise NotImplementedError, "override me!"
    filename = property(lambda s: "")
    filenames = property(lambda s: [])
    def initialize(self, config=None):
        print "initialize: %r" % (config,)
    def logfile(self, filename):
        print "logfile:", filename
    def finalize(self):
        print "finalize"
    def add_title(self, title):
        print "add_title:", title
    def add_heading(self, text, level=1):
        print "add_heading:", repr(text), level
    def add_message(self, msgtype, msg, level=1):
        print "add_message:", msgtype, repr(msg), level
    def add_summary(self, entries):
        print "add_summary"
    def add_text(self, text):
        print "add_text"
    def add_data(self, data, datatype, note=None):
        print "add_data type: %s note: %s" % (datatype, note)
    def add_url(self, text, url):
        print "add_url:", repr(text), repr(url)
    def passed(self, msg=NO_MESSAGE, level=1):
        print "passed:", repr(msg), level
    def failed(self, msg=NO_MESSAGE, level=1):
        print "failed:", repr(msg), level
    def expectedfail(self, msg=NO_MESSAGE, level=1):
        print "expected fail:",repr(msg), level
    def incomplete(self, msg=NO_MESSAGE, level=1):
        print "incomplete:", repr(msg), level
    def abort(self, msg=NO_MESSAGE, level=1):
        print "abort:", repr(msg), level
    def info(self, msg, level=1):
        print "info:", repr(msg), level
    def diagnostic(self, msg, level=1):
        print "diagnostic:", repr(msg), level
    def newpage(self):
        print "newpage"
    def newsection(self):
        print "newsection"


class StandardReport(UserFile.FileWrapper, NullReport):
    """StandardReport writes to a file or file-like object, such as stdout. If
the filename specified is "-" then use stdout.  """
    def __init__(self, name=None, formatter=None):
        self._do_close = 0
        self._formatter, self.fileext = get_formatter(formatter)
        if type(name) is str:
            if name == "-":
                fo = sys.stdout
            else:
                name = "%s.%s" % (name, self.fileext)
                fo = open(os.path.expanduser(os.path.expandvars(name)), "w")
                self._do_close = 1
        elif name is None:
            fo = sys.stdout
        else:
            fo = name # better be a file object
        UserFile.FileWrapper.__init__(self, fo)
    
    filename = property(lambda s: s._fo.name)
    filenames = property(lambda s: [s._fo.name])

    def initialize(self, config=None):
        self.write(self._formatter.initialize())

    def finalize(self):
        self.write(self._formatter.finalize())
        self.flush()
        if self._do_close:
            self.close()

    def add_title(self, title):
        self.write(self._formatter.title(title))

    def add_heading(self, text, level=1):
        self.write(self._formatter.heading(text, level))

    def add_message(self, msgtype, msg, level=1):
        self.write(self._formatter.message(msgtype, msg, level))

    def passed(self, msg=NO_MESSAGE, level=1):
        self.write(self._formatter.passed(msg, level))

    def failed(self, msg=NO_MESSAGE, level=1):
        self.write(self._formatter.failed(msg, level))

    def expectedfail(self, msg=NO_MESSAGE, level=1):
        self.write(self._formatter.expectedfail(msg, level))

    def incomplete(self, msg=NO_MESSAGE, level=1):
        self.write(self._formatter.incomplete(msg, level))

    def abort(self, msg=NO_MESSAGE, level=1):
        self.write(self._formatter.abort(msg, level))

    def info(self, msg, level=1):
        self.write(self._formatter.info(msg, level))

    def diagnostic(self, msg, level=1):
        self.write(self._formatter.diagnostic(msg, level))

    def add_text(self, text):
        self.write(self._formatter.text(text))

    def add_data(self, data, datatype, note=None):
        self.write(self._formatter.text(
                        "  DATA type: %s note: %s\n" % (datatype, note)))

    def add_url(self, text, url):
        self.write(self._formatter.url(text, url))

    def add_summary(self, entries):
        lines = map(self._formatter.summaryline, entries)
        self.write("\n".join(lines))
        self.write("\n")

    def newpage(self):
        self.write(self._formatter.page())

    def newsection(self):
        self.write(self._formatter.section())


class StandardFormatter(NullFormatter):
    """The Standard formatter just emits plain ASCII text."""
    MIMETYPE = "text/plain"
    def title(self, title):
        s = ["="*len(title)]
        s.append("%s" % title)
        s.append("="*len(title))
        s.append("\n")
        return "\n".join(s)

    def heading(self, text, level=1):
        s = ["\n"]
        s.append("%s%s" % ("  "*(level-1), text))
        s.append("%s%s" % ("  "*(level-1), "-"*len(text)))
        s.append("\n")
        return "\n".join(s)

    def message(self, msgtype, msg, level=1):
        if msgtype.find("TIME") >= 0:
            msg = timelib.localtimestamp(msg)
        return "%s%s: %s\n" % ("  "*(level-1), msgtype, msg)

    def text(self, text):
        return text

    def url(self, text, url):
        return "%s: <%s>\n" % (text, url)

    def summaryline(self, s):
        s = str(s)
        if len(s) <= 66:
            return s
        halflen = (min(66, len(s))/2)-2
        return s[:halflen]+"[..]"+s[-halflen:]

    def page(self):
        return "\n\n\n"

    def section(self):
        return "\n"

    def paragraph(self, text, level=1):
        return text+"\n"


class FailureReport(StandardReport):
    "FailureReport() A Report type that only prints failures and diagnostics."
    def __init__(self, name=None, formatter=None):
        StandardReport.__init__(self, name, formatter)
        self.state = 0

    def add_message(self, msgtype, msg, level=1):
        if msgtype == "FAILED":
            self.state = -1
            self.write(self._formatter.message(msgtype, msg, level))
        else:
            if self.state == -1 and msgtype == "DIAGNOSTIC":
                self.write(self._formatter.message(msgtype, msg, level))
            else:
                self.state = 0

class TerseReport(StandardReport):
    "TerseReport() A Report type that only prints results."
    def __init__(self, name=None, formatter=None):
        StandardReport.__init__(self, name, formatter)

    def add_message(self, msgtype, msg, level=1):
        if msgtype  in ("PASSED", "FAILED"):
            self.write(self._formatter.message(msgtype, msg, level))

    #def add_title(self, title): pass
    def add_heading(self, text, level=1): pass
    def add_summary(self, entries): pass
    def add_text(self, text): pass
    def add_url(self, text, url): pass


class StackedReport(object):
    """StackedReport allows stacking of reports, which creates multiple
    reports simultaneously.  It adds a new method, add_report() that is
    used to add on a new report object. """ 
    def __init__(self, rpt=None):
        self._reports = []
        if rpt:
            self.add_report(rpt)

    def add_report(self, rpt_or_name, *args):
        """adds a new report to the stack."""
        if type(rpt_or_name) is str:
            rpt = get_report(rpt_or_name, *params )
            self._reports.append(rpt)
        elif isinstance(rpt_or_name, NullReport):
            self._reports.append(rpt_or_name)
        else:
            raise BadReportError, "StackedReport: report must be name of report or report object."

    def _get_names(self):
        rv = []
        for rpt in self._reports:
            fn = rpt.filename
            if fn:
                rv.append(fn)
        return rv
    filenames = property(_get_names)

    def add_title(self, title):
        map(lambda rpt: rpt.add_title(title), self._reports)

    def write(self, text):
        map(lambda rpt: rpt.write(text), self._reports)

    def writeline(self, text):
        map(lambda rpt: rpt.writeline(text), self._reports)

    def writelines(self, text):
        map(lambda rpt: rpt.writelines(text), self._reports)

    def add_heading(self, text, level=1):
        map(lambda rpt: rpt.add_heading(text, level), self._reports)

    def add_message(self, msgtype, msg, level=1):
        map(lambda rpt: rpt.add_message(msgtype, msg, level), self._reports)

    def passed(self, msg=NO_MESSAGE, level=1):
        map(lambda rpt: rpt.passed(msg, level), self._reports)

    def failed(self, msg=NO_MESSAGE, level=1):
        map(lambda rpt: rpt.failed(msg, level), self._reports)

    def expectedfail(self, msg=NO_MESSAGE, level=1):
        map(lambda rpt: rpt.expectedfail(msg, level), self._reports)

    def incomplete(self, msg=NO_MESSAGE, level=1):
        map(lambda rpt: rpt.incomplete(msg, level), self._reports)

    def abort(self, msg=NO_MESSAGE, level=1):
        map(lambda rpt: rpt.abort(msg, level), self._reports)

    def info(self, msg, level=1):
        map(lambda rpt: rpt.info(msg, level), self._reports)

    def diagnostic(self, msg, level=1):
        map(lambda rpt: rpt.diagnostic(msg, level), self._reports)

    def add_text(self, text):
        map(lambda rpt: rpt.add_text(text), self._reports)

    def add_data(self, data, datatype, note=None):
        map(lambda rpt: rpt.add_data(data, datatype, note), self._reports)

    def add_url(self, text, url):
        map(lambda rpt: rpt.add_url(text, url), self._reports)

    def add_summary(self, entries):
        map(lambda rpt: rpt.add_summary(entries), self._reports)

    def newpage(self):
        map(lambda rpt: rpt.newpage(), self._reports)

    def logfile(self, fn):
        map(lambda rpt: rpt.logfile(fn), self._reports)

    def initialize(self, config=None):
        map(lambda rpt: rpt.initialize(config), self._reports)

    def finalize(self):
        map(lambda rpt: rpt.finalize(), self._reports)


# Try to return an object from this module. If that fails, import and
# return the object given by the pathname (dot-delimited path to class).
def _get_object(name):
    try:
        return getattr(sys.modules[__name__], name)
    except AttributeError:
        i = name.rfind(".")
        if i >= 0:
            modname = name[:i]
            try:
                mod = sys.modules[modname]
            except KeyError:
                try:
                    mod = __import__(modname, globals(), locals(), ["*"])
                except ImportError, err:
                    raise ReportFindError, \
                        "Could not find report module %s: %s" % (modname, err)
            try:
                return getattr(mod, name[i+1:])
            except AttributeError:
                    raise ReportFindError, \
                        "Could not find report object: %s" % (name,)
        else:
            raise ReportFindError, "%s is not a valid object path." % (name,)


def get_report(args):
    """
    If args is a list, it should contain argument-tuples that specify a series
    of reports. A StackedReport object will be generated in that case.
    Otherwise, args should be a tuple, with first arg the name of a report or
    None (for StandardReport), and remaining args get passed to report
    initializer.  
    """

    if type(args) is list:
        rpt = StackedReport()
        for subargs in args:
            n = get_report(subargs)
            rpt.add_report(n)
        return rpt
    name = args[0]
    if name is None:
        return apply(StandardReport, args[1:])
    robj = _get_object(name)
    if not hasattr(robj, "info"):
        raise ReportFindError, "%s is not a valid report object." % (name,)
    return apply(robj, args[1:])

def get_formatter(name, *args):
    objname, ext = _FORMATTERS.get(name, (name, "txt"))
    fobj = _get_object(objname)
    form = apply(fobj, args)
    return form, ext


if __name__ == "__main__":
    rpt = get_report( ("StandardReport", "-", "text/plain") )
    rpt.initialize()
    rpt.add_title("The Title")
    rpt.add_heading("Some heading")
    rpt.info("some info")
    rpt.passed("A message for a passed condition.")
    rpt.finalize()

