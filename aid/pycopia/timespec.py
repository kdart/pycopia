#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#
#    Copyright (C) Keith Dart <keith@kdart.com>
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


from pycopia.fsm import FSM, ANY
from pycopia import textutils


class TimespecParser(object):
    """Loose time span parser. 
    Convert strings such as "1day 3min" to seconds.
    The attribute "seconds" holds the updated value, after parsing.
    """
    def __init__(self):
        self._seconds = 0.0
        f = FSM(0)
        f.arg = ""
        f.add_default_transition(self._error, 0)
        f.add_transition_list(textutils.digits + "+-", 0, self._newdigit, 1)
        f.add_transition_list(textutils.digits, 1, self._addtext, 1)
        f.add_transition(".", 1, self._addtext, 2)
        f.add_transition_list(textutils.digits, 2, self._addtext, 2)
        f.add_transition_list("dhms", 1, self._multiplier, 3)
        f.add_transition_list("dhms", 2, self._multiplier, 3)
        f.add_transition_list(textutils.letters, 3, None, 3)
        f.add_transition_list(textutils.whitespace, 3, None, 3)
        f.add_transition_list(textutils.digits + "+-", 3, self._newdigit, 1)
        self._fsm = f

    seconds = property(lambda s: s._seconds)

    def _error(self, input_symbol, fsm):
        fsm.reset()
        raise ValueError('TimeParser error: %s\n%r' % (input_symbol, fsm.stack))

    def _addtext(self, c, fsm):
        fsm.arg += c

    def _newdigit(self, c, fsm):
        fsm.arg = c

    def _multiplier(self, c, fsm):
        m = {"d": 86400.0, "h": 3600.0, "m": 60.0, "s": 1.0}[c]
        v = float(fsm.arg)
        fsm.arg = ""
        self._seconds += (v*m)

    def parse(self, string):
        self._fsm.reset()
        self._seconds = 0.0
        self._fsm.process_string(string)
        if self._fsm.arg:
            self._seconds += float(self._fsm.arg) 
            self._fsm.arg = ""
        return self._seconds


def parse_timespan(string):
  p = TimespecParser()
  p.parse(string)
  return p.seconds


