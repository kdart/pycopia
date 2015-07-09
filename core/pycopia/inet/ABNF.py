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
Constants and constructs from rfc2234, Augmented BNF definition.
Refer to ftp://ftp.ietf.org/rfc/rfc2234.txt for more details.

"""
from __future__ import print_function

import re


def crange(start, fin):
    for i in range(start, fin+1):
        yield chr(i)

# a sequential string object containing characters from chr(begin) to chr(end).
class CharRange(str):
    def __new__(cls, begin, end):
        s = str()
        for i in range(begin, end+1):
            s += chr(i)
        return str.__new__(cls, s)

    def __init__(self, begin, end):
        self.begin = begin
        self.end = end


# a set of characters
class CharSet(str):
    def __new__(cls, *ranges):
        s = reduce(str.__add__, ranges, "")
        return str.__new__(cls, s)


# ABNF literals are case-INsensitive
# Keep the value in uppercase to speed up comparisons.
class Literal(str):
    def __new__(cls, s=""):
        s = str(s).upper()
        return str.__new__(cls, s)
    def __eq__(self, other):
        return str.__eq__(self, other.upper())
    def __lt__(self, other):
        return str.__lt__(self, other.upper())
    def __gt__(self, other):
        return str.__gt__(self, other.upper())
    def __le__(self, other):
        return str.__le__(self, other.upper())
    def __ge__(self, other):
        return str.__ge__(self, other.upper())
    def __add__(self, other):
        s = str(self)+str(other)
        return Literal(s)
    def upper(self):
        return Literal(self)
    def lower(self): # effectively nothing
        return Literal(self)



# CORE atoms
ALPHA  = CharRange(0x41, 0x5a)+CharRange(0x61, 0x7a)
BIT    = "01"
CHAR   = CharRange(1, 0x7f)
CR     = "\r"
CRLF   = "\r\n"
CTL    = CharRange(0, 0x1f)+"\x7f"
DIGIT  = CharRange(0x30, 0x39)
DQUOTE = '\x22'
HEXDIG = DIGIT+"ABCDEF"
HTAB   = "\t"
LF     = "\n"
OCTET  = CharRange(0, 0xff)
SP     = "\x20"
VCHAR  = CharRange(0x21, 0x7E)
WSP    = SP+HTAB

def _re_factory(charset):
    return re.compile("[%s]+" %(charset,))

LWSP   = re.compile(r'[%s]+|(%s[%s]+)+' % (WSP, CRLF, WSP))

def normalize(s):
    """Convert all linear white space to a single space."""
    return LWSP.sub(" ", s)

FOLDED   = re.compile(r'%s([%s]+)' % (CRLF, WSP))
def unfold(s):
    """Unfold a folded string, keeping line breaks and other white space."""
    return FOLDED.sub(r"\1", s)

def headerlines(bigstring):
    """Yield unfolded lines from a chunk of text."""
    bigstring = unfold(bigstring)
    for line in bigstring.split(CRLF):
        yield line



if __name__ == "__main__":
    ts = """line one: w1 w2    w3\tw4\r\n\t   \tw5\t\t\tw6\r\nline two: \r\nline three:\r\n\r\nBody."""
    print (repr(ts))
    print (repr(normalize(ts)))

