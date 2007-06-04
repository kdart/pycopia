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
I shared memory object for IPC support using coprocesses.

"""

import os, mmap, errno


class SharedBuffer(object):
    def __init__(self, size=8192):
        assert size % os.sysconf("SC_PAGESIZE") == 0, "size must be a multiple of system's page size."
        self.bufsize = size
        self._buf = mmap.mmap(-1, size, flags=mmap.MAP_SHARED|mmap.MAP_ANONYMOUS, 
                    prot=mmap.PROT_READ|mmap.PROT_WRITE )
        self._lock = 0 # simple locking

    def size(self):
        return self.bufsize

    def __del__(self):
        self.close()
    
    def close(self):
        self._buf.close()
        self._buf = None

    def getvalue(self):
        return self._buf[:]

    def write(self, data):
        if self._lock:
            raise OSError, (errno.EAGAIN, "memory busy. try again.")
        self._lock = 1
        self._buf.write(data)
        self._lock = 0
    
    def read(self, amt):
        if self._lock:
            raise OSError, (errno.EAGAIN, "memory busy. try again.")
        self._lock = 1
        d = self._buf.read(amt)
        self._lock = 0
        return d

    
    def unget(self, c):
        self.write(c)
        self.seek(-len(c), 2)

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

