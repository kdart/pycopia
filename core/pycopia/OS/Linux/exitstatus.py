#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import

import os

class ExitStatus(object):
    """Simplify decoding process exit status for any function that invokes another program.
    Can be avaluated and will appear True only if status indicates a normal process exit.
    """
    EXITED = 1
    STOPPED = 2
    SIGNALED = 3
    def __init__(self, cmdline, sts):
        self.cmdline = cmdline
        if os.WIFEXITED(sts):
            self.state = 1
            self._status = self._es = os.WEXITSTATUS(sts)

        elif os.WIFSTOPPED(sts):
            self.state = 2
            self._status = self.stopsig = os.WSTOPSIG(sts)

        elif os.WIFSIGNALED(sts):
            self.state = 3
            self._status = self.termsig = os.WTERMSIG(sts)

    status = property(lambda self: self._status)

    def exited(self):
        return self.state == 1

    def stopped(self):
        return self.state == 2

    def signalled(self):
        return self.state == 3

    def __int__(self):
        if self.state == 1:
            return self._status
        else:
            name = self.cmdline.split()[0]
            raise ValueError("ExitStatus: %r did not exit normally." % (name,))

    # exit status truth value is true if normal exit, and false otherwise.
    def __nonzero__(self):
        return (self.state == 1) and not self._status

    def __str__(self):
        name = self.cmdline.split()[0]
        if self.state == 1:
            if self._es == 0:
                return "%s: Exited normally." % (name)
            else:
                return "%s: Exited abnormally with status %d." % (name, self._es)
        elif self.state == 2:
            return "%s is stopped." % (name)
        elif self.state == 3:
            return "%s exited by signal %d. " % (name, self.termsig)
        else:
            return "FIXME! unknown state"



