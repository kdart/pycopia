#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
# $Id$
#
#    Copyright (C) 1999-2004  Keith Dart <keith@kdart.com>
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

from pycopia import reports
from pycopia import timelib

RESET = "\x1b[0m"
RED = "\x1b[31m"
LIGHTRED = "\x1b[31m"
YELLOW = "\x1b[33;01m"
GREEN = "\x1b[32m"
BLUE = "\x1b[34;01m"
WHITE = "\x1b[01m"
BROWN = "\x1b[33m"


_BOXCHARS = {1: [u'┏', u'━', u'┃', u'┓', u'┗', u'┛',],
             2: [u'╔', u'═', u'║', u'╗', u'╚', u'╝',],
             3: [u'┌', u'─', u'│', u'┐', u'└', u'┘',],
}


class UTF8Formatter(reports.NullFormatter):

    MIMETYPE = "text/ansi; charset=utf-8"
    _TRANSLATE = {
        "PASSED": GREEN + u'✔'.encode("utf8") + RESET,
        "FAILED": RED + u'✘'.encode("utf8") + RESET,
        "EXPECTED_FAIL": LIGHTRED + u'✘'.encode("utf8") + RESET,
        "ABORTED": YELLOW + u'‼'.encode("utf8") + RESET,
        "INCOMPLETE": YELLOW + u'⁇'.encode("utf8") + RESET,
        "ABORT": YELLOW + u'‼'.encode("utf8") + RESET,
        "INFO": u"ℹ".encode("utf8"),
        "DIAGNOSTIC": WHITE + u"ℹ".encode("utf8") + RESET,
    }

    def message(self, msgtype, msg, level=1):
        if msgtype.find("TIME") >= 0:
            msg = BLUE + timelib.localtimestamp(msg) + RESET
        msgtype = self._TRANSLATE.get(msgtype, msgtype)
        return "%s %s\n" % (msgtype, msg)


    def summaryline(self, entry):
        text = "%66.66s: %s" % (cut_string(repr(entry)), entry.result)
        text = text.replace("PASSED", self._TRANSLATE["PASSED"])
        text = text.replace("EXPECTED_FAIL", self._TRANSLATE["EXPECTED_FAIL"])
        text = text.replace("FAILED", self._TRANSLATE["FAILED"])
        text = text.replace("INCOMPLETE", self._TRANSLATE["INCOMPLETE"])
        text = text.replace("ABORTED", self._TRANSLATE["ABORTED"])
        return text

    def title(self, title):
        s = [title.center(80)]
        line = (u"═"*len(title)).center(80)
        s.append(line.encode("utf8"))
        s.append("\n")
        return "\n".join(s)


    def heading(self, text, level=1):
        lt = len(text)
        bl = _BOXCHARS[level]
        s = [bl[0] + (bl[1] * lt) + bl[3] + u"\n"]
        s.append(bl[2] + unicode(text, "ascii") + bl[2] + u"\n")
        s.append(bl[4] + (bl[1] * lt) + bl[5] + u"\n")
        s.append(u"\n")
        return u"".join(s).encode("utf8")

    def text(self, text):
        return text

    def url(self, text, url):
        return "%s: %s<%s>%s\n" % (text, BROWN, url, RESET)

    def page(self):
        return "\n\n\n"

    def section(self):
        return "\n"

    def paragraph(self, text, level=1):
        return (unicode(text, "ascii")+unichr(0xB6)).encode("utf8")


def cut_string(s, maxlen=66):
    if len(s) <= maxlen:
        return s
    halflen = (min(maxlen, len(s))/2)-2
    return s[:halflen]+"[..]"+s[-halflen:]

