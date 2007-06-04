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
A user defineable float type

"""

import operator

class UserFloat(object):
    def __init__(self, data=0.0):
        self.data = float(data)
        
    def __cmp__(self, other):
        if isinstance(other, UserFloat):
            return cmp(self.data, other.data)
        elif isinstance(other, type(self.data)):
            return cmp(self.data, other)
        else:
            return cmp(self.data, float(other))
    def __hash__(self):
        return self.data
    def __str__(self):
        return str(self.data)
    def __repr__(self):
        return "%s(%f)" % (self.__class__.__name__, self.data)

    def __coerce__(self, other):
        if isinstance(other, UserFloat):
            return self.__class__(self.data), self.__class__(other.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data), self.__class__(other)
        elif isinstance(float(other), type(self.data)):
            return self.__class__(self.data), self.__class__(float(other))
        else:
            return None

    def _op(self, other, op):
        if isinstance(other, UserFloat):
            return self.__class__(op(self.data, other.data))
        elif isinstance(other, type(self.data)):
            return self.__class__(op(self.data, other))
        else:
            return self.__class__(op(self.data, float(other)))

    def _rop(self, other, op):
        if isinstance(other, UserFloat):
            return self.__class__(op(other.data, self.data))
        elif isinstance(other, type(self.data)):
            return self.__class__(op(other, self.data))
        else:
            return self.__class__(op(float(other), self.data))

    def _uop(self, op):
        return self.__class__(op(self.data))

    def __add__(self, other):
        return self._op(other, operator.add)
    def __radd__(self, other):
        return self._rop(other, operator.add)
    def __sub__(self, other):
        return self._op(other, operator.sub)
    def __rsub__(self, other):
        return self._rop(other, operator.sub)
    def __mul__(self, other):
        return self._op(other, operator.mul)
    def __rmul__(self, other):
        return self._rop(other, operator.mul)
    def __div__(self, other):
        return self._op(other, operator.div)
    def __rdiv__(self, other):
        return self._rop(other, operator.div)
    def __mod__(self, other):
        return self._op(other, operator.mod)
    def __and__(self, other):
        return self._op(other, operator.and_)
    def __rand__(self, other):
        return self._rop(other, operator.and_)
    def __or__(self, other):
        return self._op(other, operator.or_)
    def __ror__(self, other):
        return self._rop(other, operator.or_)
    def __xor__(self, other):
        return self._op(other, operator.xor)
    def __rxor__(self, other):
        return self._rop(other, operator.xor)
    def __lshift__(self, other):
        return self._op(other, operator.lshift)
    def __rlshift__(self, other):
        return self._rop(other, operator.lshift)
    def __rshift__(self, other):
        return self._op(other, operator.rshift)
    def __rrshift__(self, other):
        return self._rop(other, operator.rshift)
    

    def __abs__(self):
        return self._uop(operator.abs)
    def __invert__(self):
        return self._uop(operator.inv)
    def __pos__(self):
        return self._uop(operator.pos)
    def __neg__(self):
        return self._uop(operator.neg)
    def __int__(self):
        return int(self.data)
    def __long__(self):
        return long(self.data)
    def __float__(self):
        return self.data
    def __complex__(self):
        return complex(self.data)
    def __oct__(self):
        return oct(self.data)
    def __hex__(self):
        return hex(self.data)
    def __nonzero__(self):
        return self.data != 0.0
    

