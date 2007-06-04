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

from pycopia import proctools
from pycopia import crontab
from pycopia import expect
from pycopia import netcat
from pycopia import proctools
#from pycopia import redir
from pycopia import rsynclib
from pycopia import sshlib
from pycopia import sudo
#from pycopia import xselection

def _sub_function():
    from pycopia import scheduler
    scheduler.sleep(5)
    return None

def _co_function():
    import sys
    from pycopia import scheduler
    sys.stdout.write("hello from co_function\n")
    scheduler.sleep(5)
    return None

class ProcessTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_spawnpipe(self):
        ls = proctools.spawnpipe("ls /usr/bin")
        files = ls.read()
        self.assertTrue(files)
        self.assertFalse(ls.readerr())
        ls.close()
        es = ls.stat()
        self.assertTrue(es)

    def test_lserror(self):
        ls = proctools.spawnpipe("ls /usr/binxx", merge=0)
        print ls.read()
        print "errors:"
        print ls.readerr()
        ls.close()
        ls.wait()
        es = ls.stat()
        self.assertFalse(es)

    def test_readaline(self):
        lspm = proctools.spawnpipe("ls /bin")
        lines = lspm.readlines()
        self.assertTrue(lines)
        lspm.close()
        es = lspm.stat()
        self.assertTrue(es)

    def test_pipeline(self):
        ptest = proctools.spawnpipe("cat /etc/hosts | sort")
        hosts = ptest.read()
        self.assertTrue(bool(hosts))
        self.assertFalse(bool(ptest.readerr()))
        ptest.close()
        es = ptest.stat()
        self.assertTrue(es)

    def test_subprocess(self):
        sub = proctools.subprocess(_sub_function)
        es = sub.wait()
        self.assertTrue(es)

    def test_coprocess(self):
        sub = proctools.coprocess(_co_function)
        line = sub.readline()
        es = sub.wait()
        self.assertTrue(es)

    def XXXtest_sudo(self):
        pw = sudo.getpw()
        proc = sudo.sudo("/sbin/ifconfig -a", password=pw)
        print proc.read()
        print repr(proc.readerr())
        proc.wait()
        sudo.sudo_reset()


if __name__ == '__main__':
    unittest.main()



