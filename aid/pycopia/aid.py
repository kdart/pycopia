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
Collection of general purpose functions and objects that might be considered
general enough to be new built-ins.
"""

from __future__ import print_function


import sys
from math import ceil
from errno import EINTR
from collections import deque
import functools


def add2builtin(name, obj):
    """Add an object to the builtins namespace."""
    bim = sys.modules[_biname]
    if not hasattr(bim, name):
        setattr(bim, name, obj)

def add_exception(excclass, name=None):
    """Add an exception to the builtins namespace."""
    name = name or excclass.__name__
    bimod = sys.modules[_biname]
    if not hasattr(bimod, name):
        setattr(bimod, name, excclass)

# python 3 compatibility
try:
    long
except NameError: # signals python3
    import io
    long = int
    _biname = "builtins"

    def execfile(fn, glbl=None, loc=None):
        glbl = glbl or globals()
        loc = loc or locals()
        exec(open(fn).read(), glbl, loc)
    # add py2-like builtins
    add2builtin("execfile", execfile)
    add2builtin("raw_input", input)
    add2builtin("file", io.BufferedReader)
else: # python 2
    _biname = "__builtin__"
    execfile = execfile

    def enumerate(collection):
        'Generates an indexed series:  (0, collection[0]), (1, collection[1]), ...'
        i = 0
        it = iter(collection)
        while 1:
            yield (i, it.next())
            i += 1

partial = functools.partial


class NULLType(type):
    """Similar to None, but is also a no-op callable and empty iterable."""
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
    def __next__(*args):
        raise StopIteration
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
    """A named number. Behaves as an integer, but produces a name when stringified."""
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
        return "{}({:d}, {!r})".format(self.__class__.__name__, self, self._name)
    def for_json(self):
        return {"_class_": "Enum", "_str_": self._name, "value": int(self)}

class Enums(list):
    """A list of Enum objects."""
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
        return "{}({})".format(self.__class__.__name__, list.__repr__(self))

    # works nicely with WWW framework.
    choices = property(lambda s: map(lambda e: (int(e), str(e)), s))

    def find(self, value):
        """Find the Enum with the given value."""
        i = self.index(int(value))
        return self[i]

    def get_mapping(self):
        """Returns the enumerations as a dictionary with naems as keys."""
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
            raise ValueError("Enum string not found.")

# common enumerations
NO = Enum(0, "NO")
YES = Enum(1, "YES")
DEFAULT = Enum(2, "DEFAULT")
UNKNOWN = Enum(3, "UNKNOWN")

class unsigned(long):
    """Emulate an unsigned 32 bit integer with a long."""
    floor = 0
    ceiling = 4294967295
    bits = 32
    _mask = 0xFFFFFFFF
    def __new__(cls, val):
        return long.__new__(cls, val)
    def __init__(self, val):
        if val < self.floor or val > self.ceiling:
            raise OverflowError("value %s out of range for type %s" % (val, self.__class__.__name__))
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self)
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
    """Emulate an unsigned 64-bit integer."""
    floor = 0
    ceiling = 18446744073709551615
    bits = 64
    _mask = 0xFFFFFFFFFFFFFFFF

class sortedlist(list):
    """A list that maintains a sorted order when appended to."""
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
    """Functional 'if' test. Deprecated, use new Python conditional instead."""
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

  >>> frange(-2, 2, 0.1)
  >>> frange(10)
  >>> frange(10, increment=0.5)

  The returned value is an iterator.  Use list(frange(...)) for a list.
  """
  if limit2 is None:
    limit2, limit1 = limit1, 0.
  else:
    limit1 = float(limit1)
  count = int(ceil((limit2 - limit1)/increment))
  return (limit1 + n*increment for n in xrange(0, count))

class Queue(deque):
    def push(self, obj):
        self.appendleft(obj)

class Stack(deque):
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
            raise AttributeError("invalid attribute name %r" % (name,))
        self.__dict__["_attribs"][name] = val
    def __getattr__(self, name):
        try:
            return self.__dict__["_attribs"][name]
        except KeyError:
            raise AttributeError("Invalid attribute %r" % (name,))
    def __str__(self):
        if None in self._attribs.values():
            raise ValueError("one of the attributes %r is not set" % (self._attribs.keys(),))
        return self % self._attribs
    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self % self._attribs
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str.__repr__(self))
    @property
    def attributes(self):
        return self._attribs.keys()

