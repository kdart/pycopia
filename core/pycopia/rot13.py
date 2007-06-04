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
Provides rot13 function that performs a ROT13 transormation of a given string.

"""

_rot13_map = None # will be replaced by the _init function below.

def _init():
    global _rot13_map
    L = range(256)
    for cbase in (65, 97):
        for i in range(26):
            L[i+cbase] = (i+13) % 26 + cbase
    _rot13_map = "".join(map(chr, L))

_init()

def rot13(text):
    global _rot13_map
    return text.translate(_rot13_map)


def _test(argv):
    s="The quick brown fox jumped over the lazy dog."
    print s
    tr = rot13(s)
    print tr
    assert tr != s
    back = rot13(tr)
    assert back == s
    print back


if __name__ == "__main__":
    import sys
    _test(sys.argv)

