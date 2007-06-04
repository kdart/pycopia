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

