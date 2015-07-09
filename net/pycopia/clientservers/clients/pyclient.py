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


