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
The devices file.

"""

class Devices:
    def __init__(self):
        fo = open("/proc/devices")
        self._charmap = {}
        self._blockmap = {}
        for line in fo.readlines():
            if line.startswith("Character"):
                curmap = self._charmap
                continue
            elif line.startswith("Block"):
                curmap = self._blockmap
                continue
            elif len(line) > 4:
                [num, fmt] = line.split()
                num = int(num)
                curmap[num] = fmt

    def __str__(self):
        s = ["Character devices:"]
        for num, fmt in self._charmap.items():
            s.append("%3d %s" % (num, fmt))
        s.append("\nBlock devices:")
        for num, fmt in self._blockmap.items():
            s.append("%3d %s" % (num, fmt))
        return "\n".join(s)


    def get_device(self, dtype, major, minor):
        pass


def _test(argv):
    d = Devices()
    print d

if __name__ == "__main__":
    import sys
    _test(sys.argv)

