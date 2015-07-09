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
A report type the produces an event log with time stamps.

"""

from pycopia import reports
from pycopia import timelib
now = timelib.time


class LogFormatter(reports.StandardFormatter):
    MIMETYPE = "text/plain"

    def message(self, msgtype, msg, level=1):
        if msgtype.find("TIME") >= 0:
            msg = timelib.localtimestamp(msg)
        return "%s:%s: %s\n" % (now(), msgtype, msg)

    def summaryline(self, text):
        return "%s:%s:\n" % (now(), "SUMMARY")


