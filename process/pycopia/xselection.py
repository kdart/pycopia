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
Use wxcut and wxpaste to get and set the X selection.

"""

from pycopia import proctools

try:
    WXCOPY = proctools.which("wxcopy")
    WXPASTE = proctools.which("wxpaste")
except ValueError:
    raise ImportError, "wxcopy or wxpaste program not found! Install WindowMaker for these."

WXCOPY_OPTIONS = '-clearselection'
WXPASTE_OPTIONS = ''


def wxcopy(text, callback=None, logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s" % (WXCOPY, WXCOPY_OPTIONS, extraoptions)
    copy = pm.spawnpipe(command, logfile=logfile, async=async)
    copy.write(text)
    copy.close()
    return copy.wait()

def wxpaste(callback=None, logfile=None, extraoptions="", async=False):
    """wxpaste - output a cutbuffer to stdout, returned as a string."""
    pm = proctools.get_procmanager()
    command = "%s %s %s" % (WXPASTE, WXPASTE_OPTIONS, extraoptions)
    paste = pm.spawnpipe(command, logfile=logfile, async=async)
    rv = paste.read()
    paste.close()
    es = paste.wait()
    if es:
        return rv
    else:
        raise RuntimeError, str(es)

