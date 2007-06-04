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
Interface to the /proc/mounts file.

"""

import sys

FILE="/proc/mounts"


class Mount(object):
    def __init__(self):
        self.device = None
        self.mountpoint = None
        self.fstype = None
        self.options = None
        self.freq = 0
        self.passno = 0
    def parse(self, line):
        [self.device, self.mountpoint, self.fstype, self.options, self.freq, self.passno]  = line.split()
    def __str__(self):
        return "%s %s %s %s %s %s" % (self.device, self.mountpoint, self.fstype, self.options, self.freq, self.passno)


class Mounts(dict):
    def update(self):
        self.clear()
        fo = open(FILE)
        for line in fo:
            mo = Mount()
            mo.parse(line)
            self[mo.mountpoint] = mo
        fo.close()

    def __str__(self):
        return "\n".join(map(str, self.values()))

def get_mounts():
    mounts = Mounts()
    mounts.update()
    return mounts


if __debug__:
    def _test(argv):
        mnts = get_mounts()
        print mnts
        print 
        print mnts["/"].fstype
        

    if __name__ == "__main__":
        _test(sys.argv)

