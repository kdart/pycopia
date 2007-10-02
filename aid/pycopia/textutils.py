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
General text functions. You may import this instead of the stock
"string" module in most cases.

"""

import sys
import re
import binascii

from pycopia.aid import removedups

lowercase = 'abcdefghijklmnopqrstuvwxyz'
uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
letters = lowercase + uppercase
alphanumeric = lowercase + uppercase + digits
whitespace = ' \t\n\r\v\f'
CRLF   = "\r\n"
punctuation = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
printable = digits + letters + punctuation + whitespace


def cut_string(s, maxlen=800):
    """Cuts a long string, returning the head and tail combined, with the
middle missing. """
    if len(s) <= maxlen:
        return s
    halflen = (min(maxlen, len(s))/2)-6
    return s[:halflen]+"[...snip...]"+s[-halflen:]
snip_string = cut_string # alias

def random_string(size):
    """Return a string of length <size> with random alphanumeric
characters in it."""
    import random
    rng = random.random
    lseq = len(alphanumeric)
    x = range(size)
    for i in x:
        x[i] = alphanumeric[int(rng() * lseq)]
    return "".join(x)

def crange(start, fin):
    """like range(), but for characters."""
    for i in xrange(start, fin+1):
        yield chr(i)

def maketrans(s, d):
    """maketrans(frm, to) -> string
    Return a translation table (a string of 256 bytes long). """
    tbl = range(256) 
    for src, dest in zip(s, d):
        tbl[ord(src)] = ord(dest)
    return "".join(map(chr, tbl))

tbl = ["_"]*256
for c in alphanumeric:
    tbl[ord(c)] = c
_IDENTTABLE = "".join(tbl)
del tbl, c

# build keyword map
import keyword
_KEYWORDS = {}
for kw in keyword.kwlist:
    _KEYWORDS[kw] = kw + "_"
del kw, keyword

def identifier(tag):
    """Return a valid Python identifier given an arbitrary string."""
    tag = str(tag)
    return tag.translate(_IDENTTABLE).capitalize()

def keyword_identifier(name):
    """Return a valid Python keyword identifier given an arbitrary string."""
    ident = name.translate(_IDENTTABLE)
    return _KEYWORDS.get(ident, ident)

# creating a new translation table all the time is annoying. This makes a
# default one automatically.
def translate(string, frm, to, table=None, deletechars=None):
    """Translate a string using table (one will be built if not supplied).
    First remove 'deletechars' characters from 'string', then translate the
    'from' characters to the 'to' characters."""
    table = table or maketrans(frm, to)
    return string.translate(table, deletechars)

# text filters follow
def grep(patt, *args):
    """grep(pattern, objects...)
returns a list of matches given an object, which should usually be a list of
strings, but could be a single string.  """
    regex = re.compile(patt)
    return filter(regex.search, _combine(args))

def cat(*args):
    """cat(obj...)
Combines all objects lines into one list."""
    return _combine(args)

def text(*args):
    """text(object, ...)
Returns all given objects as a single string."""
    return "".join(_combine(args))

def tac(*args):
    """tac(obj...)
Combines all objects lines into one list and returns them in reverse order."""
    l = _combine(args)
    l.reverse()
    return l

def head(*args):
    """Returns the top 10 lines of the combined objects."""
    rv = [] ; c = 0
    for arg in args:
        for item in _tolist(arg):
            if c >= 10:
                break
            rv.append(item)
            c += 1
    return rv

def tail(*args):
    """Returns the bottom 10 lines of the combined objects."""
    return _combine(args)[-10:]

def cksum(*args):
    """cksum(args...)
Returns the crc32 value of arguments."""
    crc = 0
    for arg in args:
        for item in _tolist(arg):
            crc = binascii.crc32(str(item), crc)
    return crc

def md5sum(*args):
    "Return the MD5 sum of the arguments."
    import md5
    m = md5.new()
    for arg in args:
        for item in _tolist(arg):
            m.update(str(item))
    return m.digest()

def sha1sum(*args):
    "Return the SHA1 sum of the arguments."
    import sha
    s = sha.new()
    for arg in args:
        for item in _tolist(arg):
            s.update(str(item))
    return s.digest()

def sort(*args):
    """sort - Returns argument list sorted."""
    rv = _combine(args)
    rv.sort()
    return rv

def uniq(*args):
    "Unique - returns the unique elements of the objects."
    return removedups(_combine(args))

def wc(*args):
    "Word count - returns a tuple of (lines, words, characters) of the objects."
    c = w = l = 0
    for line in _combine(args):
        c += len(line)
        w += len(line.split())
        l += 1
    return l, w, c

def nl(*args):
    "line numbers - prepends line numbers to strings in list."
    rv = []
    for n, s in enumerate(_combine(args)):
        rv.append("%6d  %s" % (n+1, s))
    return rv

def cut(obj, chars=None, fields=None, delim="\t"):
    """cut(obj, bytes=None, chars=None, fields=None, delim="\t")
Cut a section from the list of lines. arguments are tuples, except delim."""
    rv = []
    if chars:
        for line in _tolist(obj):
            st, end = chars # a 2-tuple of start and end positions
            rv.append(line[st:end])
    elif fields:
        for line in _tolist(obj):
            words = line.split(delim)
            wl = []
            for fn in fields:
                wl.append(words[fn])
            rv.append(tuple(wl))
    else:
        raise ValueError, "cut: you must specify either char range or fields"
    return rv

def hexdump(*args):
    "return a hexadecimal string representation of argument lines."
    s = []
    for line in _combine(args):
        s.append(binascii.hexlify(line))
    return "".join(s)

def comm(obj1, obj2):
    raise NotImplementedError

def csplit(*args):
    raise NotImplementedError

def expand(*args):
    raise NotImplementedError

def fold(*args):
    raise NotImplementedError

def join(*args):
    raise NotImplementedError

def od(*args):
    raise NotImplementedError

def paste(*args):
    raise NotImplementedError

def split(*args):
    raise NotImplementedError

def unexpand(*args):
    raise NotImplementedError

# utility functions
def _tolist(obj):
    _to = type(obj)
    if _to is str:
        return [obj]
    elif issubclass(_to, file) or hasattr(obj, "readlines"):
        return obj.readlines()
    else:
        return list(obj)

def _combine(args):
    c = []
    for arg in args:
        c.extend(_tolist(arg))
    return c


def _test(argv):
    print grep("b", "abacdefg")
    print grep("x", "abacdefg")
    print cut(file("/etc/passwd"), fields=(0,), delim=":")

if __name__ == "__main__":
    import sys
    _test(sys.argv)


