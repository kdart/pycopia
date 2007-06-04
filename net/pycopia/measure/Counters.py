#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Averaging counters.

"""

import array

class RunningAverage(object):
    def __init__(self, N=5):
        self._X = array.array('d', [0.0]*(N))
        n = self._N = float(N)
        self._alpha = n/(n+1.0)
        self._alphap = 1.0/(n+1.0)
        self._ewra = 0.0

    def update(self, val):
        val = float(val)
        self._ewra = self._ExponentialWeightedRunningAverage()
        self._X.insert(0, val)
        del self._X[-1]
    append = update

    def _RunningAverage(self):
        return sum(self._X)/(self._N)
    RunningAverage = property(_RunningAverage)
    RA = RunningAverage

    def _ExponentialWeightedRunningAverage(self):
        pwr = pow
        a = self._alpha
        ap = self._alphap
        X = self._X

        s = ap*X[0]
        for i in range(1, len(X)):
            s += pwr(a, i)*ap*X[i]
        s += pwr(a, len(X))*self._ewra
        return s
    ExponentialWeightedRunningAverage = property(_ExponentialWeightedRunningAverage)
    EWRA = ExponentialWeightedRunningAverage 



