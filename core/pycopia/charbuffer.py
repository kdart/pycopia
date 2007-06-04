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
Defines a Buffer object that uses an anonymous mmap. The object looks like a
StringIO object as well as supporting string operators.

"""

import mmap

# get an anonymous mmap range. Only works on Linux (possibly other Unix)
def get_buffer(size):
    return mmap.mmap(-1, size, flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS, 
                    prot=mmap.PROT_READ|mmap.PROT_WRITE )

# Also emulate a StringIO object.
class Buffer(object):
    def __init__(self, size=4096):
        self._bufsize = size
        self._buf = get_buffer(size)

    size = property(lambda s: s._bufsize)

    def close(self):
        if self._buf is not None:
            self._buf.close()
            self._buf = None

    def getvalue(self):
        return self._buf[:]

    # auto-delegate most attributes
    def __getattr__(self, name):
        return getattr(self._buf, name)
    
    def __getitem__(self, i):
        return self._buf[i]

    def __setitem__(self, i, v):
        self._buf[i] = v

    def __getslice__(self, i, j):
        return self._buf[i:j]

    def __setslice__(self, i, j, seq):
        self._buf[i:j] = seq

    def __iadd__(self, seq):
        self._buf.write(seq)
        return self

    def __len__(self):
        return self._buf.tell()

    def __str__(self):
        return self._buf[0:self._buf.tell()]


