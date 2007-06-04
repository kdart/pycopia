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
Interface to the /proc/interrupts file.

"""

FILE="/proc/interrupts"

class _CPU(object):
    def __init__(self, cpu, count=0L):
        self.cpu = int(cpu)
        self.count = long(count)
    def __str__(self):
        return "CPU%d: IRQ count = %u" % (self.cpu, self.count)


class _InterruptLine(object):
    def __init__(self):
        self.name = None
        self.handlername = None
        self.actions = None
        self._cpus = []
    
    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        #  5:       3306          XT-PIC  Ensoniq AudioPCI
        cs = "".join(map(lambda c: "%10u " % (c.count,), self._cpus))
        return "%-3s: %s %14s  %s" % (self.name, cs, self.handlername, self.actions)
    
#  15:    1539950          XT-PIC  aic7xxx, usb-uhci
    def update(self, line, cpus):
        self._cpus = []
        name, line = line.split(":", 1)
        try:
            self.name = int(name)
        except ValueError:
            self.name = name

        for cpu in cpus:
            newcpu = _CPU(cpu.cpu)
            try:
                cs, line = line.split(None, 1)
            except ValueError:
                newcpu.count = long(line)
                line = None
            else:
                newcpu.count = long(cs)
            self._cpus.append(newcpu)
        if line:
            self.handlername, line = line.split(None, 1)
            self.actions = line.strip()

    def __getitem__(self, idx):
        return self._cpus[idx]


class Interrupts(object):
    def __init__(self):
        self._cpus = []
        self._err = 0L # IRQ Error count
        self._mis = 0L # APIC mismatch count

    def update(self):
        self._cpus = []
        self._irqs = {}
        lines = open(FILE).readlines()
        for rcpu in lines[0].split():
            idx = int(rcpu[3:])
            self._cpus.append(_CPU(idx))
        
        for line in lines[1:]:
            if line.startswith("ERR"):
                self._err = long(line.split(":")[1])
            elif line.startswith("MIS"):
                self._mis = long(line.split(":")[1])
            else:
                irq = _InterruptLine()
                irq.update(line, self._cpus)
                self._irqs[irq.name] = irq

    def __str__(self):
        # CPU header line
        h = ["           "]
        h.extend(map(lambda c: "CPU%d       " % (c.cpu,), self._cpus))
        s = ["".join(h)]

        s.extend(map(str, self._irqs.values()))

        s.append("ERR: %10u" % (self._err,))
        s.append("MIS: %10u" % (self._mis,))
        return "\n".join(s)
    
    def __getitem__(self, idx):
        return self._irqs[idx]


def get_interrupts():
    ir = Interrupts()
    ir.update()
    return ir

def _test(argv):
    ir = get_interrupts()
    print ir
    print ir[5][0] # index by IRQ, CPU

if __name__ == "__main__":
    import sys
    _test(sys.argv)

