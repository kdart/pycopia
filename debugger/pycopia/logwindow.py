#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
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
Log messages to a separate windows. That window is the urxvt program, which must be installed.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
from datetime import datetime


class DebugLogWindow(object):
    """Open a urxvt terminal window to write debug messages to.
    Call the instance with any number of arguments to write to window.
    """

    def __init__(self):
        self._fo = None

    def __del__(self):
        self.close()

    def close(self):
        if self._fo is not None:
            fo = self._fo
            self._fo = None
            fo.close()

    def __call__(self, *objs):
        if self._fo is None:
            masterfd, slavefd = os.openpty()
            pid = os.fork()
            if pid: # parent
                os.close(masterfd)
                self._fo = os.fdopen(slavefd, "w+", 0)
            else: # child
                os.close(slavefd)
                os.execlp("urxvt", "urxvt", "-pty-fd", str(masterfd))
        print(datetime.now(), ":", ", ".join(map(repr, objs)), file=self._fo)



if __name__=='__main__':
    import signal
    DEBUG = DebugLogWindow()
    DEBUG("test me")
    DEBUG("test me", "again")
    signal.pause()
    DEBUG.close()
    #runcall(help)

