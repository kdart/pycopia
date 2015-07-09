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
Averaging counters. Computes a running average and an exponentially weighted running average.
"""

import array

class RunningAverage(object):
    """Maintains the current average.

    Call the update() method with a new value periodically.

    Properties:
        ExponentialWeightedRunningAverage
        RunningAverage

    These may be referenced at any time to get the current value.
    """
    def __init__(self, N=5):
        self._X = array.array('d', [0.0]*(N))
        n = self._N = float(N)
        self._alpha = n/(n+1.0)
        self._alphap = 1.0/(n+1.0)
        self._ewra = 0.0

    def update(self, val):
        """Call this to update the average and weighted average."""
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



