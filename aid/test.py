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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import unittest

from pycopia import aid
from pycopia import dictlib
from pycopia import UserFile
from pycopia import getopt
from pycopia import gzip
from pycopia import socket
from pycopia import timelib
from pycopia import tty
from pycopia import urlparse
from pycopia import textutils
from pycopia import timespec

class MyBaseClass(object):
    pass

class AidTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_mapstr(self):
        TEST = aid.mapstr("some%(one)s one\nsome%(two)s three\nsome%(three)s four")
        print(TEST.attributes)
        try:
            print(TEST)
        except ValueError:
            print("got correct error from %r" % TEST)
        TEST.one = "one"
        TEST.two = "thing"
        TEST.three = "where"
        print(TEST)
        s = str(TEST) # makes new, substituted, string
        assert s == "someone one\nsomething three\nsomewhere four"
        print(TEST.three)

    def test_formatstr(self):
        src = "one {one} {{notaone}} two {two}"
        fmt = aid.formatstr(src)
        assert src.format(one="ONE", two="TWO") == fmt(one="ONE", two="TWO")
        assert fmt.attributes == ["two", "one"]

    def test_newclass(self):
        New = aid.newclass("New", MyBaseClass)
        print(New())

    def test_AttrDictWrapper(self):
        ld = {"one":1, "two":2, "three":3}
        gd = {"gbone":1, "gbtwo":2, "gbthree":3}
        lw = dictlib.AttrDictWrapper(ld)
        lw.four = gd
        print(lw.one)
        print(lw.two)
        print(lw.four.gbone)
        print(lw.four["gbtwo"])

    def test_AttrDict(self):
        d = dictlib.AttrDict()
        d.one = "one"
        print(d)
        print(d.get)
        print(d.one)
        print(d["one"])
        d["two"] = 2
        print(d.two)
        print(d["two"])

    def test_UserFile(self):
        fd = UserFile.UserFile("/etc/hosts", "rb")
        while 1:
            d = fd.read(1024)
            if not d:
                break
        fd.close()

    def test_timelib(self):
        mt = timelib.localtime_mutable()
        print(mt)
        mt.add_seconds(3600)
        print(mt)
        print(timelib.strftime("%Y-%m-%d", timelib.weekof(timelib.time())))

        t = timelib.now()
        for d in range(1, 60):
            week = timelib.weekof(t+(d*60*60*24))
            print(timelib.MutableTime(week))

        print("Local time:")
        print(timelib.localtimestamp())

        p = timespec.TimespecParser()
        for spec, secs in [
            ("0s", 0.0),
            ("3m", 180.0),
            ("3.0m", 180.0),
            ("3minute+2secs", 182.0),
            ("2h 3minute+2.2secs", 7382.2),
            ("-3m", -180.0),
            ("-3.0m", -180.0),
            ("1h3m", 3780.0),
            ("1h-3m", 3420.0),
            ("1d 3m", 86580.0)]:
            p.parse(spec)
            self.assert_(p.seconds == secs)

        self.assertRaises(ValueError, p.parse, "12m -m")

    def XXXtest_tty_SerialPort(self):
        # just call some setup methods. This really needs some serial
        # loopback to fully test.
        sp = tty.SerialPort("/dev/ttyS0")
        sp.set_serial("9600 8N1")
        sp.stty("-parenb", "-parodd", "cs8", "hupcl", "-cstopb", "cread",
            "clocal", "-crtscts", "ignbrk", "-brkint", "ignpar", "-parmrk",
            "-inpck", "-istrip", "-inlcr", "-igncr", "-icrnl", "-ixon",
            "-ixoff", "-iuclc", "-ixany", "-imaxbel", "-opost", "-olcuc",
            "-ocrnl", "onlcr", "-onocr", "-onlret", "-ofill", "-ofdel", "nl0",
            "cr0", "tab0", "bs0", "vt0", "ff0", "-isig", "-icanon", "-iexten",
            "-echo", "echoe", "echok", "-echonl", "-noflsh", "-xcase",
            "-tostop", "-echoprt", "echoctl", "echoke")


if __name__ == '__main__':
    unittest.main()
