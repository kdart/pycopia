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
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import unittest
import signal
import time

import readline
import fcntl
import mmap
from pycopia import itimer

s = time.time()

def catcher(n,f):
    global s
    print('Alarmed in %.4f' % ( time.time() - s ))
    s = time.time()

class UtilsTests(unittest.TestCase):

    def test_itimer(self):
        signal.signal(signal.SIGALRM, catcher)
        print('Setting alarm for 0.3 seconds with repeat every 0.5 seconds')
        try:
            itimer.setitimer(itimer.ITIMER_REAL, 0.3, 0.5)
            initial, interval =  itimer.getitimer(itimer.ITIMER_REAL)
            self.assertAlmostEqual(initial, 0.3, places=2)
            self.assertAlmostEqual(interval, 0.5, places=2)
            signal.pause()
            signal.pause()
            signal.pause()
        finally:
            itimer.setitimer(itimer.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)

    def test_z_alarm(self):
        global s
        signal.signal(signal.SIGALRM, catcher)
        print('Setting alarm for 0.3 seconds')
        start = s = time.time()
        itimer.alarm(0.3)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 0.3, places=2)

        print('Setting alarm for 1.1 seconds')
        start = s = time.time()
        itimer.alarm(1.1)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 1.1, places=2)

        print('Setting alarm for 5.5 seconds')
        start = s = time.time()
        itimer.alarm(5.5)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 5.5, places=2)
        itimer.alarm(0)
        olddelay, oldinterval = itimer.getitimer(itimer.ITIMER_REAL)
        self.assertEqual(olddelay, 0.0)
        self.assertEqual(oldinterval, 0.0)

    def test_nanosleep(self):
        global s
        signal.signal(signal.SIGALRM, catcher)
        start = s = time.time()
        try:
            itimer.alarm(2.0)
            itimer.nanosleep(10.0)
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
        self.assertAlmostEqual(time.time()-start, 10.0, places=2)

    def test_absolutesleep(self):
        global s
        signal.signal(signal.SIGALRM, catcher)
        start = s = time.time()
        try:
            itimer.alarm(2.0)
            itimer.absolutesleep(start + 10.0)
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
        self.assertAlmostEqual(time.time()-start, 10.0, places=2)

    def test_FDTimer(self):
        t = itimer.FDTimer()
        self.assertFalse(t)
        t.settime(5.0, 2.0)
        self.assertTrue(t)
        start = time.time()
        print(t.read())
        self.assertAlmostEqual(time.time()-start, 5.0, places=2)
        print(t.read())
        self.assertAlmostEqual(time.time()-start, 7.0, places=2)
        print(t.read())
        self.assertAlmostEqual(time.time()-start, 9.0, places=2)
        t.close()
        self.assertFalse(t)
        self.assertTrue(t.closed)

    def test_FDTimer_absolute(self):
        t = itimer.FDTimer(itimer.CLOCK_MONOTONIC)
        start = time.time()
        t.settime(itimer.gettime(itimer.CLOCK_MONOTONIC)+5.0, 0.0, absolute=True)
        print(t.read())
        t.close()
        self.assertAlmostEqual(time.time()-start, 5.0, places=2)

if __name__ == '__main__':
    unittest.main()
