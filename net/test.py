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

#    def test_tcpserver(self):
#        """Test basic client server."""
#        srv = clientserver.TCPServer(clientserver.EchoWorker)
##        srv.run()
#
#    def test_tcpclient(self):
#        ec = clientserver.EchoClient("localhost")
##        ec.run()
#
#    def test_udpserver(self):
#        srv = clientserver.UDPServer(clientserver.UDPEchoWorker)
##        srv.run()
#
#    def test_udpclient(self):
#        srv = clientserver.UDPEchoClient("localhost")
##        srv.run()

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
