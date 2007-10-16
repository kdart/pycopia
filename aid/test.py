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

class AidTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_mapstr(self):
        TEST = aid.mapstr("some%(one)s one\nsome%(two)s three\nsome%(three)s four")
        print TEST.attributes()
        try:
            print TEST
        except ValueError:
            print "got correct error from %r" % TEST
        TEST.one = "one"
        TEST.two = "thing"
        TEST.three = "where"
        print TEST
        s = str(TEST) # makes new, substituted, string
        assert s == "someone one\nsomething three\nsomewhere four"
        print TEST.three

    def test_AttrDictWrapper(self):
        ld = {"one":1, "two":2, "three":3}
        gd = {"gbone":1, "gbtwo":2, "gbthree":3}
        lw = dictlib.AttrDictWrapper(ld)
        lw.four = gd
        print lw.one
        print lw.two
        print lw.four.gbone
        print lw.four["gbtwo"]

    def test_AttrDict(self):
        d = dictlib.AttrDict()
        d.one = "one"
        print d
        print d.get
        print d.one
        print d["one"]
        d["two"] = 2
        print d.two
        print d["two"]

    def test_UserFile(self):
        fd = UserFile.UserFile("/etc/hosts", "r")
        while 1:
            d = fd.read(1024)
            if not d:
                break
        fd.close()

    def test_timelib(self):
        mt = timelib.localtime_mutable()
        print mt
        mt.add_seconds(3600)
        print mt
        print timelib.strftime("%Y-%m-%d", timelib.weekof(timelib.time()))

        t = timelib.now()
        for d in range(1, 60):
            week = timelib.weekof(t+(d*60*60*24))
            print timelib.MutableTime(week)

        print "Local time:"
        print timelib.localtimestamp()

        p = timelib.TimespecParser()
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


if __name__ == '__main__':
    unittest.main()
