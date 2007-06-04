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


