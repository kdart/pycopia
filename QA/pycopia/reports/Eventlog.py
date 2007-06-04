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


