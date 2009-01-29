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
import sre_constants

from pycopia import textutils
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
    sre_constants.CATEGORY_DIGIT: textutils.digits,
    sre_constants.CATEGORY_NOT_DIGIT: textutils.letters,
    sre_constants.CATEGORY_SPACE: " \t", # don't want VT or FF
    sre_constants.CATEGORY_NOT_SPACE: textutils.alphanumeric + textutils.punctuation,
    sre_constants.CATEGORY_WORD: textutils.alphanumeric + "_",
    sre_constants.CATEGORY_NOT_WORD: textutils.whitespace + textutils.punctuation,
}

CATEGORY_SUBS_INVERTED = {
    sre_constants.CATEGORY_DIGIT: textutils.letters,
    sre_constants.CATEGORY_NOT_DIGIT: textutils.digits,
    sre_constants.CATEGORY_SPACE: textutils.letters,
    sre_constants.CATEGORY_NOT_SPACE: textutils.whitespace,
    sre_constants.CATEGORY_WORD: textutils.punctuation,
    sre_constants.CATEGORY_NOT_WORD: textutils.alphanumeric + "_",
}

ANYCHAR = textutils.ascii.replace("\n", "")

def get_substitute(category, inverse):
    if inverse:
        return random.choice(CATEGORY_SUBS_INVERTED[category])
    else:
        return random.choice(CATEGORY_SUBS[category])


def make_match_string(regexp):
    """Given a string that is a regular expression,
    return a string (perhaps with some randomness) that is certain to
    produce a match (we hope).
    """
    s = _make_match_string_from_pattern(sre_parse.parse(regexp), False)
    if __debug__:
        cre = re.compile(regexp, 0)
        if not cre.match(s):
            raise GeneratorError("'%s' does not match '%s'" % (s, regexp))
    return s


def make_nonmatch_string(regexp):
    """Given a string that is a regular expression,
    return a string (perhaps with some randomness) that is certain to
    NOT produce a match.
    """
    s = _make_match_string_from_pattern(sre_parse.parse(regexp), True)
    if __debug__:
        cre = re.compile(regexp, 0)
        if cre.match(s):
            raise GeneratorError("'%s' matches '%s'" % (s, regexp))
    return s


def _make_match_string_from_pattern(parsetree, makebad=False):
    collect = []
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
                collect.append(_make_match_string_from_pattern(val, makebad))
            else:
                collect.append(chr(random.choice(val)[1]))
        elif op is sre_constants.BRANCH:
            collect.append(_make_match_string_from_pattern(val[1][random.randint(0,1)]))
        elif op is sre_constants.SUBPATTERN:
            collect.append(_make_match_string_from_pattern(val[1]))
        elif op is sre_constants.MAX_REPEAT or op is sre_constants.MIN_REPEAT:
            for i in xrange(random.randint(val[0], min(val[1], 10))):
                collect.append(_make_match_string_from_pattern(val[2]))
        elif op is sre_constants.ANY:
            collect.append(random.choice(ANYCHAR))
        elif op is sre_constants.AT:
            pass # ignore anchors
        else:
            UnhandledOpError("Unhandled RE op: %r" % (op,))
    if makebad: # in case it didn't get done yet.
        collect.insert(random.randrange(0, len(collect)), random.choice(textutils.printable))
    return "".join(collect)


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

