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

from pycopia import anypath
from pycopia import asyncinterface
from pycopia import asyncio
from pycopia import asyncserver
#from pycopia import autodebug
from pycopia import basicconfig
from pycopia import benchmarks
from pycopia import charbuffer
from pycopia import cliutils
from pycopia import combinatorics
from pycopia import daemonize
from pycopia import environ
from pycopia import ezmail
from pycopia import fsm
from pycopia import gtktools
from pycopia import guid
from pycopia import interactive
from pycopia import ipv4
from pycopia import logfile
from pycopia import makepassword
from pycopia import md5lib
from pycopia import methodholder
from pycopia import netstring
from pycopia import ringbuffer
from pycopia import rot13
from pycopia import scheduler
from pycopia import sharedbuffer
from pycopia import smtp_envelope
from pycopia import sourcegen
from pycopia import shparser
from pycopia import table
from pycopia import texttools
from pycopia import passwd

from pycopia.inet import ABNF
from pycopia.inet import CGI
from pycopia.inet import cgi_test
from pycopia.inet import DICT
from pycopia.inet import fcgi
from pycopia.inet import HTTP
from pycopia.inet import httputils
from pycopia.inet import mailaliases
from pycopia.inet import rfc2822
from pycopia.inet import SMTP
from pycopia.inet import telnet
from pycopia.inet import toc
from pycopia.inet import XHTMLcgi

from pycopia.ISO import iso3166
from pycopia.ISO import iso639a

import pycopia.OS


class CoreTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_ipv4(self):
        """basic test of ipv4 module."""

        r1 = ipv4.IPRange("172.22.1.11/24", "172.22.1.21/24")
        r2 = ipv4.IPRange("172.22.1.21/24", "172.22.1.11/24")
        r3 = ipv4.IPRange("172.22.1.55/24", "172.22.1.55/24")

        l1 = list(r1)
        l2 = list(r2)
        print l1
        print l1 == l2
        print r3, list(r3)

        ip = ipv4.IPv4("172.22.4.1/24")
        print ip.address
        ip.address = "172.22.4.2/24"
        print ip.address
        ip.address = -1407843325
        print ip.CIDR

        ip = ipv4.IPv4("1.1.1.1/30")
        print len(ip)
        print len(ipv4.IPv4("1.1.1.1/29"))
        print len(ipv4.IPv4("1.1.1.1/28"))
        print len(ipv4.IPv4("1.1.1.1/24"))
        for each_ip in ip:
            print each_ip

    def test_passwd(argv):
        pwent = passwd.getpwself()
        print repr(pwent)
        print str(pwent)
        print int(pwent)
        print pwent.name
        print pwent.home
        print pwent.uid
        print pwent[3]

    def test_shparser(self):
        sh = shparser.ShellParser(_print_argv)
        args = sh.feedline('echo -q -N "" -t tparm -b 1024 -f "bogus one" $PATH ${PATH}')
        print args

if __name__ == "__main__":
    import sys
    _test(sys.argv)

def _print_argv(argv):
    print repr(argv)


if __name__ == '__main__':
    unittest.main()
