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
Implements a netstring object, as described in:

http://cr.yp.to/proto/netstrings.txt

"""

def encode(s):
    return "%d:%s," % (len(s), s)

def decode(s):
    c = s.find(":")
    l = int(s[:c])
    ns = s[c+1:c+l+1]
    if len(ns) != l:
        raise ValueError, "invalid netstring, bad length"
    if s[c+l+1] != ",":
        raise ValueError, "invalid encoding, bad terminator"
    return ns


if __name__ == "__main__":
    s = "hello, this is a test!\nagain!"
    es = encode(s)
    print es
    ds = decode(es)
    print ds
    if ds == s:
        print "passed"
    else:
        print "failed"

