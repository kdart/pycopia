
"""
Network package unit tests.
"""

import unittest

from pycopia import clientserver
from pycopia import measure
from pycopia import model

from pycopia import ping
from pycopia import slogsink
from pycopia import dnsupdate
from pycopia import ifconfig
from pycopia import simpleserver
from pycopia import smtpCLI
from pycopia import imapCLI

from pycopia.clientserver.clients import smtp
from pycopia.clientserver.clients import udp

from pycopia.clientserver.servers import udp

from pycopia.measure import Counters


class NetTests(unittest.TestCase):

    def test_ping(self):
        """Run a ping."""
        self.assert_(bool(ping.reachable("localhost")))

    def test_runningaverage(self):
        rc = Counters.RunningAverage()
        rc.update(1200)
        rc.update(1300)
        print rc.RunningAverage, rc.EWRA
        rc.update(1250)
        rc.update(0)
        rc.update(1400)
        rc.update(1100)
        print rc.RunningAverage, rc.EWRA

    def test_thousands(self):
        print "-- thousands --"
        rce = Counters.RunningAverage()
        print rce.EWRA, rce._X
        print rce.RunningAverage, rce.EWRA
        for i in range(20):
            rce.update(1000)
            print rce.RunningAverage, rce.EWRA

    def test_increasing(self):
        print "-- increasing --"
        rci = Counters.RunningAverage()
        print rci.EWRA, rci._X
        print rci.RunningAverage, rci.EWRA
        for i in range(20):
            rci.update(100*i)
            print rci.RunningAverage, rci.EWRA


if __name__ == '__main__':
    unittest.main()
