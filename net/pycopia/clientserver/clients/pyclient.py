#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Python object client.

"""

from pycopia import clientserver


class PyObjectClient(clientserver.TCPClient):
    port = 8155
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition("GREETINGS_FROM_SERVER", fsm.RESET, self._greet, 1)
        fsm.add_transition("BYE_FROM_SERVER", 1, self._bye, fsm.RESET)
# XXX

    def _error(self, s, fsm):
        raise ClientExit, 1

    def _greet(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_CLIENT")
        fsm.writeln("BYE_FROM_CLIENT")

    def _bye(self, s, fsm):
        raise ClientExit, 0


