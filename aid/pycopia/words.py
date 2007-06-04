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


WORDFILES = ["/usr/share/dict/words", "/usr/dict/words"]


def get_wordfile():
    for fn in WORDFILES:
        try:
            wordfile = open(fn, "r")
        except IOError:
            pass
        else:
            return wordfile
    raise ValueError, "cannot find file of words."


def get_word_list(patt, wordfile=None):
    wl = []
    if not wordfile:
        wordfile = get_wordfile()
    wre = re.compile(patt)
    for line in wordfile:
        test = line.strip()
        if wre.search(test):
            wl.append(test)
    return wl

