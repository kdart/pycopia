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
Input/Output objects.

"""

import sys

# wraps stdio to look like a single read-write object. Also provides
# additional io methods.  The termtools.PagedIO object should have all the
# same methods as this class.

class ConsoleIO(object):
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        # reading methods
        self.read = self.stdin.read
        self.readline = self.stdin.readline
        self.readlines = self.stdin.readlines
        self.xreadlines = self.stdin.xreadlines
        # writing methods
        self.write = self.stdout.write
        self.flush = self.stdout.flush
        self.writelines = self.stdout.writelines
    
    def raw_input(self, prompt=""):
        return raw_input(prompt)

    def close(self):
        self.stdout = None
        self.stdin = None
        self.closed = 1
        del self.read, self.readlines, self.xreadlines, self.write
        del self.flush, self.writelines

    def fileno(self): # ??? punt, since mostly used by readers
        return self.stdin.fileno()

    def isatty(self):
        return self.stdin.isatty() and self.stdout.isatty()

    def errlog(self, text):
        self.stderr.write("%s\n" % (text,))
        self.stderr.flush()

class ConsoleErrorIO(object):
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stderr
        self.stderr = sys.stderr
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        # reading methods
        self.read = self.stdin.read
        self.readline = self.stdin.readline
        self.readlines = self.stdin.readlines
        self.xreadlines = self.stdin.xreadlines
        # writing methods
        self.write = self.stderr.write
        self.flush = self.stderr.flush
        self.writelines = self.stderr.writelines
    
    def raw_input(self, prompt=""):
        return raw_input(prompt)

    def close(self):
        self.stdout = None
        self.stdin = None
        self.closed = 1
        del self.read, self.readlines, self.xreadlines, self.write
        del self.flush, self.writelines

    def fileno(self): # ??? punt, since mostly used by readers
        return self.stdin.fileno()

    def isatty(self):
        return self.stdin.isatty() and self.stdout.isatty()

    def errlog(self, text):
        self.stderr.write("%s\n" % (text,))
        self.stderr.flush()




def _test(argv):
    pass

if __name__ == "__main__":
    _test(sys.argv)
