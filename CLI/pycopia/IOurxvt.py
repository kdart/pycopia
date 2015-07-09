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
IO module that uses a separate unicode-rxvt instance for IO.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os


class UrxvtIO(object):
    def __init__(self):
        masterfd, slavefd = os.openpty()
        pid = os.fork()
        if pid: # parent
            os.close(masterfd)
            self._fo = os.fdopen(slavefd, "w+", 0)
        else: # child
            os.close(slavefd)
            os.execlp("urxvt", "urxvt", "-pty-fd", str(masterfd))
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        # reading methods
        self.read = self._fo.read
        self.readline = self._fo.readline
        self.readlines = self._fo.readlines
        # writing methods
        self.write = self._fo.write
        self.flush = self._fo.flush
        self.writelines = self._fo.writelines

    def raw_input(self, prompt=""):
        self._fo.write(prompt)
        return self._fo.readline()[:-1]

    def close(self):
        if self._fo is not None:
            self.closed = 1
            self._fo.close()
            self._fo = None
            self.read = None
            self.readline = None
            self.readlines = None
            # writing methods
            self.write = None
            self.flush = None
            self.writelines = None

    def fileno(self):
        return self._fo.fileno()

    def isatty(self):
        return self._fo.isatty()

    def errlog(self, text):
        self._fo.write("%s\n" % (text,))
        self._fo.flush()



def _test(argv):
    import time
    io = UrxvtIO()
    inp = io.raw_input("type something> ")
    io.write(inp + "\n")
    io.write("closing in 5 seconds\n")
    time.sleep(5)
    io.close()

if __name__ == "__main__":
    import sys
    _test(sys.argv)

