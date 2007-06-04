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
A minimal lisp implementation in Python. 8-)

Tries to leverage Python's existing functional style features.

"""


import new
from operator import *


def car(args):
    return args[0]

def cdr(args):
    return args[1:]

def cons(arg1, arg2):
    return [arg1, arg2]

def quote(args):
    return args

def eq(arg1, arg2):
    return arg2 == arg2

def neq(arg1, arg2):
    return arg2 != arg2

#def IF(cond, tv, fv):
#   if cond:
#       return tv
#   else:
#       return fv

# XXX needs work
def defun(name, args, impl):
    code = compile(impl, "defun_%s" % (name,), "exec")
    f = new.function(code, {}, name, args)
    return f


def _test(argv):
    pass # XXX

if __name__ == "__main__":
    import sys
    _test(sys.argv)

