#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Vulnerability package - client side
===================================

Package for client (usually "attacker") functions and data.

These are used to send various protocols to clientserver.servers.

"""


from pycopia import clientserver


class FlowClient(clientserver.TCPClient):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition("GREETINGS_FROM_SERVER", fsm.RESET, self._greet, 1)
        fsm.add_transition("BYE_FROM_SERVER", 1, self._bye, fsm.RESET)

    def _error(self, s, fsm):
        raise ClientExit, 1

    def _greet(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_CLIENT")
        fsm.writeln("BYE_FROM_CLIENT")

    def _bye(self, s, fsm):
        raise ClientExit, 0


class FlowClient2server(clientserver.TCPClient):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition("GREETINGS_FROM_SERVER2", fsm.RESET, self._greet, 1)
        fsm.add_transition("BYE_FROM_SERVER2", 1, self._bye, fsm.RESET)

    def _error(self, s, fsm):
        raise ClientExit, 1

    def _greet(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_CLIENT2")
        fsm.writeln("BYE_FROM_CLIENT2")

    def _bye(self, s, fsm):
        raise ClientExit, 0

class FlowClient2client(clientserver.TCPClient):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition("GREETINGS_FROM_SERVER3", fsm.RESET, self._greet, 1)
        fsm.add_transition("BYE_FROM_SERVER3", 1, self._bye, fsm.RESET)

    def _error(self, s, fsm):
        raise ClientExit, 1

    def _greet(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_CLIENT3")
        fsm.writeln("BYE_FROM_CLIENT3")

    def _bye(self, s, fsm):
        raise ClientExit, 0


