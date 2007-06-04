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
Constants and constructs from rfc2234, Augmented BNF definition.
Refer to ftp://ftp.ietf.org/rfc/rfc2234.txt for more details.

"""
import sre


def crange(start, fin):
    for i in range(start, fin+1):
        yield chr(i)

# a sequential string object containing characters from chr(begin) to chr(end).
class CharRange(str):
    def __new__(cls, begin, end):
        s = str()
        for i in xrange(begin, end+1):
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
    return sre.compile("[%s]+" %(charset,))

LWSP   = sre.compile(r'[%s]+|(%s[%s]+)+' % (WSP, CRLF, WSP))

def normalize(s):
    """Convert all linear white space to a single space."""
    return LWSP.sub(" ", s)

FOLDED   = sre.compile(r'%s([%s]+)' % (CRLF, WSP))
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
    print repr(ts)
    print repr(normalize(ts))

