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
Fake vim module used for testing vimlib outside of vim itself. Currently,
this means this module mocks the vim module just enough to import vimlib
without errors.

"""

import sys

class error(Exception):
    pass

class Window(object):
    pass

class Current(object):
    pass

class Range(object):
    pass

class Buffer(bytearray):
    pass

def command(s):
    print "vim command:", s

buffers = [Buffer()]
buffers[0].name = "<unknown>"
windows = [Window()]


current = Current()
current.window = windows[0]
current.buffer = buffers[0]
current.line = ""
current.range = Range()

