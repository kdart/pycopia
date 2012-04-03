#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>
# $Id$

"""
Clientserver Server Package
===========================

Package for server-side engines.

These are usually used for testing various client-side engines. Generally run on
victim agents.

"""

from pycopia import clientserver



# The following server as examples.

class FlowServer(clientserver.TCPWorker):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition(fsm.ANY, fsm.RESET, self._start, 1)
        fsm.add_transition("GREETINGS_FROM_CLIENT", 1, None, 2)
        fsm.add_transition("BYE_FROM_CLIENT", 2, self._bye, fsm.RESET)
        fsm.step(fsm.ANY) # kickstart the protocol

    def _start(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_SERVER")

    def _bye(self, s, fsm):
        fsm.writeln("BYE_FROM_SERVER")
        raise ServerExit

class FlowServer2server(clientserver.TCPWorker):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition(fsm.ANY, fsm.RESET, self._start, 1)
        fsm.add_transition("GREETINGS_FROM_CLIENT2", 1, None, 2)
        fsm.add_transition("BYE_FROM_CLIENT2", 2, self._bye, fsm.RESET)
        fsm.step(fsm.ANY)

    def _start(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_SERVER2")

    def _bye(self, s, fsm):
        fsm.writeln("BYE_FROM_SERVER2")
        raise ServerExit


class FlowServer2client(clientserver.TCPWorker):
    port = 8555
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition(fsm.ANY, fsm.RESET, self._start, 1)
        fsm.add_transition("GREETINGS_FROM_CLIENT3", 1, None, 2)
        fsm.add_transition("BYE_FROM_CLIENT3", 2, self._bye, fsm.RESET)
        fsm.step(fsm.ANY) # kickstart the protocol

    def _start(self, s, fsm):
        fsm.writeln("GREETINGS_FROM_SERVER3")

    def _bye(self, s, fsm):
        fsm.writeln("BYE_FROM_SERVER3")
        raise ServerExit



