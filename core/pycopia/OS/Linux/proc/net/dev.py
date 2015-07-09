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

