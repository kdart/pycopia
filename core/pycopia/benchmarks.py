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
Benchmark support. Tools for helping you choose the best Python implementation
of algorithms and functions. 

"""


import itertools

from pycopia import table
from pycopia.timelib import now


# simple timing loop
def time_it(count, callit, *args, **kwargs):
    start = now()
    for i in range(count):
        callit(*args, **kwargs)
    end = now()
    return (end - start)/count


class FunctionTimerResult(object):
    def __init__(self, name):
        self.name = name
        self.returnvalue = None
        self.runtime = 0.0
        self.overhead = 0.0

    def __str__(self):
        return "%s: %.9f secs" % (self.name, self.runtime)

    def __float__(self):
        return self.runtime

    def __int__(self):
        return int(self.runtime)

    def __long__(self):
        return long(self.runtime)


class ResultSet(list):
    def __str__(self):
        s = map(str, self)
        s.append("--------------------")
        s.append("min: %.9f max: %.9f avg: %.9f" % (self.get_min(), self.get_max(), self.average()))
        return "\n".join(s)

    def get_max(self):
        return reduce(lambda f, n: max(float(f), float(n)), self)

    def get_min(self):
        return reduce(lambda f, n: min(float(f), float(n)), self)

    def average(self):
        sum = reduce(lambda f, n: float(f) + float(n), self)
        return float(sum)/float(len(self))


def _form_name(meth, args, kwargs):
    if args and kwargs:
        return "%s(*%r, **%r)" % (meth.func_name, args, kwargs)
    if args and not kwargs:
        return "%s%r" % (meth.func_name, args)
    if not args and kwargs:
        return "%s(**%r)" % (meth.func_name, kwargs)
    if not args and not kwargs:
        return "%s()" % (meth.func_name,)


class FunctionTimer(object):
    """A class to test run times of callable objects. Use for simple
benchmarks, and to characterize baseline performance."""
    def __init__(self, iterations=10000):
        self._iter = int(iterations)
        self.calibrate()

    def __float__(self):
        return self.runtime

    def calibrate(self):
        print "Calibrating...",
        self._overhead = 0.0
        self._overhead = self.run(lambda x:None, (1,)).runtime
        print "done (%d iterations, %.3f ms of overhead)." % (self._iter, self._overhead*1000.0)

    def run(self, meth, args=(), kwargs={}, argiterator=None):
        res = FunctionTimerResult(_form_name(meth, args, kwargs))
        if argiterator:
            iterator = itertools.cycle(argiterator)
        else:
            iterator = itertools.repeat(args)
        start = now()
        for i in xrange(self._iter):
            args = iterator.next()
            rv = meth(*args, **kwargs)
        end = now()
        res.runtime = ((end - start)/self._iter) - self._overhead
        res.overhead = self._overhead
        res.returnvalue = rv
        return res

_timers = {}
def get_timer(iterations=10000):
    global _timers
    tm = _timers.get(iterations, None)
    if tm is None:
        tm = _timers[iterations] = FunctionTimer(iterations)
    return tm

class BenchMarker(object):
    def __init__(self, testmeth, iterations=10000, loops=1):
        if not callable(testmeth):
            raise TypeError, "test method must be callable"
        self.testmeth = testmeth
        self.loops = loops
        self._timer = get_timer(iterations)

    def get_name(self):
        return self.testmeth.func_name
    name = property(get_name)

    def __call__(self, args=(), kwargs={}, argiterator=None):
        rs = ResultSet()
        for loop in xrange(self.loops):
            rs.append(self._timer.run(self.testmeth, args, kwargs, argiterator))
        return rs


# A report that will contain a matrix of the time ratios comparing each
# measured function with another. returned by CompareResults.get_ratios()
# method.
class RatioReport(table.GenericTable):
    pass

# a table with columns of function (names) and rows of trail-run times (loops).
class CompareResults(table.GenericTable):
    def get_ratios(self):
        rrep = RatioReport(self.headings, title=self.title, width=self.width)
        for rowname in self.headings:
            newrow = []
            for col in self.headings:
                newrow.append(self.average(rowname)/self.average(col))
            rrep.append(newrow, rowname)
        return rrep

    def average(self, col):
        """Return average value of column."""
        sum = reduce(lambda f, n: float(f) + float(n), self.get_column(col))
        return float(sum)/float(len(self))


# This should be  used to compare execution speed of different variants of a
# function.  The functions should take the same arguments, and return the same
# value. It checks that the return values match (i.e. they provide same
# results).
class BenchCompare(object):
    def __init__(self, methodlist, iterations=10000, loops=3):
        assert type(methodlist) in (tuple, list), "methodlist must be sequence of methods"
        self._timer = get_timer(iterations)
        self.loops = loops
        self._methlist = []
        for meth in methodlist:
            if not callable(meth):
                raise TypeError, "test method must be callable"
            self._methlist.append( meth )


    def __call__(self, args=(), kwargs={}, argiterator=None, tablewidth=130):
        headings = map(lambda o: o.func_name, self._methlist)
        names = map(lambda o: _form_name(o, args, kwargs), self._methlist)
        rep = CompareResults(headings, title=" vs. ".join(names), width=tablewidth)
        for loop in xrange(self.loops):
            newrow = []
            for meth in self._methlist:
                newrow.append( self._timer.run(meth, args, kwargs, argiterator) )
            rep.append(newrow, loop)
            # verify consistent return values
            iv = newrow[0]
            for res in newrow[1:]:
                if iv.returnvalue != res.returnvalue:
                    raise ValueError, "inconsistent values returned"
        return rep


if __name__ == "__main__":
    import random
    def F1():
        f = "abcdefgxxxxxxxxxxxxxxxxxx" * random.randint(2, 4000)

    def F2():
        f = "abcdefgxxxxxxxxxxxxxxxxxx" * random.randint(2, 2000)

    bm = BenchMarker(F1, loops=5)
    res = bm()
    print res
    print
    bc = BenchCompare((F1, F2), iterations=1000, loops=3)
    cmpres = bc()
    print cmpres
    print
    rr = CompareResults(["one", "two", "three", "four", "five"])
    rr.append([1,2,3,4,5], 1)
    rr.append([1,2,3,4,5], 2)
    rr.append([1,2,3,4,5], 3)
    rat = rr.get_ratios()
    print rat


