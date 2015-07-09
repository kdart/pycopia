#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    halflen = (min(maxlen, len(s))//2)-2
    return s[:halflen]+"[..]"+s[-halflen:]

