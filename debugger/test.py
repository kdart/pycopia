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

Purposly buggy module to test the new debugger.
Run in debug mode.

"""

import unittest

from pycopia import debugger
from pycopia import autodebug

def indexerror(idx=0):
    L = []
    s = "string"
    i = 1
    l = 2L
    f = 3.14159265
    return L[idx] # will raise index error

# functions to get a reasonably sized stack
def f1(*args):
    x = 1
    return indexerror(*args)

def f2(*args):
    x = 2
    return f1(*args)

def f3(*args):
    x = 4
    return f2(*args)

def f4(*args):
    x = 4
    return f3(*args)

def f5(*args):
    x = 5
    return f4(*args)


class Buggy(object):
    def __init__(self):
        self.D = {}

    def keyerror(self, key):
        l = 1
        return self.D[key]


class DebuggerTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_debugger(self):
        """Test documentation."""
        pass
        #f5() # will enter debugger since auto debug enabled.

    def test_debuginclass(self):
        #b = Buggy()
        #b.keyerror("bogus")
        pass

f5() # will enter debugger since auto debug enabled.


if __name__ == '__main__':
    unittest.main()
