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
Test sshlib functions.

"""

import qatest
import os, getpass

import sshlib

class SSHlibBaseTest(qatest.Test):
    def get_password(self):
        pw = getpass.getpass("Password for ssh and scp client tests:")
        return pw   

class SSHlib_scp(SSHlibBaseTest):
    def test_method(self):
        try:
            os.unlink("/tmp/hosts")
        except OSError, err:
            pass
        pw = self.get_password()
        es = sshlib.scp(srcpath="/etc/hosts", dsthost="localhost", dstpath="/tmp/", 
                password=pw, logfile=self.config.logfile)
        if es:
            if os.path.isfile("/tmp/hosts"):
                return self.passed("successful scp of hosts file")
            else:
                return self.failed("Hosts file not copied")
        else:
            self.diagnostic(str(es))
            return self.failed("scp returned failure")


class SSHlibSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = SSHlibSuite(conf)
    suite.add_test(SSHlib_scp)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


