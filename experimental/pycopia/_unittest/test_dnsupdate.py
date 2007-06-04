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
Test the Dynamic DNS resolver.

"""



import qatest

import dnsupdate
import time, socket # for the resolver stuff


class DNSTests(qatest.Test):
    def initialize(self):
        du = dnsupdate.get_dnsupdate()
        du.server(self.config.dnsserver, 53)
        du.key(self.config.keyname, self.config.secret)
        du.zone(self.config.zone)
        self.updater = du

    def finalize(self):
        self.updater.send()
        self.updater.close()
        del self.updater

class DNSUpdate(DNSTests):
    def test_method(self):
        name, addr = self.config.test_add
        self.updater.add_A(name, addr)
        self.updater.send()
        time.sleep(2)
        try:
            r = socket.gethostbyname(self.config.fqdn)
        except socket.gaierror, err:
            return self.abort("failed to add name '%s' [%s]" % (self.config.fqdn, err))
        self.assert_equal(addr, r)
        return self.passed("update ok")

class DNSDelete(DNSTests):
    def test_method(self):
        name, addr = self.config.test_add
        self.updater.delete_A(name)
        self.updater.send()
        time.sleep(2)
        try:
            r = socket.gethostbyname(self.config.fqdn)
        except socket.gaierror, err:
            return self.passed("removed name '%s' [%s]" % (self.config.fqdn, err))
        else:
            return self.failed("resolved '%s' after deleting it." % (self.config.fqdn,))

class DNSSuite(qatest.TestSuite):
    pass


def get_suite(cf):
    suite = DNSSuite(cf)
    suite.add_test(DNSUpdate)
    suite.add_test(DNSDelete)
    return suite

def run(cf):
    # create the suite and add the test cases. 
    suite = get_suite(cf)
    # run the suite
    suite()

