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
Make a hard to guess set of passwords.

Basic algorithm:

    * Pick a dictionary word at random. This is so that the password may have
      some mnemonic value.
    * Munge the word in various randomly selected ways.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
import sys
import random

if sys.version_info.major == 3:
    ord = lambda x: x

from pycopia import textutils

WORDPLACES = ["/usr/dict/words", "/usr/share/dict/words"]


def getrandomlist():
    """
    get a list of random bytes from Linux's
    cryptographically strong random number generator.
    """
    fd = os.open("/dev/urandom", os.O_RDONLY)
    try:
        randnums = map(ord, os.read(fd, 256))
    finally:
        os.close(fd)
    return list(randnums)


def getrandomwords(N=2):
    """
    Get a word at random from the system word list.
    The psuedo-random number generator is suitable for this purpose.
    """
    wordlist = []
    wordfile = list(filter(os.path.isfile, WORDPLACES))[0]
    words = open(wordfile, "r").readlines()
    plainword = ""
    i = 0
    while i < N:
        while len(plainword) < 6 or len(plainword) > 15:
            plainword = words[random.randint(1, len(words))]
        wordlist.append(plainword.strip())
        plainword = ""
        i += 1
    return tuple(wordlist)


def hashword(plaintext):
    """
    Munge a plaintext word into something else. Hopefully, the result
    will have some mnemonic value.
    """
    # get a list of random bytes. A byte will be randomly picked from
    # this list when needed.
    rb = getrandomlist()
    # 0.25 chance of case being swapped
    if rb[rb[0]] < 64:
        plaintext = plaintext.swapcase()
    # 0.50 chance of vowels being translated one of two ways.
    if rb[rb[2]] > 127:
        plaintext = plaintext.translate(textutils.maketrans('aeiou AEIOU',
                                                            '@3!0& 4#10%'))
    else:
        plaintext = plaintext.translate(textutils.maketrans('aeiou AEIOU',
                                                            '^#1$~ $3!0&'))
    # 0.1 chance of some additional consonant translation
    if rb[rb[4]] < 25:
        plaintext = plaintext.translate(textutils.maketrans('cglt CGLT', '(<1+ (<1+'))
    # if word is short, add some digits
    if len(plaintext) < 5:
        plaintext = plaintext + repr(rb[5])
    # 0.2 chance of some more digits appended
    if rb[rb[3]] < 51:
        plaintext = plaintext + repr(rb[205])
    return plaintext


def get_hashed_password():
    word = getrandomwords(1)[0]
    return word, hashword(word)


def get_double_word():
    word1, word2 = getrandomwords(2)
    sep = "-=+#:"[random.randint(0,4)]
    return "%s%s%s" % (word1, sep, word2)

## Main part
def main(argv):
    try:
        n = int(argv[1])
    except:
        n = 1
    words = getrandomwords(n)
    munged = map(hashword, words)
    return zip(munged, words)

if __name__ == "__main__":
    for pw, mnemonic in main(sys.argv):
        print ("password is: %s (mnemonic is: %s)" % (pw, mnemonic))
