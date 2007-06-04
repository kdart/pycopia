#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
# $Id$
#
#    Copyright (C) 1999-2004  Keith Dart <keith@kdart.com>
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
Platform dependent modules, and modules using "duck-typing" to hide
platform details.

"""

import sys
import os

# Patch os module with extra constants.
os.ACCMODE = 03

# Additional module path for polymorphic platform modules.
platdir = {
    "linux1":"Linux", 
    "linux2":"Linux", 
    "cygwin":"CYGWIN_NT", 
    "sunos5":"SunOS",
    "freebsd4":"FreeBSD", 
    "freebsd5":"FreeBSD", 
    "darwin":"Darwin", 
    "win32":"Win32"}[sys.platform]

__path__.append(os.path.join(__path__[0], platdir))


