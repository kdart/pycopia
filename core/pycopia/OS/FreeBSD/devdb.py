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

