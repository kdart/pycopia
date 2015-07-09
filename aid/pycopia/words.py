#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    raise ValueError("cannot find file of words.")


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

