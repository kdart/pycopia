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
The WindowsServer cannot return objects contained in the WindowsServer module
to Posix clients, because that module cannot be imported on Posix clients.
Objects here mirror the objects from the WindowsServer that the WindowsServer
may return to a PosixClient.

"""

import os

class ExitStatus(object):
    def __init__(self, cmdline, sts):
        self.cmdline = cmdline
        self._status = int(sts)

    def status(self):
        self._status

    def exited(self):
        return NotImplemented

    def stopped(self):
        return NotImplemented

    def signalled(self):
        return NotImplemented

    def __int__(self):
        return self._status

    # exit status truth value is true if normal exit, and false otherwise.
    # Shell semantics are that zero is true
    def __nonzero__(self):
        return self._status == 0

    def __str__(self):
        name = self.cmdline.split()[0]
        if self._status == 0:
            return "%s: Exited normally." % (name)
        elif self._status > 0:
            return "%s: Exited abnormally with status %d." % (name, self._status)
        else:
            return "%s exited by signal %d. " % (name, -self._status)

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r)" % (cl.__module__, cl.__name__, self.cmdline, self._status)

