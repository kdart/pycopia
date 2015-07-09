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
Wrapper for the 'rsync' program. See the rsync manpage for more details.

"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia import proctools

RSYNC = proctools.which("rsync")

TESTED_VERSIONS = ["rsync  version 2.5.5  protocol version 26"]

def rsync(src, dst, password=None, extraopts=None, logfile=None):
    """rsync(src, dst, [password, [extraopts, [logfile]]])

Usage: rsync [OPTION]... SRC [SRC]... [USER@]HOST:DEST
  or   rsync [OPTION]... [USER@]HOST:SRC DEST
  or   rsync [OPTION]... SRC [SRC]... DEST
  or   rsync [OPTION]... [USER@]HOST::SRC [DEST]
  or   rsync [OPTION]... SRC [SRC]... [USER@]HOST::DEST
  or   rsync [OPTION]... rsync://[USER@]HOST[:PORT]/SRC [DEST]

You might want to set the RSYNC_RSH environment variable first.
    """
    opts = "-q"
    if extraopts:
        opts += extraopts
    CMD = "%s %s %s %s" % (RSYNC, opts, src, dst)
    rsync = proctools.spawnpty(CMD, logfile=logfile)
    # assume a password will be requested if one is supplied here
    if password is not None:
        from pycopia import expect
        ersync = expect.Expect(rsync)
        ersync.expect("password:", timeout=2.0)
        ersync.writeln(password)
        del ersync
    rsync.wait()
    return rsync.exitstatus # user can check exit status for success

def rsync_version():
    """rsync_version() Return the version string for the rsync command on this
system."""
    rsync = proctools.spawnpipe("rsync --version")
    ver = rsync.readline() # version on first line of output
    rsync.read() # discard rest
    rsync.close()
    return ver

def check_version():
    """Checks that the installed rsync program is the same one that this module was
    tested with (and written for)."""
    ver = rsync_version()[15:20]
    for vs in TESTED_VERSIONS:
        if ver == vs[15:20]:
            return 1
    return 0


if __name__ == "__main__":
    if check_version():
        print ("your rsync version is good!")
    else:
        print ("your rsync version is an untested one, beware of errors!")

