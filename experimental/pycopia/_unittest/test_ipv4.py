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
Test the ipv4 module.

"""

import qatest

from ipv4 import *

TEST_CASES = [
                ("10.1.2.3", None),
                ("0.0.0.0/0", None),
                ("164.1.2.3", None),
                ("192.168.1.1", None),
                ("192.168.1.4/32", None),
                ("192.168.1.5", "255.255.255.255"),
                ("192.168.1.1", "255.255.255.248"),
                ("192.168.1.1", "/27"),
                ("192.168.1.1/28", None),
                ("www.dartworks.biz", None),
                ("www.dartworks.biz/28", None),
                ("www.dartworks.biz", "255.255.255.248"),
                ("192.168.1.2/28", "255.255.255.0"),
                (0xa1010102, None),
                (0xc1020203, 0xfffff000),
                ("192.168.1.2", 0xffffff80),
                (0,0),
                (0xc0020201, "255.255.255.0")
            ]

class IPv4BaseTest(qatest.Test):
    pass


class IPv4Test(IPv4BaseTest):
    def test_method(self):
        for case in TEST_CASES:
            self.info("\ntest case where address=%s mask=%s" % (case[0], case[1]))
            ip = IPv4(case[0], case[1])
            self.info(str( ip ))
            self.info("repr  = %r" % (ip,))

            s = ["\nraw address    = %x" % (ip.address)]
            s.append("raw mask       = %x" % (ip.mask))
            s.append("maskbits       = %u" % (ip.maskbits))
            s.append("network        = %s" % (ip.network))
            s.append("raw host       = %x" % (ip.host))
            s.append("raw broadcast  = %x" % (ip.broadcast))
            self.info("\n".join(s))
        
# XXX
        ip = IPv4("192.168.1.1")
        print ip
        print ip.getStrings()
        ip.mask = "255.255.255.248"
        print ip
        ip.address = "192.168.1.2"
        print ip
        ip.maskbits = 24
        print ip

        net = IPv4("172.22.0.0/16")
        print "net is:", net
        for host in ( IPv4("172.22.0.1/16"), 
                        IPv4("172.24.0.1/16"), 
                        IPv4("172.22.0.1/24") ):
            if host in net:
                print host.cidr(), "in", net.cidr()
            else:
                print host.cidr(), "NOT in", net.cidr()

        return self.passed()



class IPv4Suite(qatest.TestSuite):
    pass


def get_suite(conf):
    suite = IPv4Suite(conf)
    suite.add_test(IPv4Test)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


