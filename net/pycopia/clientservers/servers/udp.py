#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
UDP Servers.

"""

from pycopia import clientserver

# An example UDP server for testing.

class TestUDPServer(clientserver.UDPWorker):
    port = 8555
    altport = 8556
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_expression("GREETINGS_FROM_(.*)", fsm.RESET, self._greet, 1)
        fsm.add_expression("BYE_FROM_(.*)", 1, self._bye, fsm.RESET)

    def _error(self, s, fsm):
        raise ServerExit, 1

    def _greet(self, mo, fsm):
        self.send("GREETINGS %s" % (mo.group(1),))
        self.send("BYE_FROM_UDPSERVER")

    def _bye(self, mo, fsm):
        raise ServerExit, 0

