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

