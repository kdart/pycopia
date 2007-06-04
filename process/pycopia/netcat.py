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
Wrapper for the netcat program. Allows TCP port forwarding to stdio. If your
netcat (nc) is suid to root, you can forward privileged ports, such as SMTP.

"""

import sys
from pycopia import proctools

NETCAT = proctools.which("nc")

TESTED_VERSIONS = ["[v1.10]"]


def get_netcat(host, port, callback=None, logfile=None, extraoptions=""):
    """get_netcat(host, port, [prompt], [callback], [logfile], [extraoptions])
Returns a Netcat object (an Expect subclass) attached to a netcat client.

The logfile parameter should be a file-like object (has a 'write' method).
"""
    cmd = "%s %s %s %s" %(NETCAT, extraoptions, host, port)
    pm = proctools.get_procmanager()
    proc = pm.spawnpipe(cmd, callback=callback, logfile=logfile, merge=0)
    return proc

def netcat_server(port, callback=None, logfile=None, extraoptions=""):
    extraoptions += " -l -p %d" % (port)
    cmd = "%s %s" %(NETCAT, extraoptions)
    pm = proctools.get_procmanager()
    proc = pm.spawnpipe(cmd, callback=callback, logfile=logfile, merge=0)
    return proc

netcat_listener = netcat_server # alias

def killall():
    pm = proctools.get_procmanager()
    for proc in pm.getbyname(NETCAT):
        proc.kill()


def netcat_version():
    """netcat_version() Return the version string for the netcat command on this system."""
    nc = proctools.spawnpipe("%s -h" % (NETCAT))
    ver = nc.readline()
    nc.read() # discard rest
    nc.wait()
    return ver.strip()

def check_version():
    """Checks that the installed netcat program is the same as this module was
    tested with (and written for)."""
    ver = netcat_version()
    for vs in TESTED_VERSIONS:
        if ver == vs:
            return 1
    return 0

