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
Only truly useful and general functions should go here. Also, things that
fix Python's "warts" can go here. Many of these would be useful as new
builtins. ;-)

"""



import sys
from math import ceil
from errno import EINTR

# have to import this way to avoid a circular import
from _socket import error as SocketError

# Works like None, but is callable and iterable.
class NULLType(type):
    def __new__(cls, name, bases, dct):
        return type.__new__(cls, name, bases, dct)
    def __init__(cls, name, bases, dct):
        super(NULLType, cls).__init__(name, bases, dct)
    def __str__(self):
        return ""
    def __repr__(self):
        return "NULL"
    def __nonzero__(self):
        return False
    def __len__(self):
        return 0
    def __call__(self, *args, **kwargs):
        return None
    def __contains__(self, item):
        return False
    def __iter__(self):
        return self
    def next(*args):
        raise StopIteration
NULL = NULLType("NULL", (type,), {})

# shortcuts to save time
sow = sys.stdout.write
sew = sys.stderr.write
# the embedded vim interpreter replaces stdio with objects that don't have a
# flush method!
try: 
    soflush = sys.stdout.flush
except AttributeError:
    soflush = NULL
try:
    seflush = sys.stderr.flush
except AttributeError:
    seflush = NULL

class Enum(int):
    __slots__ = ("_name")
    def __new__(cls, val, name=None): # name must be optional for unpickling to work
        v = int.__new__(cls, val)
        v._name = str(name)
        return v
    def __getstate__(self):
        return int(self), self._name
    def __setstate__(self, args):
        i, self._name = args
    def __str__(self):
        return self._name
    def __repr__(self):
        return "%s(%d, %r)" % (self.__class__.__name__, self, self._name)

class Enums(list):
    def __init__(self, *init, **kwinit):
        for i, val in enumerate(init):
            if issubclass(type(val), list):
                for j, subval in enumerate(val):
                    self.append(Enum(i+j, str(subval)))
            elif isinstance(val, Enum):
                self.append(val)
            else:
                self.append(Enum(i, str(val)))
        for name, value in kwinit.items():
            enum = Enum(int(value), name)
            self.append(enum)
        self._mapping = None
        self.sort()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, list.__repr__(self))

    # works nicely with Django ORM. :-)
    choices = property(lambda s: map(lambda e: (int(e), str(e)), s))

    def find(self, value):
        if type(value) is str:
            return self.findstring(value)
        else:
            i = self.index(int(value))
            return self[i]

    def get_mapping(self):
        if self._mapping is None:
            d = dict(map(lambda it: (str(it), it), self))
            self._mapping = d
            return d
        else:
            return self._mapping

    def findstring(self, string):
        """Returns the Enum object given a name string."""
        d = self.get_mapping()
        try:
            return d[string]
        except KeyError:
            raise ValueError, "Enum string not found."

# common enumerations
NO = Enum(0, "NO")
YES = Enum(1, "YES")
DEFAULT = Enum(2, "DEFAULT")
UNKNOWN = Enum(3, "UNKNOWN")

# emulate an unsigned 32 bit and 64 bit ints with a long
class unsigned(long):
    floor = 0L
    ceiling = 4294967295L
    bits = 32
    _mask = 0xFFFFFFFFL
    def __new__(cls, val):
        return long.__new__(cls, val)
    def __init__(self, val):
        if val < self.floor or val > self.ceiling:
            raise OverflowError, "value %s out of range for type %s" % (val, self.__class__.__name__)
    def __repr__(self):
        return "%s(%sL)" % (self.__class__.__name__, self)
    def __add__(self, other):
        return self.__class__(long.__add__(self, other))
    def __sub__(self, other):
        return self.__class__(long.__sub__(self, other))
    def __mul__(self, other):
        return self.__class__(long.__mul__(self, other))
    def __floordiv__(self, other):
        return self.__class__(long.__floordiv__(self, other))
    def __mod__(self, other):
        return self.__class__(long.__mod__(self, other))
    def __divmod__(self, other):
        return self.__class__(long.__divmod__(self, other))
    def __pow__(self, other, modulo=None):
        return self.__class__(long.__pow__(self, other, modulo))
    def __lshift__(self, other):
        return self.__class__(long.__lshift__(self, other) & self._mask)
    def __rshift__(self, other):
        return self.__class__(long.__rshift__(self, other))
    def __and__(self, other):
        return self.__class__(long.__and__(self, other))
    def __xor__(self, other):
        return self.__class__(long.__xor__(self, other))
    def __or__(self, other):
        return self.__class__(long.__or__(self, other))
    def __div__(self, other):
        return self.__class__(long.__div__(self, other))
    def __truediv__(self, other):
        return self.__class__(long.__truediv__(self, other))
    def __neg__(self):
        return self.__class__(long.__neg__(self))
    def __pos__(self):
        return self.__class__(long.__pos__(self))
    def __abs__(self):
        return self.__class__(long.__abs__(self))
    def __invert__(self):
        return self.__class__(long.__invert__(self))
    def __radd__(self, other):
        return self.__class__(long.__radd__(self, other))
    def __rand__(self, other):
        return self.__class__(long.__rand__(self, other))
    def __rdiv__(self, other):
        return self.__class__(long.__rdiv__(self, other))
    def __rdivmod__(self, other):
        return self.__class__(long.__rdivmod__(self, other))
    def __rfloordiv__(self, other):
        return self.__class__(long.__rfloordiv__(self, other))
    def __rlshift__(self, other):
        return self.__class__(long.__rlshift__(self, other))
    def __rmod__(self, other):
        return self.__class__(long.__rmod__(self, other))
    def __rmul__(self, other):
        return self.__class__(long.__rmul__(self, other))
    def __ror__(self, other):
        return self.__class__(long.__ror__(self, other))
    def __rpow__(self, other):
        return self.__class__(long.__rpow__(self, other))
    def __rrshift__(self, other):
        return self.__class__(long.__rrshift__(self, other))
    def __rshift__(self, other):
        return self.__class__(long.__rshift__(self, other))
    def __rsub__(self, other):
        return self.__class__(long.__rsub__(self, other))
    def __rtruediv__(self, other):
        return self.__class__(long.__rtruediv__(self, other))
    def __rxor__(self, other):
        return self.__class__(long.__rxor__(self, other))


class unsigned64(unsigned):
    floor = 0L
    ceiling = 18446744073709551615L
    bits = 64
    _mask = 0xFFFFFFFFFFFFFFFFL

# a list that self-maintains a sorted order
class sortedlist(list):
    def insort(self, x):
        hi = len(self)
        lo = 0
        while lo < hi:
            mid = (lo+hi)//2
            if x < self[mid]:
               hi = mid
            else:
               lo = mid+1
        self.insert(lo, x)
    append = insort

# print helpers
def _printobj(obj):
    sow(str(obj))
    sow(" ")

def _printerr(obj):
    sew(str(obj))
    sew(" ")

def Write(*args):
    map (_printobj, args)
    soflush()

def Print(*args):
    """Print is a replacement for the built-in print statement. Except that it
    is a function object.  """
    map (_printobj, args)
    sow("\n")
    soflush()

def Printerr(*args):
    """Printerr writes to stderr."""
    map(_printerr, args)
    sew("\n")
    seflush()

def IF(test, tv, fv=None):
    """Functional 'if' test. """
    if test:
        return tv
    else:
        return fv

def sgn(val):
    """Sign function. Returns -1 if val negative, 0 if zero, and 1 if
    positive.
    """
    try:
        return val._sgn_()
    except AttributeError:
        if val == 0:
            return 0
        if val > 0:
            return 1
        else:
            return -1

# Nice floating point range function from Python snippets
def frange(limit1, limit2=None, increment=1.0):
  """
  Range function that accepts floats (and integers).

  Usage:
  frange(-2, 2, 0.1)
  frange(10)
  frange(10, increment=0.5)

  The returned value is an iterator.  Use list(frange(...)) for a list.
  """
  if limit2 is None:
    limit2, limit1 = limit1, 0.
  else:
    limit1 = float(limit1)
  count = int(ceil((limit2 - limit1)/increment))
  return (limit1 + n*increment for n in xrange(0, count))

class Queue(list):
    def push(self, obj):
        self.insert(0, obj)

class Stack(list):
    def push(self, obj):
        self.append(obj)

# a self-substituting string object. Just set attribute names to mapping names
# that are given in the initializer string.
class mapstr(str):
    def __new__(cls, initstr, **kwargs):
        s = str.__new__(cls, initstr)
        return s
    def __init__(self, initstr, **kwargs):
        d = {}
        for name in _findkeys(self):
            d[name] = kwargs.get(name, None)
        self.__dict__["_attribs"] = d
    def __setattr__(self, name, val):
        if name not in self.__dict__["_attribs"].keys():
            raise AttributeError, "invalid attribute name %r" % (name,)
        self.__dict__["_attribs"][name] = val
    def __getattr__(self, name):
        try:
            return self.__dict__["_attribs"][name]
        except KeyError:
            raise AttributeError, "Invalid attribute %r" % (name,)
    def __str__(self):
        if None in self._attribs.values():
            raise ValueError, "one of the attributes %r is not set" % (self._attribs.keys(),)
        return self % self._attribs
    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self % self._attribs
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str.__repr__(self))
    def attributes(self):
        return self._attribs.keys()

import re
_findkeys = re.compile(r"%\((\w+)\)").findall
del re

# metaclasses... returns a new class with given bases and class attributes
def newclass(name, *bases, **attribs):
    class _NewType(type):
        def __new__(cls):
            return type.__new__(cls, name, bases, attribs)
    return _NewType()

# partial function returns callable with some parameters already setup to run. 
def partial(meth, *args, **kwargs):
    def _lambda(*iargs, **ikwargs):
        iargs = args + iargs
        kwds = kwargs.copy()
        kwds.update(ikwargs)
        return meth(*iargs, **kwds)
    return _lambda

# decorator for making methods enter the debugger on an exception
def debugmethod(meth):
    def _lambda(*iargs, **ikwargs):
        try:
            return meth(*iargs, **ikwargs)
        except:
            ex, val, tb = sys.exc_info()
            from pycopia import debugger
            debugger.post_mortem(tb, ex, val)
    return _lambda

# decorator to make system call methods safe from EINTR
def systemcall(meth):
    def systemcallmeth(*args, **kwargs):
        while 1:
            try:
                rv = meth(*args, **kwargs)
            except EnvironmentError, why:
                if why.args and why.args[0] == EINTR:
                    continue
                else:
                    raise
            except SocketError, why:
                if why.args and why.args[0] == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return rv
    return systemcallmeth


def removedups(s):
    """Return a list of the elements in s, but without duplicates.
