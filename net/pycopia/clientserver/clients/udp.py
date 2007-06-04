#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
UDP clients.

"""

import sys
from pycopia import clientserver


# the following serves as an example.

class TestUDPClient(clientserver.UDPClient):
    port = 8555
    altport = 8556
    def initialize(self):
        fsm = self.fsm
        fsm.add_transition(fsm.ANY, fsm.RESET, self._greet, 1)
        fsm.add_expression("GREETINGS (.*)", 1, None, 2)
        fsm.add_transition("BYE_FROM_UDPSERVER", 2, self._bye, fsm.RESET)
        fsm.process(fsm.ANY)

    def _greet(self, s, fsm):
        self.send("GREETINGS_FROM_UDPCLIENT")

    def _bye(self, s, fsm):
        self.send("BYE_FROM_UDPCLIENT")
        raise ClientExit, 0


