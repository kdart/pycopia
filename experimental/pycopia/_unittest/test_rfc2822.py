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
Unit test of rfc2822 module.

"""


import qatest

import inet.rfc2822 as rfc2822

class rfc2822Tests(qatest.Test):
    pass

class HeaderTests(rfc2822Tests):
    def test_method(self): # implicitly tests Header base class.
        s = rfc2822.Subject()
        assert str(s) == "Subject: ", "incorrect stringification."
        return self.passed()

class SubjectParse(rfc2822Tests):
    def test_method(self):
        SubString = "Subject: This is a test."
        s = rfc2822.Subject()
        s.parse(SubString)
        assert s.value == "This is a test.", "incorrect Header parse"
        return self.passed()


def get_suite(cf):
    suite = qatest.TestSuite(cf)
    suite.add_test(HeaderTests)
    suite.add_test(SubjectParse)
    return suite

def run(cf):
    suite = get_suite(cf)
    suite()

