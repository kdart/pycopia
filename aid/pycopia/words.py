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
fetch words from the system word list, using regular expressions.

"""

import re

from pycopia import UserFile

WORDFILES = ["/usr/share/dict/words", "/usr/dict/words"]


def get_wordfile():
    for fn in WORDFILES:
        try:
            wordfile = UserFile.open(fn, "r")
        except IOError:
            pass
        else:
            return wordfile
    raise ValueError, "cannot find file of words."


def get_random_word():
    """Return a randomly selected word from dict file."""
    from pycopia import sysrandom
    fo = get_wordfile()
    try:
        point = sysrandom.randrange(fo.size)
        fo.seek(point)
        c = fo.read(1)
        while c != '\n' and fo.tell() > 0:
            fo.seek(-2, 1)
            c = fo.read(1)
        word = fo.readline().strip()
    finally:
        fo.close()
    return word


def get_word_list(patt, wordfile=None):
    """Yield words matching pattern (like grep)."""
    if not wordfile:
        wordfile = get_wordfile()
    wre = re.compile(patt)
    for line in wordfile:
        test = line.strip()
        if wre.match(test):
            yield test

