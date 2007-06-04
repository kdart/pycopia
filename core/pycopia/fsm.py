#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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
This module implements a Finite State Machine (FSM) with two stacks.
The FSM is fairly simple. It is useful for small parsing tasks.

"""

import sre as re

from pycopia.aid import Enum, Enums

class FSMError(Exception):
    pass

_cre = re.compile("test")
SREType = type(_cre)
del _cre

# default state and state Enum constructor
def make_states(*args):
    "converts an argument list of strings to a list of Enum. Use as state transitions."
    return Enums(map(str, args))

ANY = Enum(-1, "ANY")

class FSM(object):
    """This class is a Finite State Machine (FSM).
    You set up a state transition table which is the association of
        (input_symbol, current_state) --> (action, next_state)
    When the FSM matches a pair (current_state, input_symbol)
    it will call the associated action.
    The action is a function reference defined with a signature like this:
            def f (input_symbol, fsm):
    and pass as parameters the input symbol, and the FSM instance itself.
    The action function may produce output and update the stack.
    """
    ANY = ANY

    def __init__(self, initial_state=0):
        self._transitions = {}   # Map (input_symbol, state) to (action, next_state).
        self._expressions = []
        self.default_transition = None
        self.RESET = Enum(0, "RESET") # there is always a RESET state
        self.initial_state = self.RESET
        self._reset()

    # FSM stack for user
    def push(self, v):
        self.stack.append(v)
    def pop(self):
        return self.stack.pop()
    def pushalt(self, v):
        self.altstack.append(v)
    def popalt(self):
        return self.altstack.pop()

    def _reset(self):
        """Rest the stacks and resets the current_state to the initial_state.  """
        self.current_state = self.initial_state
        self.stack = [] # primary stack
        self.altstack = [] # alternate stack

    def reset(self):
        "overrideable user reset."
        self._reset()

    def add_states(self, *args):
        for enum in make_states(*args):
            if not hasattr(self, str(enum)):
                setattr(self, str(enum), enum)
            else:
                raise FSMError, "state or attribute already exists."

    def set_default_transition(self, action, next_state):
        '''This sets the default transition.
        If the FSM cannot match the pair (input_symbol, current_state)
        in the transition table then this is the transition that 
        will be returned. This is useful for catching errors and undefined states.
        The default transition can be removed by calling
        add_default_transition (None, None)
        If the default is not set and the FSM cannot match
        the input_symbol and current_state then it will 
        raise an exception (see process()).
        '''
        if action == None and next_state == None:
            self.default_transition = None
        else:
            self.default_transition = (action, next_state)
    add_default_transition = set_default_transition # alias

    def add_transition(self, input_symbol, state, action, next_state):
        '''This adds an association between inputs and outputs.
                (input_symbol, current_state) --> (action, next_state)
           The action may be set to None.
           The input_symbol may be set to None.  '''
        self._transitions[(input_symbol, state)] = (action, next_state)

    def add_expression(self, expression, state, action, next_state, flags=0):
        """Adds a transition that activates if the input symbol matches the
        regular expression. The action callable gets a match object instead of
        the symbol."""
        cre = re.compile(expression, flags)
        self._expressions.append( (cre, state, action, next_state) )
        self._transitions[(SREType, state)] = (self._check_expression, None)

    # self-action to match against expressions
    def _check_expression(self, symbol, myself):
        for cre, state, action, next_state in self._expressions:
            mo = cre.match(symbol)
            if state is self.current_state and mo:
                if action is not None:
                    action(mo, self)
                self.current_state = next_state

    def add_transition_list(self, list_input_symbols, state, action, next_state):
        '''This adds lots of the same transitions for different input symbols.
        You can pass a list or a string. Don't forget that it is handy to use
        string.digits, string.letters, etc. to add transitions that match 
        those character classes.
        '''
        for input_symbol in list_input_symbols:
            self.add_transition (input_symbol, state, action, next_state)

    def get_transition(self, input_symbol, state):
        '''This tells what the next state and action would be 
        given the current state and the input_symbol.
        This returns (action, new state).
        This does not update the current state
        nor does it trigger the output action.
        If the transition is not defined and the default state is defined
        then that will be used; otherwise, this throws an exception.
        '''
        try:
            return self._transitions[(input_symbol, state)]
        except KeyError:
            try:
                return self._transitions[(ANY, state)]
            except KeyError:
                try:
                    return self._transitions[(SREType, state)]
                except KeyError:
                    # no expression matched, so check for default
                    if self.default_transition is not None:
                        return self.default_transition
                    else:
                        raise FSMError, 'Transition %r is undefined.' % (input_symbol,)

    def process(self, input_symbol):
        """This causes the fsm to change state and call an action.
        (input_symbol, current_state) --> (action, next_state)
        If the action is None then no action is taken,
        only the current state is changed.  """
        action, next_state = self.get_transition(input_symbol, self.current_state)
        if action is not None:
            action(input_symbol, self)
        if next_state is not None:
            self.current_state = next_state

    def step(self, token):
        """This causes the fsm to change state and call an action.
        (token, current_state) --> (action, next_state) If the action is
        None then no action is taken, only the current state is changed.    """
        action, next_state = self.get_transition(token, self.current_state)
        if action is not None:
            rv = action(token, self)
            if rv is None: 
                if next_state is not None:
                    self.current_state = next_state
            else: # returning a value from a method sets the state, else take the FSM defined default.
                self.current_state = rv
        elif next_state is not None:
            self.current_state = next_state

    def process_string(self, s):
        for c in s:
            self.process(c)

if __name__ == '__main__':
    pass

