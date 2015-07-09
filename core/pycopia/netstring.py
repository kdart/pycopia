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
Implements a netstring object, as described in:

http://cr.yp.to/proto/netstrings.txt

"""

def encode(s):
    return "%d:%s," % (len(s), s)

def decode(s):
    c = s.find(":")
    l = int(s[:c])
    ns = s[c+1:c+l+1]
    if len(ns) != l:
        raise ValueError, "invalid netstring, bad length"
    if s[c+l+1] != ",":
        raise ValueError, "invalid encoding, bad terminator"
    return ns


if __name__ == "__main__":
    s = "hello, this is a test!\nagain!"
    es = encode(s)
    print es
    ds = decode(es)
    print ds
    if ds == s:
        print "passed"
    else:
        print "failed"

