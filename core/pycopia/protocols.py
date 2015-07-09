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
Implment an abstraction of a protocol state machine.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


import sys
import re

from pycopia.stringmatch import compile_exact
from pycopia.aid import Enum


class ProtocolExit(Exception):
    """Raise when the protocol completes."""
    pass

class ProtocolError(Exception):
    """Raise when the protocol transition is invalid."""
    pass


RESET = Enum(0, "RESET")
ANY = Enum(-1, "ANY")

# default transition
def transition_error(text):
    raise ProtocolError('Symbol {!r} is undefined.'.format(text))


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
                action(symbol)
        except KeyError:
            action, next = self.default_transition
            self.current_state = next
            if action:
                action(symbol)

    # transition constructors
    def set_default_transition(self, action, next_state):
        self.default_transition = (action, next_state)

    def add_exact(self, symbol, state, action, next_state):
        cre = compile_exact(symbol)
        self._exact_transitions[(symbol, state)] = (cre, action, next_state)

    # general add method that knows what you want. ;-)
    def add(self, symbol, state, action, next_state):
        if symbol is ANY:
            self._any_transitions[state] = (action, next_state)
        elif is_exact(symbol):
            self.add_exact(symbol, state, action, next_state)
        else:
            self.add_regex(symbol, state, action, next_state)

    def add_any(self, state, action, next_state):
        self._any_transitions[state] = (action, next_state)

    def add_glob(self, expression, state, action, next_state):
        self.add_regex(glob_translate(expression),
                                   state, action, next_state)

    def add_regex(self, expression, state, action, next_state,
            ignore_case=False, multiline=False):
        cre = re.compile(expression, _get_re_flags(ignore_case, multiline))
        try:
            rel = self._re_transitions[state]
            rel.append((cre, action, next_state))
        except KeyError:
            self._re_transitions[state] = [(cre, action, next_state)]

    def add_list(self, expression_list, state, action, next_state):
        for input_symbol in expression_list:
            self.add_exact(input_symbol, state, action, next_state)


def is_exact(pattern):
    for c in pattern:
        if c in ".^$*?+\\{}(),[]|":
            return False
    return True



class Protocol(object):
    """Implement the actions for the state machine. Add bound methods to it."""
    EOL = "\n"

    def __init__(self, eol=None):
        self.states = StateMachine()
        self.iostream = None
        self.data = None # extra data action handlers might use.
        self.eol = eol or self.EOL
        self.initialize(self.states)

    def __str__(self):
        if self.iostream is None:
            return "Protocol: fsm: {}. current: {}, Not running.".format(
                    self.states, self.states.current_state)
        else:
            return "Protocol: fsm: {},\n  current: {},\n  iostream: {}".format(
                    self.states, self.states.current_state, self.iostream)

    def log(self, *args):
        print(*args, file=sys.stderr)

    def run(self, iostream, data=None):
        self.iostream = iostream
        self.data = data
        states = self.states
        states.reset()
        self.start()
        try:
            while 1:
                nextline = iostream.readline()
                if nextline:
                    states.step(nextline)
                else:
                    break
        finally:
            self.iostream = None
            self.data = None

    def step(self, iostream, data=None):
        self.iostream = iostream
        self.data = data
        try:
            nextline = iostream.readline()
            if nextline:
                self.states.step(nextline)
            else:
                raise ProtocolExit("No more data")
        finally:
            self.iostream = None
            self.data = None

    def close(self):
        self.states = None
        self.iostream = None

    def initialize(self, states):
        """Fill this in with state transitions."""
        raise NotImplementedError

    def start(self):
        return NotImplemented

    def reset(self):
        self.states.reset()

    def writeln(self, data):
        self.iostream.write(data + self.eol)


def _get_re_flags(ignore_case, multiline):
    flags = 0
    if ignore_case:
        flags |= re.I
    if multiline:
        flags |= re.M
    return flags


if __name__ == "__main__":
    from pycopia import autodebug
    from pycopia import IO

    class TestProtocol(Protocol):

        def initialize(self, fsm):
            fsm.set_default_transition(self._error, fsm.RESET)
            fsm.add("GREETINGS\n", fsm.RESET, self._bye, 2)
            fsm.add(fsm.ANY, 2, self._bye, fsm.RESET)

        def start(self):
            self.writeln("HELLO type GREETINGS")

        def _bye(self, match):
            self.writeln("BYE")
            raise ProtocolExit

        def _error(self, symbol):
            self.writeln("ERROR")

    proto = TestProtocol()
    try:
        proto.run(IO.ConsoleIO())
    except ProtocolExit:
        print("exited")
