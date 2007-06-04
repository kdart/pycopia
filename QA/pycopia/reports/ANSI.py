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
A standard formatter enhanced to support ANSI terminal color output.

"""

from pycopia import reports
from pycopia import timelib

RESET = "\x1b[0m"
RED = "\x1b[31;01m"
LIGHTRED = "\x1b[31m"
YELLOW = "\x1b[33;01m"
GREEN = "\x1b[32;01m"
BLUE = "\x1b[34;01m"
WHITE = "\x1b[01m"


class ANSIFormatter(reports.StandardFormatter):
    MIMETYPE = "text/ansi"
    _TRANSLATE = {
        "PASSED":GREEN+'PASSED'+RESET,
        "FAILED":RED+'FAILED'+RESET,
        "EXPECTED_FAIL":LIGHTRED+'FAILED'+RESET,
        "ABORTED":YELLOW+'ABORTED'+RESET,
        "INCOMPLETE":YELLOW+'INCOMPLETE'+RESET,
        "ABORT":YELLOW+'ABORT'+RESET,
        "INFO":"INFO",
        "DIAGNOSTIC":WHITE+'DIAGNOSTIC'+RESET,
    }

    def message(self, msgtype, msg, level=1):
        if msgtype.find("TIME") >= 0:
            msg = BLUE+timelib.localtimestamp(msg)+RESET
        msgtype = self._TRANSLATE.get(msgtype, msgtype)
        return "%s%s: %s\n" % ("  "*(level-1), msgtype, msg)

    def summaryline(self, entry):
        text = "%66.66s: %s" % (cut_string(repr(entry)), entry.result)
        text = text.replace("PASSED", self._TRANSLATE["PASSED"])
        text = text.replace("EXPECTED_FAIL", self._TRANSLATE["EXPECTED_FAIL"])
        text = text.replace("FAILED", self._TRANSLATE["FAILED"])
        text = text.replace("INCOMPLETE", self._TRANSLATE["INCOMPLETE"])
        text = text.replace("ABORTED", self._TRANSLATE["ABORTED"])
        return text

def cut_string(s, maxlen=66):
    if len(s) <= maxlen:
        return s
    halflen = (min(maxlen, len(s))/2)-2
    return s[:halflen]+"[..]"+s[-halflen:]

