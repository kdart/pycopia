#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

class Bitfield(object):
    def __init__(self, init_bits=0, numbits=32):
        self.bits = init_bits
        self._mask = self.__bits2mask(numbits)

    def getbit(self, bit):
        return self.bits & (1 << bit)

    def setbit(self, bit):
        self.bits = self.bits | (1 << bit)

    def __call__(self):
        return self.bits & self.mask

    def __bits2mask(self, bits):
        if bits <= 32 and bits >= 0:
            return ~(0xffffffff << bits)
        else:
            raise ValueError

