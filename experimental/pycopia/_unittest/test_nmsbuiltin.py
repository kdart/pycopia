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
Check new Builtin types

"""

import qatest

from StringIO import StringIO
import pickle


class NSMBuiltinsBaseTest(qatest.Test):
    pass

class EnumPickleTest(NSMBuiltinsBaseTest):
    "Test the creation of Enum, and its pickle-ability"
    def initialize(self):
        fo = self.fo = StringIO()
        self.pickler = pickle.Pickler(fo)
        self.unpickler = pickle.Unpickler(fo)

    def test_method(self):
        for e in Enums("ZERO", "ONE", "TWO", "THREE"):
            self.assert_passed(self.test_one(e))
        return self.passed("all enum tests passed")

    def test_one(self, orig):
        self.info("original Enum: %r" % (orig,))
        self.pickler.dump(orig)
        self.fo.seek(0)
        new = self.unpickler.load()
        self.fo.seek(0)
        self.info("Unpickled Enum: %r" % (new, ))
        assert orig == new, "original and unpickled Enum are not equal"
        assert str(orig) == str(new), "original and unpickled Enum do not have same string value"
        return self.passed("unpickled equals original")
    
    def finalize(self):
        del self.pickler
        del self.unpickler
        del self.fo


### suite ###
class NSMBuiltinsSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = NSMBuiltinsSuite(conf)

    suite.add_test(EnumPickleTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


