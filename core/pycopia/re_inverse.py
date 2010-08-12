#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2009  Keith Dart <keith@kdart.com>
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
Analyze regular expressions. Parse the regular expressions and construct a
string that will match it, or a string that will not match it. The
matching string will have some randomness to introduce some
characteristics of Monte Carlo testing. For complex REs, it's not likely
that the same string will be produced twice.

"""
import sys
import re
import sre_parse
import sre_compile
import sre_constants

from pycopia import ascii
try:
  from pycopia import sysrandom as random
except: # Windows...
  import random


class Error(Exception):
    pass

class GeneratorError(Error):
    pass

class UnhandledOpError(Error):
    pass

CATEGORY_SUBS = {
    sre_constants.CATEGORY_DIGIT: ascii.digits,
    sre_constants.CATEGORY_NOT_DIGIT: ascii.letters,
    sre_constants.CATEGORY_SPACE: " \t", # don't want VT or FF
    sre_constants.CATEGORY_NOT_SPACE: ascii.alphanumeric + ascii.punctuation,
    sre_constants.CATEGORY_WORD: ascii.alphanumeric + "_",
    sre_constants.CATEGORY_NOT_WORD: ascii.whitespace + ascii.punctuation,
    sre_constants.CATEGORY_LINEBREAK: ascii.LF,
    sre_constants.CATEGORY_NOT_LINEBREAK: ascii.CR,
#    sre_constants.CATEGORY_LOC_WORD: "XXX",
#    sre_constants.CATEGORY_LOC_NOT_WORD: "XXX",
}

CATEGORY_SUBS_LOCALE = {
    sre_constants.CATEGORY_UNI_DIGIT: "XXX",
    sre_constants.CATEGORY_UNI_NOT_DIGIT: "XXX",
    sre_constants.CATEGORY_UNI_SPACE: "XXX",
    sre_constants.CATEGORY_UNI_NOT_SPACE: "XXX",
    sre_constants.CATEGORY_UNI_WORD: "XXX",
    sre_constants.CATEGORY_UNI_NOT_WORD: "XXX",
    sre_constants.CATEGORY_UNI_LINEBREAK: "XXX",
    sre_constants.CATEGORY_UNI_NOT_LINEBREAK: "XXX",
}

CATEGORY_SUBS_INVERTED = {
    sre_constants.CATEGORY_DIGIT: ascii.letters,
    sre_constants.CATEGORY_NOT_DIGIT: ascii.digits,
    sre_constants.CATEGORY_SPACE: ascii.letters,
    sre_constants.CATEGORY_NOT_SPACE: ascii.whitespace,
    sre_constants.CATEGORY_WORD: ascii.punctuation,
    sre_constants.CATEGORY_NOT_WORD: ascii.alphanumeric + "_",
    sre_constants.CATEGORY_LINEBREAK: "\r",
    sre_constants.CATEGORY_NOT_LINEBREAK: "\n",
#    sre_constants.CATEGORY_LOC_WORD: "XXX",
#    sre_constants.CATEGORY_LOC_NOT_WORD: "XXX",
}

ANYCHAR = ascii.ascii.replace("\n", "")

def get_substitute(category, inverse):
    if inverse:
        return random.choice(CATEGORY_SUBS_INVERTED[category])
    else:
        return random.choice(CATEGORY_SUBS[category])


# simplified flag setting, allows use of string of letter codes.
def get_flags(flags):
    if isinstance(flags, basestring):
        f = 0
        for c in flags:
            f |= sre_parse.FLAGS[c.lower()]
        return f
    else:
        return int(flags)

# simplifed RE compile allows string flags. Bypasses cache.
def compile(regexp, flags=0):
    return sre_compile.compile(regexp, get_flags(flags))


def make_match_string(regexp, flags=0):
    """Given a string that is a regular expression,
    return a string (perhaps with some randomness) that is certain to
    produce a match (we hope).
    """
    s = _make_match_string_from_pattern(sre_parse.parse(regexp, get_flags(flags)), False)
    if __debug__:
        cre = compile(regexp, flags)
        if not cre.match(s):
            raise GeneratorError("'%s' does not match '%s'" % (s, regexp))
    return s


def make_nonmatch_string(regexp, flags=0):
    """Given a string that is a regular expression,
    return a string (perhaps with some randomness) that is certain to
    NOT produce a match.
    """
    s = _make_match_string_from_pattern(sre_parse.parse(regexp, get_flags(flags)), True)
    if __debug__:
        cre = compile(regexp, flags)
        if cre.match(s):
            raise GeneratorError("'%s' matches '%s'" % (s, regexp))
    return s


def _make_match_string_from_pattern(parsetree, makebad=False, groups=None):
    collect = []
    if groups is None:
        groups = {}
    for op, val in parsetree:
        if op is sre_constants.LITERAL:
            if makebad:
                collect.append(chr((val ^ 4) & 0xFF)) # flip bit 4
                if random.randint(0,9) == 0:
                    makebad = False # don't error everything
            else:
                collect.append(chr(val))
        elif op is sre_constants.CATEGORY:
            collect.append(get_substitute(val, makebad))
        elif op is sre_constants.IN:
            if val[0][0] is sre_constants.CATEGORY:
                collect.append(_make_match_string_from_pattern(val, False, groups))
            else:
                collect.append(chr(random.choice(val)[1]))
        elif op is sre_constants.BRANCH:
            collect.append(_make_match_string_from_pattern(val[1][random.randint(0,1)], False, groups))
        elif op is sre_constants.SUBPATTERN:
            string = _make_match_string_from_pattern(val[1], False, groups)
            groups[val[0]] = string
            collect.append(string)
        elif op is sre_constants.MAX_REPEAT or op is sre_constants.MIN_REPEAT:
            for i in xrange(random.randint(val[0], min(val[1], 10))):
                collect.append(_make_match_string_from_pattern(val[2], False, groups))
        elif op is sre_constants.ANY:
            collect.append(random.choice(ANYCHAR))
        elif op is sre_constants.GROUPREF:
            collect.append(groups[val])
        elif op is sre_constants.AT:
            pass # ignore anchors
        else:
            raise UnhandledOpError("Unhandled RE op: %r" % (op,))
    if makebad: # in case it didn't get done yet.
        collect.insert(random.randrange(0, len(collect)), random.choice(ascii.printable))
    return "".join(collect)


class StringGenerator(object):
    def __init__(self, regexp, N=10, bad=False, flags=0):
        self._parsetree = sre_parse.parse(regexp, get_flags(flags))
        self.bad = bad
        self._max = N
        self._i = 0

    def __iter__(self):
        self._i = 0
        return self

    def next(self):
        if self._i < self._max:
            self._i += 1
            return _make_match_string_from_pattern(self._parsetree, self.bad)
        else:
            raise StopIteration


if __name__ == "__main__":
    from pycopia import autodebug
    RE = r'(firstleft|)somestring(\s.*|) \S(a|b) [fgh]+ R{2,3} M{2,5}? (\S)'
    print sre_parse.parse(RE)
    print
    print RE
    print "\nMatchers:"
    for i in range(10):
        ms = make_match_string(RE)
        print ms
    print "\nNON matchers:"
    for i in range(10):
        ms = make_nonmatch_string(RE)
        print ms

