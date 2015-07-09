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

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

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
        es = ls.wait()
        self.assertTrue(es)

    def test_lserror(self):
        ls = proctools.spawnpipe("ls /usr/binxx", merge=0)
        print(ls.read())
        print("errors:")
        print(ls.readerr())
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

#    def test_pipeline(self):
#        ptest = proctools.spawnpipe("cat /etc/hosts | sort")
#        hosts = ptest.read()
#        self.assertTrue(bool(hosts))
#        self.assertFalse(bool(ptest.readerr()))
#        ptest.close()
#        es = ptest.stat()
#        self.assertTrue(es)

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
        proc = sudo.sudo("/bin/ifconfig -a", password=pw)
        print(proc.read())
        print(repr(proc.readerr()))
        proc.wait()
        sudo.sudo_reset()


if __name__ == '__main__':
    unittest.main()




