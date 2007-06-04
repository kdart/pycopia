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
XGzip Test.

"""

import sys
import qatest

import x_gzip

class XGzipBaseTest(qatest.Test):
    pass

class ReadChunks(XGzipBaseTest):
    def test_method(self, readsize):
        chunks = []
        gz = x_gzip.open("gzipped2.txt.gz", "r")
        self.verboseinfo(gz.header)
        self.assert_equal(gz.header.name, "gzipped.txt")
        while 1:
            d = gz.read(readsize)
            if not d:
                break
            chunks.append(d)
        gz.close()
        del gz

        data = "".join(chunks)
        lines = data.split("\n")
        # got chunks, data as text, and lines. Now do some checks.
        self.assert_equal(len(data), 6378, "Should be 6378 chars, got %d" % (len(data),))
        self.assert_equal(data.count("\n"), 80, "Should be 80 lines, got %d" % (len(lines),))
        self.assert_equal(lines[40].strip(), "0:This file is compressed using gzip.")
        return self.passed("all assertions passed.")
        

class XGzipSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = XGzipSuite(conf)
    suite.add_test(ReadChunks, 512)
    suite.add_test(ReadChunks, 1024)
    suite.add_test(ReadChunks, 2048)
    suite.add_test(ReadChunks, 4096)
    suite.add_test(ReadChunks, 6377)
    suite.add_test(ReadChunks, 6378)
    suite.add_test(ReadChunks, 6379)
    suite.add_test(ReadChunks, 8192)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


