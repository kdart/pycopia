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
Start and control an alsaplayer deamon instance.
"""

from pycopia import proctools
import os

try:
    PLAYER = proctools.which("alsaplayer")
except ValueError:
    raise ImportError, "alsaplayer program not found!"

DEVICE = os.environ.get("ALSAPLAYERDEVICE", "default")

def get_alsaplayer(session=0, name="alsaplayer", device=DEVICE, extraopts="", logfile=None):
    """Return a process object for the alsaplayer."""
    opts = "-i daemon -q -n %s -s '%s' -d %s --nosave" % (session, name, device)
    CMD = "%s %s %s" % (PLAYER, opts, extraopts)
    aplayer = proctools.spawnpipe(CMD, logfile=logfile)
    return aplayer


