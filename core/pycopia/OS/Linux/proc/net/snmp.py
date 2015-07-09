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
The basic SNMP scalars from /proc/net/snmp.

"""

FILE = "/proc/net/snmp"

class _Row(dict):
    def __init__(self, namestr, valstr):
        for name, val in zip(namestr.split(), valstr.split()):
            try:
                self[name] = long(val)
            except ValueError: # catches heading
                self._name = name

    def __str__(self):
        s = [self._name]
        for name, val in self.items():
            s.append("  %20s: %ld" % (name, val))
        return "\n".join(s)

    def __getattr__(self, name):
        return dict.__getitem__(self, name)


class SNMP(object):
    def __init__(self):
        self.update()

    def update(self):
        lines = open(FILE).readlines()
        self.Ip = _Row(lines[0], lines[1])
        self.Icmp = _Row(lines[2], lines[3])
        self.Tcp = _Row(lines[4], lines[5])
        self.Udp = _Row(lines[6], lines[7])

    def __str__(self):
        return "\n".join(map(str, [self.Ip, self.Icmp, self.Tcp, self.Udp]))


def get_snmp():
    s = SNMP()
    return s

def _test(argv):
    snmp = get_snmp()
    print snmp
    return snmp

if __name__ == "__main__":
    import sys, time
    snmp = _test(sys.argv)
    while 1:
        print snmp.Ip
        snmp.update()
        time.sleep(1)


