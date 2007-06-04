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
A Python implementation of Knuth's MIX machine.

"""

#from array import array
#from struct import pack, unpack

# the sign enumerations
PLUS = Enum(1, "+")
MINUS = Enum(-1, "-")

def sign(i):
    if i >= 0:
        return PLUS
    else:
        return MINUS

class Register(object):
    def __init__(self, value=0):
        self.value = _pack(value)

class IndexRegister(Register):
    pass

class MemoryCell(Register):
    pass

def _pack(i):
    value = [sign(i), 0,0,0,0,0] # 5 "bytes" and a sign
    for idx in range(5):
        value[5-idx] = (i >> (idx*6)) & 0x3f
    return value

class Memory(object):
    def __init__(self, size):
        self._mem = m = []
        for i in xrange(size):
            m.append(MemoryCell(i))
    def __getitem__(self, idx):
        return self._mem[idx]
    def __setitem__(self, idx, val):
        self._mem[int(idx)] = MemoryCell(int(val))


class MIX1009(object):
    def __init__(self):
        self.A = Register()
        self.X = Register() # extend right-side of A
        self.I1 = IndexRegister()
        self.I2 = IndexRegister()
        self.I3 = IndexRegister()
        self.I4 = IndexRegister()
        self.I5 = IndexRegister()
        self.I6 = IndexRegister()
        self.J  = IndexRegister() # always signed PLUS
        self.memory = Memory(4000)




def _test(argv):
    pass

if __name__ == "__main__":
    import sys
    #_test(sys.argv)
    mix = MIX1009()
    print mix

