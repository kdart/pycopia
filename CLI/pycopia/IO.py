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
        del self.read, self.readlines, self.write
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
        del self.read, self.readlines, self.write
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
