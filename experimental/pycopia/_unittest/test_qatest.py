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
test the test framework.

"Framework, test thyself!"

"""

# $Id$

import sys

import qatest
import reports

NULLREPORT = reports.NullReport()

DO_PASSED = qatest.PASSED
DO_FAILED = qatest.FAILED
DO_ABORT = qatest.ABORT
DO_INCOMPLETE = qatest.INCOMPLETE
DO_TestIncompleteError = 100
DO_TestFailError = 101
DO_TestSuiteAbort = 102
DO_FAILASSERT = 103
DO_KeyboardInterrupt = 104

ON = True
OFF = False

class SelfTestBase(qatest.Test):
    # squelch reeporting of utility tests
    pass

class TestTest(qatest.Test):
    def test_method(self, arg):
        if arg == DO_PASSED:
            return self.passed("arg %d means passed." % (arg,))
        elif arg == DO_FAILED:
            return self.failed("arg %d means failed." % (arg,))
        elif arg == DO_ABORT:
            return self.abort("arg %d means abort." % (arg,))
        elif arg == DO_INCOMPLETE:
            return self.incomplete("arg %d means incomplete." % (arg,))
        elif arg == DO_TestIncompleteError:
            raise TestIncompleteError, "forced TestIncompleteError"
        elif arg == DO_TestFailError:
            raise TestFailError, "forced TestFailError"
        elif arg == DO_FAILASSERT:
            self.assert_equal(1, 0, "forced bad assertion.")
        elif arg == DO_KeyboardInterrupt:
            raise KeyboardInterrupt
        else:
            return self.passed("got arg %d" % (arg))

class AAETest(qatest.Test):
    def _negative(self, arg1, arg2, fudge):
        try:
            self.assert_approximately_equal(arg1, arg2, fudge)
        except TestFailError, msg:
            self.verboseinfo(msg)
            return qatest.PASSED
        else:
            self.diagnostic("%s should be within %s unit of %s" % (arg1, fudge, arg2))
            return qatest.FAILED

    def test_method(self):
        self.assert_approximately_equal(1, 1, 1)
        self.assert_approximately_equal(1.0, 1, 1)
        self.assert_approximately_equal(1, 1.0, 1)
        self.assert_approximately_equal(1, 2, 1)
        self.assert_approximately_equal(3, 1, 2)
        self.assert_approximately_equal(10, 10.1)
        self.assert_approximately_equal(10, 11, 1)
        self.assert_passed(self._negative(1, 2, 0.5))
        self.assert_passed(self._negative(1, 3, 1))
        self.assert_passed(self._negative(3, 1, 1))
        self.assert_passed(self._negative(10, 11, None)) # None == default of 5%

        return self.passed("all approx. assertions passed")

class TestInfo(qatest.Test):
    def test_method(self, msg="TestInfo message"):
        self.info(msg)
        return self.passed("no exception in info message.")

class TestVerboseInfo(qatest.Test):
    def test_method(self):
        ov = self.set_verbose(0)
        self.verboseinfo("if you see THIS then the unit test failed!")
        self.set_verbose(1)
        self.verboseinfo("This is a verboseinfo() message.")
        self.set_verbose(ov)
        return self.passed("you should see exactly one 'verboseinfo' message above.")

class TestDiagnostic(qatest.Test):
    def test_method(self, msg):
        self.diagnostic(msg)
        return self.passed("no exception in diagnostic message.")


class TestReturnValues(SelfTestBase):
    def test_method(self):
        cf = self.config
        passtest = TestTest(cf)
        rv = passtest(DO_PASSED)
        assert rv == qatest.PASSED, "did not return PASSED"
        del passtest
        failtest = TestTest(cf)
        rv = failtest(DO_FAILED)
        assert rv == qatest.FAILED, "did not return FAILED"
        del failtest
        aborttest = TestTest(cf)
        rv = aborttest(DO_INCOMPLETE)
        assert rv == qatest.INCOMPLETE, "did not return INCOMPLETE"
        del aborttest
        failaborttest = TestTest(cf)
        try:
            rv = failaborttest(DO_ABORT)
        except TestSuiteAbort:
            pass
        else:
            return self.failed("abort() did not raise TestSuiteAbort")
        del failaborttest
        return self.passed("all assertions passed")


class SuiteHandlePassed(SelfTestBase):
    def test_method(self):
        cf = self.config
        suite = TesterSuite(cf)
        suite.add_test(TestTest, DO_PASSED)
        suite()
        return suite.results()[0]

class SuiteHandleFailed(SelfTestBase):
    def test_method(self):
        cf = self.config
        suite = TesterSuite(cf)
        suite.add_test(TestTest, DO_FAILED)
        suite()
        res = suite.results()[0]
        assert res == qatest.FAILED
        return self.passed()

class SuiteHandleAbort(SelfTestBase):
    def test_method(self):
        cf = self.config
        suite = TesterSuite(cf)
        suite.add_test(TestTest, DO_ABORT)
        self.info("Should abort test suite.")
        suite()
        res = suite.results()[0]
        assert res == qatest.INCOMPLETE, "Suite test did not indicate INCOMPLETE, got %s" % (res,)
        return self.passed("Suite aborted properly")

class _TestKeyboardInterrupt(qatest.Test):
    def initialize(self):
        self.finalize_ran = 0
    def test_method(self):
        raise KeyboardInterrupt
    def finalize(self):
        self.finalize_ran = 1

##############################
### prerequisite testing #####
##############################
class _PrereqPrereqBase(qatest.Test):
    pass

class _PrereqPrereqPass(_PrereqPrereqBase):
    def test_method(self):
        return qatest.PASSED

class _PrereqPrereqFail(_PrereqPrereqBase):
    def test_method(self):
        return qatest.FAILED

class _PrereqPrereqAbort(_PrereqPrereqBase):
    def test_method(self):
        return qatest.ABORT

class _PrereqParam(qatest.Test):
    PREREQUISITES = [qatest.PreReq("TestTest", DO_PASSED)]
    def test_method(self):
        return qatest.PASSED

class _PrereqTestPassed(qatest.Test):
    PREREQUISITES = [qatest.PreReq("_PrereqPrereqPass")]
    def test_method(self):
        return qatest.PASSED

class _PrereqTestFailed(qatest.Test):
    PREREQUISITES = [qatest.PreReq("_PrereqPrereqFail")]
    def test_method(self):
        return qatest.PASSED

class _PrereqTestAborted(qatest.Test):
    PREREQUISITES = [qatest.PreReq("_PrereqPrereqAbort")]
    def test_method(self):
        return qatest.PASSED

class PrereqTest(SelfTestBase):
    def test_method(self):
        cf = self.config
        cf.test_results = []
        suite = TesterSuite(cf)
        expected = [
                qatest.PASSED,
                qatest.PASSED,
                qatest.PASSED,
                qatest.FAILED,
        #       qatest.INCOMPLETE,
                qatest.PASSED,
                qatest.PASSED,
                qatest.INCOMPLETE,
                qatest.PASSED,
        ]
        suite.add_test(TestTest, DO_PASSED)
        suite.add_test(_PrereqPrereqPass)
        suite.add_test(_PrereqParam) # depends on TestTest(DO_PASSED)
        suite.add_test(_PrereqPrereqFail) # will fail
        #suite.add_test(_PrereqPrereqAbort) # will abort
        suite.add_test(_PrereqTestPassed) # depends on _PrereqPrereqPass
        suite.add_test(_PrereqPrereqPass)
        suite.add_test(_PrereqTestFailed) # depends on _PrereqPrereqFail
        suite.add_test(_PrereqPrereqPass)
        suite()
        res = suite.results()
        assert len(res) == len(expected), "Huh? lengths don't match."
        if expected == res:
            return self.passed("Suite executed properly.")
        else:
            self.diagnostic("expected values:")
            self.diagnostic(repr(expected))
            self.diagnostic("do not equal result:")
            self.diagnostic(repr(res))
            return self.failed("some prerequisite did not match.")

##########################
### Interrupt handling ###
##########################
class TestHandleKeyboardInterrupt(qatest.Test):
    def test_method(self):
        tki = _TestKeyboardInterrupt(self.config)
        try:
            tki()
        except KeyboardInterrupt:
            pass
        assert tki.finalize_ran == 1, "finalize() not run after interrupt!"
        return self.passed("correct test interrupt handling.")


class SuiteHandleKeyboardInterrupt(SelfTestBase):
    def test_method(self):
        cf = self.config
        expected = [qatest.ABORT, None]
        suite = TesterSuite(cf)
        suite.add_test(TestTest, DO_KeyboardInterrupt)
        suite.add_test(TestTest, DO_PASSED)
        suite()
        res = suite.results()
        assert len(res) == len(expected), "did not abort?"
        assert expected == res, "%s != %s" % (expected, res)
        return self.passed("Suite aborted properly")


class TestTestSuite(SelfTestBase):
    def test_method(self):
        cf = self.config
        suite = TesterSuite(cf)
        expected = [qatest.PASSED, qatest.FAILED, qatest.INCOMPLETE, 
            qatest.INCOMPLETE, qatest.FAILED, qatest.FAILED, qatest.PASSED, qatest.PASSED]
        suite.add_test(TestTest, DO_PASSED)
        suite.add_test(TestTest, DO_FAILED)
        suite.add_test(TestTest, DO_INCOMPLETE)
        suite.add_test(TestTest, DO_TestIncompleteError)
        suite.add_test(TestTest, DO_TestFailError)
        suite.add_test(TestTest, DO_FAILASSERT)
        suite.add_test(TestInfo, "You should NOT see this message!")
        suite.add_test(TestReturnValues)
        suite()
        res = suite.results()
        assert len(res) == len(expected), "number of results does not match suite!"
        if res != expected:
            self.diagnostic("expected values:")
            self.diagnostic(repr(expected))
            self.diagnostic("do not equal result:")
            self.diagnostic(repr(res))
            return self.failed("not expected values!")
        return self.passed("got expected return values")


# utility suite that does not emit report messages
class TesterSuite(qatest.TestSuite):
    def initialize(self):
        for entry in self._tests:
            entry.inst._report = NULLREPORT
        self.report = NULLREPORT

# a nested test suite
class TestGroup(qatest.TestSuite):
    def initialize(self):
        self.info("Initialized nested test suite.")

    def finalize(self):
        self.info("Finalized nested test suite.")


# the primary test suite
class Testqatest(qatest.TestSuite):
    def initialize(self):
        self.info("Starting test suite")

def get_suite(cf):
    # test the nesting of suites
    subgroup = TestGroup(cf)
    subgroup.add_test(TestTest, DO_PASSED)
    subgroup.add_test(TestReturnValues)

    grp = TestGroup(cf)
    grp.add_test(TestReturnValues)
    grp.add_test(TestTest, DO_PASSED)
    grp.add_test(TestTest, DO_PASSED)
    grp.add_suite(subgroup)

    # the main (real) test suite. ALL of the top-level tests should pass.
    suite = Testqatest(cf)
    suite.add_test(TestInfo, "info message")
    suite.add_test(TestVerboseInfo)
    suite.add_test(TestTest, DO_PASSED)
    suite.add_test(TestReturnValues)
    suite.add_test(SuiteHandlePassed)
    suite.add_test(SuiteHandleFailed)
    suite.add_test(SuiteHandleAbort)
    suite.add_test(TestTestSuite)
    suite.add_test(PrereqTest)
    suite.add_test(TestHandleKeyboardInterrupt)
    suite.add_test(SuiteHandleKeyboardInterrupt)
    suite.add_test(AAETest)
    suite.add_suite(grp)

    return suite

def run(cf):
    suite = get_suite(cf)
    suite()

