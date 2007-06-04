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

import qatest


def indexerror(idx=0):
    L = []
    s = "string"
    i = 1
    l = 2L
    f = 3.14159265
    return L[idx]

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

class FunctionStack(qatest.Test):
    def test_method(self):
        f5()
        return self.passed()

class MethodStack(qatest.Test):
    def test_method(self):
        b = Buggy()
        b.keyerror("bogus")
        return self.passed()

class SetTrace(qatest.Test):
    def test_method(self):
        x = 1
        self.debug()
        return self.passed()

def run(cf):
    suite = qatest.TestSuite(cf)
    suite.add_test(FunctionStack)
    suite.add_test(MethodStack)
    suite.add_test(SetTrace)

    suite()

