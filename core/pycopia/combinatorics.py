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
Functions and classes for doing object permutation.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys

if sys.version_info.major == 3:
    basestring = str

from functools import reduce

def factorial(x):
    """factorial(x)
    return x!
    """
    return x<=0 or reduce(lambda a,b: a*b, range(1,x+1) )
fact = factorial

def nCr(n, r):
    "nCr = n! / ( (n-r)! * r! )"
    return factorial(n) / ( factorial(n-r) * factorial(r))
combinations = nCr

def nPr(n, r):
    "nPr = n! / (n-r)!"
    return factorial(n) / factorial(n-r)
permutations = nPr


class Permuter(object):
    def __init__(self, seq):
        self.seq = seq

    def __iter__(self):
        return PermuterIter(self.seq)

    def __getitem__(self, idx):
        return get_permutation(self.seq, idx)

    def __len__(self):
        return factorial(len(self.seq))


class PermuterIter(object):
    def __init__(self, seq):
        self.seq = seq
        self.maximum = factorial(len(seq))
        self.i = 0
        self.is_string = isinstance(seq, basestring)

    def __iter__(self):
        return (self)

    def __next__(self):
        if self.i >= self.maximum:
            raise StopIteration
        n = get_permutation(self.seq, self.i)
        self.i += 1
        if self.is_string:
            return "".join(n)
        else:
            return n
    next = __next__


# default pruning policy. Other possibilites are random selection or upper end.
def prune_end(n, l):
    return l[:n]


class ListCounter(object):
    """An iterator that counts through its list of lists."""
    def __init__(self, lists):
        self._lists = lists
        self._lengths = [len(l) for l in lists]
        if self._lengths.count(0) > 0:
            raise ValueError("All lists must have at least one element.")
        self._places = len(self._lengths)
        self.reset()

    def reset(self):
        self._counters = [0] * self._places
        self._counters[0] -= 1

    def __iter__(self):
        self.reset()
        return self

    def __next__(self):
        self._increment(0)
        return self.fetch()
    next = __next__

    def _increment(self, place):
        carry, self._counters[place] = divmod(self._counters[place]+1, self._lengths[place])
        if carry:
            if place+1 < self._places:
                return self._increment(place+1)
            else:
                raise StopIteration
        return carry

    def fetch(self):
        return [l[i] for l, i in zip(self._lists, self._counters)]

    def get_number(self):
        return reduce(lambda a,b: a*b, self._lengths, 1)


class KeywordCounter(object):
    """Instantiate this as you would any callable with keyword arguments,
    except that the keyword values should be a list of possible values. When
    you iterate over it it will return a dictionary with values cycle through
    the set of possible values.
    """
    def __init__(self, **kwargs):
        self._names = kwargs.keys()
        self._counter = ListCounter(kwargs.values()) # values should be sequences

    def prune(self, maxN, chooser=prune_end):
        lists = prune(maxN, self._counter._lists, chooser)
        self._counter = ListCounter(lists)

    def __iter__(self):
        self._counter.reset()
        return self

    def __next__(self):
        values = self._counter.next() # the list counter will raise StopIteration
        return self.fetch(values)
    next = __next__

    def get_number(self):
        return self._counter.get_number()

    def fetch(self, values):
        return dict(zip(self._names, values))



# Python algorithm from snippet by Christos Georgiou
def get_permutation(seq, index):
    "Returns the <index>th permutation of <seq>"
    seqc= list(seq[:])
    seqn= [seqc.pop()]
    divider= 2 # divider is meant to be len(seqn)+1, just a bit faster
    while seqc:
        index, new_index= index // divider, index % divider
        seqn.insert(new_index, seqc.pop())
        divider += 1
    return seqn


def unique_combinations(items, n):
    if n==0:
        yield []
    else:
        for i in range(len(items)):
            for cc in unique_combinations(items[i+1:], n-1):
                yield [items[i]] + cc


def prune(maxN, sets, chooser=prune_end):
    """Prune a collection of sets such that number of combinations is less than
    or equal to maxN.  Use this to set an upper bound on combinations and you
    don't care if you "hit" all combinations.  This simple algorithm basically
    reduces the number of entries taken from the largest set. If then are equal
    numbered, then removal is left to right.

    maxN is the maximum number of combinations.
    sets is a list of lists containing the items to be combined.
    chooser implements the pruning policy. It should be a function taking a
    number, N, and a list and returning a new list with N elements.
    """
    lenlist = [len(l) for l in sets]
    while reduce(lambda a,b: a*b, lenlist, 1) > maxN:
        lv, li = maxi(lenlist)
        lenlist[li] -= 1
    return [chooser(n, l) for n, l in zip(lenlist, sets)]


def maxi(seq):
    cmax = seq[0]
    ci = 0
    for i, val in enumerate(seq):
        if val > cmax:
            cmax = val
            ci = i
    return cmax, ci


# some self test if run as main script
if __name__ == "__main__":
    from pycopia import interactive
    perm = Permuter("abc")
    for p in perm:
        print (p)

    perm = Permuter(range(10))
    for i in [0, 1, 10, 55, 1000, 3600000, 3628799, 3628800]:
        print (perm[i])

    print ("---")

#    10*5*2 = 100
    s1 = range(10)
    s2 = range(5)
    s3 = range(2)
    lc = ListCounter(prune(60, [s1, s2, s3]))
    print (lc.get_number())
    for i, l in enumerate(lc):
        print ("%02d. %s" % (i, l))

    try:
        badlc = ListCounter([[], s2, s3])
    except ValueError:
        pass
    else:
        print ("*** didn't find zero length")

    kc = KeywordCounter(arg1=s1, arg2=s2, arg3=s3)
    print (kc.get_number())
    for kwargs in kc:
        print (kwargs)

