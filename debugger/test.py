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
