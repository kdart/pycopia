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
Wrapper for the netcat program. Allows TCP port forwarding to stdio. If your
netcat (nc) is suid to root, you can forward privileged ports, such as SMTP.

"""

import sys
from pycopia import proctools

try:
    NETCAT = proctools.which("nc")
except proctools.NotFoundError:
    NETCAT = proctools.which("netcat")

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

