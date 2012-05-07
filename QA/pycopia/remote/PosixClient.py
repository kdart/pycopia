#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012  Keith Dart <keith@dartworks.biz>
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
Client addidtions to transparently connect from a Posix remote agent
client to a server running on MS Windows.

A WindowsServer can raise WindowsError exception, but Pyro can't map that
to a Python exception running under Posix. So, define that here to fake
it.
"""

import sys, new

class WindowsError(OSError):
    pass

class error(Exception):
    pass

# build a fake pywintypes module that the WindowsServer may return an object from.
pywintypes = new.module("pywintypes")
setattr(pywintypes, "WindowsError", WindowsError)
setattr(pywintypes, "error", error)
sys.modules["pywintypes"] = pywintypes
del sys, new

# also stuff the exception in the exceptions module
import exceptions
exceptions.WindowsError = WindowsError


