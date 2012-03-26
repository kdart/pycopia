#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Implment an abstraction of a protocol state machine.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


import re

from pycopia.stringmatch import compile_exact
from pycopia.aid import Enum


class ProtocolExit(Exception):
    pass

class ProtocolError(Exception):
    pass


ANY = compile_exact("")
RESET = Enum(0, "RESET")

# default transition
def transition_error(mo):
    raise ProtocolError('Symbol %r is undefined.' % (mo.string,))


class StateMachine(object):
    ANY = ANY # place here for easy access from other modules
    RESET = RESET
    def __init__(self, initial_state=RESET):
        self._exact_transitions = {}
        self._any_transitions = {}
        self._re_transitions = {}
        self.default_transition = (transition_error, initial_state)
        self.initial_state = initial_state
        self.reset()

    def __str__(self):
        return "StateMachine: state=%r" % (self.current_state,)

    def reset(self):
        self.current_state = self.initial_state
        self.stack = [] # primary stack
        self.altstack = [] # alternate stack

    #  stacks for user
    def push(self, v):
        self.stack.append(v)

    def pop(self):
        return self.stack.pop()

    def pushalt(self, v):
        self.altstack.append(v)

    def popalt(self):
        return self.altstack.pop()

    # transition constructors
    def set_default_transition(self, action, next_state):
        self.default_transition = (action, next_state)

    def add_exact(self, symbol, state, action, next_state):
        if symbol is ANY:
            self._any_transitions[state] = (action, next_state)
        else:
            cre = compile_exact(symbol)
            self._exact_transitions[(symbol, state)] = (cre, action, next_state)

    add = add_exact

    # general add method that knows what you want. ;-)
    def append(self, symbol, state, action, next_state):
        if symbol is ANY:
            self.add_any(state, action, next_state)
        elif is_exact(symbol):
            self.add_exact(symbol, state, action, next_state)
        else:
            self.add_regex(symbol, state, action, next_state)

    def add_any(self, state, action, next_state):
        self._any_transitions[state] = (action, next_state)

    def add_glob(self, expression, state, action, next_state, flags=0):
        self.add_regex(glob_translate(expression), 
                                   state, action, next_state, flags=0)

    def add_regex(self, expression, state, action, next_state, flags=0):
        cre = re.compile(expression, flags)
        try:
            rel = self._re_transitions[state]
        except IndexError:
            rel = self._re_transitions[state] = []
        rel.append((cre, action, next_state))

    def add_list(self, expression_list, state, action, next_state):
        for input_symbol in expression_list:
            self.add_exact(input_symbol, state, action, next_state)

    def step(self, symbol):
        state = self.current_state
        try:
            cre, action, next = self._exact_transitions[(symbol, state)]
            mo = cre.search(symbol)
            if mo:
                self.current_state = next
                if action:
                    action(mo)
                return
        except KeyError:
            pass

        try:
            rel =  self._re_transitions[state]
            for cre, action, next in rel:
                mo = cre.search(symbol)
                if mo:
                    self.current_state = next
                    if action:
                        action(mo)
                    return
        except KeyError:
            pass

        try:
            action, next =  self._any_transitions[state]
            self.current_state = next
            if action:
                action(ANY.search(symbol))
        except KeyError:
            action, next = self.default_transition
            self.current_state = next
            if action:
                action(ANY.search(symbol))


def is_exact(pattern):
    for c in pattern:
        if c in ".^$*?+\\{}(),[]|":
            return False
    return True



class Protocol(object):

    def __init__(self):
        self.states = StateMachine()
        self.iostream = None
        self.initialize(self.states)

    def run(self, iostream):
        states = self.states
        states.reset()
        self.iostream = iostream
        try:
            self.start()
            while 1:
                nextline = iostream.readline()
                if nextline:
                    states.step(nextline)
                else:
                    break
        finally:
            self.iostream = None

    def initialize(self, states):
        """Fill this in with state transitions."""
        return NotImplemented

    def start(self):
        return NotImplemented


def _test(argv):
    from pycopia import IO

    class TestProtocol(Protocol):

        def initialize(self, fsm):
            fsm.set_default_transition(self._error, fsm.RESET)
            fsm.append("GREETINGS\n", fsm.RESET, self._bye, 2)
            fsm.append(fsm.ANY, 2, self._bye, fsm.RESET)

        def start(self):
            self.iostream.write("HELLO type GREETINGS\n")

        def _bye(self, match):
            self.iostream.write("BYE\n")
            raise ProtocolExit

        def _error(self, match):
            self.iostream.write("ERROR\n")

    proto = TestProtocol()
    try:
        proto.run(IO.ConsoleIO())
    except ProtocolExit:
        print("exited")

if __name__ == "__main__":
    from pycopia import autodebug
    import sys
    _test(sys.argv)

