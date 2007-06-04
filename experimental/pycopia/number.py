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
Number module contains Number class that can represent any number using an
arbitrary base and arbitrary symbol set.

"""

class Number(object):
    def __init__(self, symbols, init=0, sep="", sign=1):
        self.symbols = list(symbols)
        self.sign = sign
        self.sep = sep
        self.radix = len(self.symbols)
        self._convert(init)

    def __copy__(self):
        return self.__class__(self.symbols, self.value[:], self.sep, self.sign)
    copy = __copy__

    def _convert(self, val):
        r = self.radix
        if isinstance(val, self.__class__):
            self.value = val.value[:]
            self.sign = val.sign
            return
        val_type = type(val)
        if val_type is list: # for eval(repr(Number())) don't use this yourself!
            self.value = map(lambda o: o % r, val)
            return
        if val_type is not int and val_type is not long:
            raise ValueError, "Number: initializer must be list, Number instance, or integer."
        if val < 0:
            val = -val
            self.sign = -1
        else:
            self.sign = 1
        val, rem = divmod(val, r)
        rv = [rem]
        while val:
            val, rem = divmod(val, r)
            rv.append(rem)
        self.value = rv
    
    def zero(self):
        self.value = [0]
        self.sign = 1

    def increment(self, inc=1):
        carry, new = divmod(self.value[0]+inc, self.radix)
        self.value[0] = new
        return carry, self

    def __str__(self):
        s = map(lambda i: self.symbols[i], self.value)
        s.reverse()
        if self.sign == 1:
            return self.sep.join(s)
        else:
            return "-"+self.sep.join(s)
    
    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.symbols, self.value, self.sep, self.sign)

    def __nonzero__(self):
        return (len(self.value)-1) or self.value[0]

    def __int__(self):
        acc = 0
        r = self.radix
        for p in xrange(len(self.value)):
            acc += self.value[p]*pow(r, p)
        return acc

    def range(self, start, end=None, stride=1):
        return NumberIter(self, start, end, stride)

    def __coerce__(self, other):
        return self, self.__class__(self.symbols, other, self.sep)

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return self.value <= other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __ne__(self, other):
        return self.value != other.value

    def __cmp__(self, other):
        if self.value < other.value:
            return -1
        elif self.value > other.value:
            return 1
        else:
            return 0

    def __hash__(self):
        return reduce(lambda a,b: a^b, self.value)

    def __add__(self, other):
        r = self.radix
        carry = 0
        res = []
        for x, y in map(None, self.value, other.value):
            x = x or 0 # remove None values
            y = y or 0
            y = y * other.sign
            carry, sum = divmod(x+y+carry, r)
            res.append(sum)
        if carry:
            res.append(carry)
        return self.__class__(self.symbols, res, self.sep, self.sign)

    def __iadd__(self, other):
        r = self.radix
        carry = 0
        res = []
        for x, y in map(None, self.value, other.value):
            x = x or 0 # remove None values
            y = y or 0
            carry, sum = divmod(x+y+carry, r)
            res.append(sum)
        if carry:
            res.append(carry)
        self.value = res
        return self

    def __neg__(self):
        self.sign *= -1

    def __sub__(self, other):
        r = self.radix
        borrow = 0
        res = []
#XXX

    def _borrow(self, digit):
        pass

    
    def __divmod__(self, other):
        #XXX
        pass

# XXX
    def __floordiv__(self, other):
        return self.__divmod__(other)[0]

    def __mod__(self, other):
        return self.__divmod__(other)[1]

#   def __div__(self, other):
#       pass


class NumberIter(object):
    def __init__(self, numobj, start, end, stride):
        self.numobj = numobj
        self.value = Number(numobj.symbols, start)
        self.end = Number(numobj.symbols, end)
        self.stride = Number(numobj.symbols, stride)

    def __iter__(self):
        return self
    
    def next(self):
        if self.value < self.end:
            self.value += self.stride
            return Number(self.numobj.symbols, self.value, self.numobj.sep)
        raise StopIteration


# utility class used by BinCounter
class CountedElement(object):
    def __init__(self, element, counter):
        self.element = element
        self.counter = counter # a Number class
    
    def cycle(self, inc=1):
        return self.counter.increment(inc)
    
    def reset(self):
        self.counter.zero()
    
    def __int__(self):
        return int(self.counter)
    
    def __str__(self):
        return str(self.element)
    
    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__, self.element, self.counter)


class BinCounter(object):
    def __init__(self, bins):
        self.elements = []
        self.counter = bins

    def cycle(self, inc=1):
        self._cycle(inc=inc)
    
    def _cycle(self, idx=0, inc=1):
        carry, counter = self.elements[idx].cycle(inc)
        if carry:
            if idx < (len(self.elements)-1):
                self._cycle(idx+1, inc)

    def fetch(self):
        bins = []
        for i in xrange(self.counter.radix):
            bins.append(list())
        for el in self.elements:
            bins[int(el)].append(el.element)
        return bins
    
    def __iter__(self):
        self.reset()
        return self
    
    def next(self):
        if self._count < self._maxiter:
            self._count += 1
            rv = self.fetch()
            self._cycle()
            return rv
        else:
            raise StopIteration

    def append(self, element):
        self.elements.append(CountedElement(element, self.counter.copy()))

    def extend(self, ellist):
        self.elements.extend(map(lambda o: CountedElement(o, self.counter.copy()), ellist))

    def __str__(self):
        s = []
        for bin in self.fetch():
            bs = ",".join(map(str, bin))
            s.append(bs)
        return ";   ".join(s)

    def reset(self):
        self._count = 0
        self._maxiter = self.counter.radix**len(self.elements)
        map(lambda o: o.reset(), self.elements)
    

# works like range() but produces a sequence of Number classes.
def nrange(symbols, start, end=None, stride=1):
    if end is None:
        return [i for i in Number(symbols).range(0, start, stride)]
    else:
        return [i for i in Number(symbols).range(start, end, stride)]

def number(val, sep=","):
    symbols = val.split(sep)
    return Number(symbols, val, sep)



if __name__ == "__main__":
    # test with a base 10 number
    n = Number("0123456789", 100)
    for i in xrange(10):
        print 100+i,"==", n+i, "==", int(n+i), "?"

    nm = Number("0123456789", -100)
    print nm
    print nm+100

