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
Wrapper for the 'rsync' program. See the rsync manpage for more details.

"""


from pycopia import proctools

try:
    RSYNC = proctools.which("rsync")
except ValueError:
    raise ImportError, "rsync program not found!"

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
        print "your rsync version is good!"
    else:
        print "your rsync version is an untested one, beware of errors!"
