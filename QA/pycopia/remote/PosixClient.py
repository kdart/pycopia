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


