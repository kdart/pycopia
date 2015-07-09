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
Server side of pyserver. Python objects over a socket.

"""

from pycopia import clientserver


# The following server as examples.

class PyObjectWorker(clientserver.TCPWorker):
    port = 8155
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition(fsm.ANY, fsm.RESET, self._start, 1)
# XXX
        fsm.add_transition("GREETINGS_FROM_CLIENT", 1, None, 2)
        fsm.add_transition("BYE_FROM_CLIENT", 2, self._bye, fsm.RESET)
        fsm.step(fsm.ANY) # kickstart the protocol

    def _start(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_SERVER")

    def _bye(self, s, fsm):
        fsm.writeln("BYE_FROM_SERVER")
        raise ServerExit

