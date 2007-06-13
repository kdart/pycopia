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
Fake vim module used for testing vimlib outside of vim itself. Currently,
this means this module mocks the vim module just enough to import vimlib
without errors.

"""

import sys
from pycopia import charbuffer

class error(Exception):
    pass

class Window(object):
    pass

class Current(object):
    pass

class Range(object):
    pass

def command(s):
    print "vim command:", s

buffers = [charbuffer.Buffer()]
buffers[0].name = "<unknown>"
windows = [Window()]


current = Current()
current.window = windows[0]
current.buffer = buffers[0]
current.line = ""
current.range = Range()

