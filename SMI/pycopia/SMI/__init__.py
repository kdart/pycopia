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
An SMI parser and collection of tools. This package wraps the SWIG generated
code that in turn wraps the libsmi library. The libsmi library is a C library
that parses SMI files.

libsmi home page:

http://www.ibr.cs.tu-bs.de/projects/libsmi/

"""

import sys

from pycopia.aid import Import

# "global" OIDMAP contains reverse OID for all imported MIBS.
OIDMAP = {}

def update_oidmap(basemodname):
    global OIDMAP
    modname = "%s_OID" % basemodname
    oidmod = Import(modname)
    OIDMAP.update(oidmod.OIDMAP)
    # clean up extra references
    delattr(oidmod, "OIDMAP")
    del sys.modules[modname]

