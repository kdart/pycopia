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
Read /proc/net/dev data.

"""

FILE = "/proc/net/dev"

class ReceiveData(object):
    def __init__(self, bytes, packets, errs, drop, fifo, frame, compressed, multicast):
        self.bytes = bytes
        self.packets = packets
        self.errs = errs
        self.drop = drop
        self.fifo = fifo
        self.frame = frame
        self.compressed = compressed
        self.multicast = multicast
    
    def __str__(self):
        return "%10d %10d %6d %6d %6d %6d %10d %10d" % (self.bytes, self.packets, 
            self.errs, self.drop, self.fifo, self.frame, self.compressed, self.multicast)

class TransmitData(object):
    def __init__(self, bytes, packets, errs, drop, fifo, colls, carrier, compressed):
        self.bytes = bytes
        self.packets = packets
        self.errs = errs
        self.drop = drop
        self.fifo = fifo
        self.colls = colls
        self.carrier = carrier
        self.compressed = compressed

    def __str__(self):
        return "%10d %10d %6d %6d %6d %6d %8d %10d" % (self.bytes, self.packets, 
            self.errs, self.drop, self.fifo, self.colls, self.carrier, self.compressed)

class Interface(object):
    def __init__(self, name):
        self.name = name
        self.rx = None
        self.tx = None
    
    def __str__(self):
        return "%5s: %s %s" % (self.name, self.rx, self.tx)


class DevTable(object):
    def __init__(self):
        self._devs = {}

    def __str__(self):
        s = ["""
Inter-|   Receive                                                             |  Transmit
 face |bytes         packets   errs   drop   fifo  frame compressed  multicast|bytes         packets   errs   drop   fifo  colls  carrier compressed
"""]
        for dev in self._devs.values():
            s.append(str(dev))
        return "\n".join(s)
    
    def _get_names(self):
        names = self._devs.keys()
        names.sort()
        return names
    names = property(_get_names)

    def __getitem__(self, name):
        return self._devs[name]

    def update(self):
        lineno = 0
        raw = open(FILE).read()
        for line in raw.splitlines():
            if lineno > 1:
                colon = line.find(":")
                name = line[:colon].strip()
                parts = map(long, line[colon+1:].split())
                iface = Interface(name)
                iface.rx = ReceiveData(*tuple(parts[0:8]))
                iface.tx = TransmitData(*tuple(parts[8:16]))
                self._devs[name] = iface
            lineno += 1



if __name__ == "__main__":
    dt = DevTable()
    dt.update()
    print dt
    print dt["eth0"].rx.bytes
    print dt["eth0"].tx.bytes

