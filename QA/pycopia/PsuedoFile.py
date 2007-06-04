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
Defines the PsuedoFile class. This class emulates a file object in memory.

"""


class PsuedoFile(object):
    """
Objects of this class behave as file objects, but no actual file exists.
It is used to generate arbitrary data for transmission tests where a file
object is required by the API. 

You instantiate this object with an integer that represents the size of
the file in bytes. An optional "file" name may be given.

Example:

fp = PsuedoFile(1000000)

will create a file-like object with a "size" of 1000000 bytes. 

    """
    def __init__(self, size=0, name=''):
        self.size = size
        self.name = name
        self.pos = 0
        self.softspace = 0
        self.closed = 0
        self.randomblock = '\t\t"\xce\x8d\xab3\x92\x83\xc1\xdf\xaa\xc7+\'e[d\xc1f\xdbS4\xa6{\x9a4v\x9d\xdd\xe0\xfd\x8bb\xe1"'
        self.stringblock = "%6d: abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
        self.randomblocklen = len(self.randomblock)
    def __repr__(self):
        return "%s(%d, %s)" % ( self.__class__.__name__, self.size, self.name)
    def __str__(self):
        return "%8d %s" % (self.size, self.name)
    def set_size(self, sz):
        self.size = int(sz)
    def open(self, mode="r"):
        self.closed = 0
        if mode[0] == "a":
            self.pos = self.size
        elif mode[0] == "w":
            self.pos = 0
            self.size = 0
        else:
            self.pos = 0
    def close(self):
        if not self.closed:
            self.closed = 1
            self.pos = 0
    def read(self, bs=8192):
        if self.closed:
            raise ValueError, "file is closed"
        if self.pos == self.size:
            return ""
        if (self.pos + bs) > self.size:
            bs = self.size - self.pos
            self.pos = self.size
        else:
            self.pos = self.pos + bs
        buf = self.randomblock * int(bs/self.randomblocklen)
        buf = buf + self.randomblock[0:bs % self.randomblocklen]
        return buf
    def readline(self):
        if self.closed:
            raise ValueError, "file is closed"
        if self.pos == self.size:
            return ""
        s = self.stringblock % self.pos
        len_s = len(s)
        if (self.pos + len_s) > self.size:
            s = s[0:len_s - (self.size - self.pos)]
            self.pos = self.size
        else:
            self.pos = self.pos + len_s
        return s
    def readlines(self):
        lines = []
        while self.pos < self.size:
            lines.append(self.readline())
        return lines
    def seek(self, pos, mode=0):
        if self.closed:
            raise ValueError, "file is closed"
        if mode == 0:
            if pos < self.size:
                self.pos = pos
            else:
                self.pos = self.size
        elif mode == 1:
            if self.pos + pos < self.size:
                self.pos = self.pos + pos
            else:
                self.pos = self.size
        elif mode == 2:
            if pos > self.size:
                self.pos = 0
            else:
                self.pos = self.size - pos
        elif mode == -1: # special mode setting the size
            self.size = pos

    def tell(self):
        if self.closed:
            raise ValueError, "file is closed"
        return self.pos
    def isatty(self):
        return 0
    def write(self, buf):
        self.size += len(buf)
        return 0
    def writelines(self, lines):
        for line in lines:
            self.write(line)
        return 0


