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
Run things as root (or another user) via sudo.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia import proctools
from pycopia.aid import IF

SUDO = proctools.which("sudo")

def sudo(command, user=None, password=None, extraopts=None, logfile=None):
    opts = "-S %s" % ("-u %s" % user if user else "")
    cmd = "%s %s %s %s" % (SUDO, opts, extraopts or "", command)
    proc = proctools.spawnpipe(cmd, logfile=logfile, merge=0)
    if password:
        proc.readerr(9) # discard password prompt
        proc.write("%s\r" % (password,))
        proc.readerr(1) # discard newline
    return proc

def sudo_reset():
    proc = proctools.spawnpipe("%s -k" % (SUDO,), merge=0)
    proc.read()
    proc.wait()

def sudo_command(cmd, password=None, logfile=None):
    """Run a command with sudo and return the output."""
    proc = sudo(cmd, password, logfile=logfile)
    rv = proc.read()
    errs = proc.readerr()
    es = proc.wait()
    if errs or not es:
        raise RuntimeError((es, errs))
    return rv

def getpw():
    import getpass
    pw = getpass.getpass("sudo password: ")
    if not pw:
        return None
    return pw

