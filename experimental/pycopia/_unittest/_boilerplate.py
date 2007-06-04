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
XXX_ENTER_TEST_DESCRIPTION

"""

import qatest

# add any other imports your test tests. The MUT? 

# A common base class for all tests in a module is useful for common helper
# methods.
class XXXBaseTest(qatest.Test):
    pass

# the actual test implementation class. There may be more than one of these.
class XXXTest(XXXBaseTest):
    # delete or override this as necessary. 
    def initialize(self):
        pass

    # where your main test goes. It may take arguments that are obtained from
    # the suite's add_test() method.
    def test_method(self, all_ok=1):
        if all_ok:
            return self.passed("all is ok.")
        else:
            return self.failed("all is NOT ok.")

    # delete or override this as necessary. 
    def finalize(self):
        pass


# A TestSuite is a collection of tests that are logically related. Most test
# modules have one. It runs all added tests in sequence when called.
class XXXSuite(qatest.TestSuite):
    # delete or override this as necessary. 
    def initialize(self):
        pass

    # delete or override this as necessary. 
    def finalize(self):
        pass


# required function - returns a XXXSuite instance, with all tests added.
def get_suite(conf):
    # create the suite with the passed-in configuration object.
    suite = XXXSuite(conf)

    # add your actual tests cases, as class objects. Any extra options given to
    # "add_test" will be passed to the "test_method" method in the test class
    # when it is run.
    suite.add_test(XXXTest, 1)
    suite.add_test(XXXTest, 0)
    # suite.add_test(AnyOtherTest)
    return suite

# Required function. Gets and runs the suite, taking a single configuration
# object. The configuration object is contstructed in the testrunner module.
def run(conf):
    suite = get_suite(conf)
    suite()