import re
_findkeys = re.compile(r"%\((\w+)\)").findall
_findfkeys = re.compile(r"[^{]{(\w+)}").findall
del re

class formatstr(str):
    """A string with format-style substitutions (limited to the form {name})
    with attribute style setters, and inspection of defined substitutions (attributes).

    >>> fms = formatstr("This is a {value}.")
    >>> fms.value = "somevalue"
    >>> print (fms)
    >>> fms.value = "othervalue"
    >>> print (fms)
    """
    def __new__(cls, initstr, **kwargs):
        s = str.__new__(cls, initstr)
        return s

    def __init__(self, initstr, **kwargs):
        d = {}
        for name in _findfkeys(self):
            d[name] = kwargs.get(name, None)
        self.__dict__["_attribs"] = d

    def __setattr__(self, name, val):
        if name not in self.__dict__["_attribs"].keys():
            raise AttributeError("invalid attribute name %r" % (name,))
        self.__dict__["_attribs"][name] = val

    def __getattr__(self, name):
        try:
            return self.__dict__["_attribs"][name]
        except KeyError:
            raise AttributeError("Invalid attribute %r" % (name,))

    def __str__(self):
        if None in self._attribs.values():
            raise ValueError("one of the attributes %r is not set" % (self._attribs.keys(),))
        return self.format(**self._attribs)

    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)
        return self.format(**self._attribs)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str.__repr__(self))

    @property
    def attributes(self):
        return list(self._attribs.keys())


def newclass(name, *bases, **attribs):
    """Returns a new class with given name, bases and class attributes."""
    class _NewType(type):
        def __new__(cls):
            return type.__new__(cls, str(name), bases, attribs)
        def __init__(self, *args, **kwargs):
            pass # XXX quick fix for python 2.6, not sure if this is correct. seems to work.
    return _NewType()


def debugmethod(meth):
    """Decorator for making methods enter the debugger on an exception."""
    def _lambda(*iargs, **ikwargs):
        try:
            return meth(*iargs, **ikwargs)
        except:
            ex, val, tb = sys.exc_info()
            from pycopia import debugger
            debugger.post_mortem(tb, ex, val)
    return _lambda

def systemcall(meth):
    """Decorator to make system call methods safe from EINTR."""
    # have to import this way to avoid a circular import
    from _socket import error as SocketError
    def systemcallmeth(*args, **kwargs):
        while 1:
            try:
                rv = meth(*args, **kwargs)
            except EnvironmentError as why:
                if why.args and why.args[0] == EINTR:
                    continue
                else:
                    raise
            except SocketError as why:
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
        return list(u.keys())
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
        print (" " * indent, end="")
    print ("[", end="")
    col = indent + 2
    for c in clist[:-1]:
        ps = "%r," % (c)
        col = col + len(ps) + 1
        if col > width:
            print()
            col = indent + len(ps) + 1
            if indent:
                print (" " * indent, end="")
        print (ps, end="")
    if col + len(clist[-1]) > width:
        print()
        if indent:
            print (" " * indent, end="")
    print ("%r ]" % (clist[-1],))

def reorder(datalist, indexlist):
    """reorder(datalist, indexlist)
    Returns a new list that is ordered according to the indexes in the
    indexlist.
    e.g.
    reorder(["a", "b", "c"], [2, 0, 1]) -> ["c", "a", "b"]
    """
    return [datalist[idx] for idx in indexlist]

def repeat(self,n, f):
    """Call function f, n times."""
    i = n
    while i > 0:
        f()
        i -= 1

def flatten(alist):
    """Flatten a nested set of lists into one list."""
    rv = []
    for val in alist:
        if isinstance(val, list):
            rv.extend(flatten(val))
        else:
            rv.append(val)
    return rv

def str2hex(s):
    """Convert string to hex-encoded string."""
    res = ["'"]
    for c in s:
        res.append("\\x%02x" % ord(c))
    res.append("'")
    return "".join(res)

def hexdigest(s):
    """Convert string to string of hexadecimal string for each character."""
    return "".join(["%02x" % ord(c) for c in s])

def unhexdigest(s):
    """Take a string of hexadecimal numbers (as ascii) and convert to binary string."""
    l = []
    for i in xrange(0, len(s), 2):
        l.append(chr(int(s[i:i+2], 16)))
    return "".join(l)

def Import(modname):
    """Improved __import__ function that returns fully initialized subpackages."""
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    __import__(modname)
    return sys.modules[modname]