Thanks to Tim Peters for fast method.
    """
    n = len(s)
    if n == 0:
        return []
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()
    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti = lasti + 1
            i = i + 1
        return t[:lasti]
    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u


def pprint_list(clist, indent=0, width=74):
    """pprint_list(thelist, [indent, [width]])
Prints the elements of a list to the screen fitting the most elements
per line.  Should not break an element across lines. Sort of like word
wrap for lists."""
    indent = min(max(indent,0),width-1)
    if indent:
        print " " * indent,
    print "[",
    col = indent + 2
    for c in clist[:-1]:
        ps = "%r," % (c)
        col = col + len(ps) + 1
        if col > width:
            print
            col = indent + len(ps) + 1
            if indent:
                print " " * indent,
        print ps,
    if col + len(clist[-1]) > width:
        print
        if indent:
            print " " * indent,
    print "%r ]" % (clist[-1],)

def reorder(datalist, indexlist):
    """reorder(datalist, indexlist)
    Returns a new list that is ordered according to the indexes in the
    indexlist.  
    e.g.
    reorder(["a", "b", "c"], [2, 0, 1]) -> ["c", "a", "b"]
    """
    return [datalist[idx] for idx in indexlist]

def enumerate(collection):
    'Generates an indexed series:  (0,coll[0]), (1,coll[1]) ...'
    i = 0
    it = iter(collection)
    while 1:
        yield (i, it.next())
        i += 1

def flatten(alist):
    rv = []
    for val in alist:
        if isinstance(val, list):
            rv.extend(flatten(val))
        else:
            rv.append(val)
    return rv

def str2hex(s):
    res = ["'"]
    for c in s:
        res.append("\\x%02x" % ord(c))
    res.append("'")
    return "".join(res)

def Import(modname):
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    mod = __import__(modname)
    pathparts = modname.split(".")
    for part in pathparts[1:]:
        mod = getattr(mod, part)
    sys.modules[modname] = mod
    return mod

def add2builtin(name, obj):
    """Add an object to the __builtin__ namespace."""
    setattr(sys.modules['__builtin__'], name, obj)

def add_exception(excclass, name=None):
    """Add an exception to the __builtin__ namespace."""
    name = name or excclass.__name__
    bimod = sys.modules['__builtin__']
    if not hasattr(bimod, name):
        setattr(bimod, name, excclass)

