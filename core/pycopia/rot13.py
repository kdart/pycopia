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

