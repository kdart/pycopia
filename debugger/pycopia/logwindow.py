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
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
from datetime import datetime

from pycopia import methods

class DebugLogWindow(object):
    """Open a urxvt terminal window to write debug messages to.
    Call the instance with any number of arguments to write to window.
    """

    def __init__(self, do_stderr=False):
        self._do_stderr = do_stderr
        self._fo = None

    def __del__(self):
        self.close()

    def fileno(self):
        if self._fo is not None:
            return self._fo.fileno()
        else:
            return -1

    def close(self):
        if self._fo is not None:
            fo = self._fo
            self._fo = None
            fo.close()
            if self._do_stderr:
                os.close(2)
                os.dup2(1, 2)

    def __call__(self, *objs):
        if self._fo is None:
            masterfd, slavefd = os.openpty()
            pid = os.fork()
            if pid: # parent
                os.close(masterfd)
                self._fo = os.fdopen(slavefd, "w+b", 0)
                if self._do_stderr:
                    os.close(2)
                    os.dup2(slavefd, 2)
            else: # child
                os.close(slavefd)
                os.execlp("urxvt", "urxvt", "-pty-fd", str(masterfd))
        fo = self._fo
        fo.write("{}: ".format(datetime.now()).encode("utf-8"))
        lo = len(objs) - 1
        for i, o in enumerate(objs):
            fo.write(repr(o).encode("utf-8"))
            if i < lo:
                fo.write(b", ")
        fo.write(b"\n")


# automatic, lazy construction of DEBUG object
def _debug_builder(*args):
    global DEBUG
    if DEBUG is _debug_builder:
        DEBUG = DebugLogWindow()
    DEBUG(*args)

DEBUG = _debug_builder

# decorator to report on function calls
def logcall(f):
    def _debug(*args, **kwargs):
        ms = methods.MethodSignature(f)
        argdict = ms.get_keyword_arguments(args, kwargs)
        DEBUG(str(methods.MethodSignature(f)),
                ", ".join("{!s}={!r}".format(t[0], t[1]) for t in argdict.items() if t[0] != "self"))
        return f(*args, **kwargs)
    _debug.__doc__ = f.__doc__
    return _debug


if __name__=='__main__':
    import signal
    DEBUG(b"test me")
    DEBUG(b"test me", b"again")
    signal.pause()
    DEBUG.close()

