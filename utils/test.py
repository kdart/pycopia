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


"""

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
    print 'Alarmed in %.4f' % ( time.time() - s )
    s = time.time()

class UtilsTests(unittest.TestCase):

    def test_itimer(self):
        signal.signal(signal.SIGALRM, catcher)
        print 'Setting alarm for 0.3 seconds with repeat every 0.5 seconds'
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
        print 'Setting alarm for 0.3 seconds'
        start = s = time.time()
        itimer.alarm(0.3)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 0.3, places=2)

        print 'Setting alarm for 1.1 seconds'
        start = s = time.time()
        itimer.alarm(1.1)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 1.1, places=2)

        print 'Setting alarm for 5.5 seconds'
        start = s = time.time()
        itimer.alarm(5.5)
        signal.pause()
        self.assertAlmostEqual(time.time()-start, 5.5, places=2)
        itimer.alarm(0)
        olddelay, oldinterval = itimer.getitimer(itimer.ITIMER_REAL)
        self.assertEqual(olddelay, 0.0)
        self.assertEqual(oldinterval, 0.0)


if __name__ == '__main__':
    unittest.main()
