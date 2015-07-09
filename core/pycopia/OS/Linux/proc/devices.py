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

