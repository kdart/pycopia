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
Access the FreeBSD device database.

"""

import os, bsddb, struct

# file types
from stat import S_IFDIR, S_IFCHR, S_IFBLK, S_IFREG, S_IFIFO, S_IFLNK, S_IFSOCK


DEVFILE = "/var/run/dev.db"

class DevDB(object):
    def __init__(self):
        self.db = bsddb.hashopen(DEVFILE)

    def get(self, ftype, rdev):
        key = struct.pack("ii", ftype, rdev)
        return self.db[key][:-1] # remove trailing null

    def _rdev(ielf, maj, minor):
        return (maj << 8) | (minor & 0xff)

    def get_char(self, major, minor):
        return self.get(S_IFCHR, self._rdev(major, minor))

    def get_block(self, major, minor):
        return self.get(S_IFBLK, self._rdev(major, minor))

    def get_dir(self, major, minor):
        return self.get(S_IFDIR, self._rdev(major, minor))

    def get_fifo(self, major, minor):
        return self.get(S_IFFIFO, self._rdev(major, minor))

    def get_link(self, major, minor):
        return self.get(S_IFLNK, self._rdev(major, minor))

    def get_sock(self, major, minor):
        return self.get(S_IFSOCK, self._rdev(major, minor))

    def keys(self):
        return self.db.keys()

    def close(self):
        self.db.close()
        self.db = None

    def __del__(self):
        if self.db is not None:
            self.db.close()


def open():
    return DevDB()


if __name__ == "__main__":
    db = open()
    print db.get_char(12,0)
    db.close()

