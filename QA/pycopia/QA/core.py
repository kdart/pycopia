#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
This module contains the test case and test suite classes used to control
the running of tests and provides a basic framework for automated testing.
It is the core part of automated testing.

This module defines a Test class, which is the base class for all test
case implementations. This class is not normally substantiated itself, but
a subclass is defined that defines a 'execute()' method. 

To use the test case, instantiate your class and call it with test method
parameters. You can define two hook methods in the subclass: 'initialize'
and 'finalize'.  These are run at the beginning and end of the test,
respectively.

You may also need to define dependencies. Your class definition may
contain a PREREQUISITE class-variable that is used for this. This should
be set, if required, so dependency tracking works.

All test related errors are based on the 'TestError' exception. If a test
cannot be completed for some reason you may raise a 'TestIncompleteError'
exception.

Your 'execute()' should return the value of the 'passed()' or
'failed()' method, as appropriate. You may also use assertions. The
standard Python 'assert' keyword may be used, or the assertion test
methods may be used.

Usually, a set of test cases is collected in a TestSuite object, and run
sequentially by calling the suite instance. 

"""

import sys, os

from pycopia.aid import Enum, IF
from pycopia import debugger
from pycopia import scheduler
from pycopia import timelib
from pycopia import cliutils


__all__ = ['TestError', 'TestIncompleteError', 'TestFailError',
'TestSuiteAbort', 'Test', 'PreReq', 'TestSuite', 'repr_test',
]

# exception classes that may be raised by test methods.
class TestError(AssertionError):
    """TestError() Base class of testing errors."""
    pass

class TestIncompleteError(TestError):
    """Test case disposition could not be determined."""
    pass

class TestFailError(TestError):
    """Test case failed to meet the pass criteria."""
    pass

class TestSuiteAbort(RuntimeError):
    """Entire test suite must be aborted."""
    pass


# One of the below values should be returned by execute(). The usual
# method is to return the value of the method with the same name. E.g.
# 'return self.passed()'. The Test.passed() method adds a passed message
# to the report, and returns the PASSED value for the suite to check.

# execute() passed, and the suite may continue.
PASSED = Enum(1, "PASSED")

# execute() failed, but the suite can continue. You may also raise a
# TestFailError exception.
FAILED = Enum(0, "FAILED") 

# execute() could not complete, and the pass/fail criteria could not be
# determined. but the suite may continue. You may also raise a TestIncompleteError
# exception.
INCOMPLETE = Enum(-1, "INCOMPLETE") 

# execute() could not complete, and the suite cannot continue. Raising
# TestSuiteAbort is the same.
ABORT = Enum(-2, "ABORT") 


# default report message
NO_MESSAGE = "no message"


# Cheat a little here for better user input
BRIGHTWHITE = "\x1b[37;01m"
NORMAL = "\x1b[0m"



######################################################
# abstract base class of all tests
class Test(object):
    """Base class for all test cases. The test should be as atomic as possible.
    Multiple instances of these may be run in a TestSuite object.  Be sure to
    set the PREREQUISITES class-variable in the subclass if the test has a
    prerequisite test."""
    # prerequisite tests are static, defined in the class definition.
    # They are defined by the PreReq class. The PreReq class takes a name of a
    # test case (which is the name of the Test subclass) and any arguments that
    # the test requires. A unique test case is defined by the Test class and
    # its specific arguments. The PREREQUISITES class attribute is a list of
    # PreReq objects.
    # e.g. PREREQUISITES = [PreReq("MyPrereqTest", 1)]
    PREREQUISITES = []
    INTERACTIVE = False # define to True if your test is interactive (takes user input).

    def __init__(self, config):
        self.test_name = self.__class__.__name__
        self.config = config 
        self._report = config.report 
        self._debug = config.flags.DEBUG 
        self._verbose = config.flags.VERBOSE 
        self.datapoints = [] # optionally used to collect data during test run

    def __call__(self, *args, **kw):
        # this heading displays the test name just as a PREREQUISITES entry needs.
        self._report.add_heading(repr_test(self.test_name, args, kw), 2)
        self.starttime = timelib.now()
        self.info("STARTTIME: %s" % (timelib.strftime("%a, %d %b %Y %H:%M:%S %Z", timelib.localtime(self.starttime)),))
        rv = None # in case of exception
        rv = self._initialize(rv)
        if rv is not None: # an exception happened
            return rv
        # test elapsed time does not include initializer time.
        teststarttime = timelib.now()
        # run execute
        try:
            rv = apply(self.execute, args, kw)
        except KeyboardInterrupt:
            if self._debug:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
            rv = self.incomplete("%s: aborted by user." % self.test_name)
            self._finalize(rv)
            raise
        except TestFailError, errval:
            rv = self.failed("Caught Fail exception: %s" % (errval,))
        except TestIncompleteError, errval:
            rv = self.incomplete("Caught Incomplete exception: %s" % (errval,))
        except AssertionError, errval:
            rv = self.failed("failed assertion: %s" % (errval,))
        except TestSuiteAbort:
            raise # pass this one up to suite
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                debugger.post_mortem(tb, ex, val)
                tb = None
            rv = self.failed("%s: Exception occured! (%s: %s)" % (self.test_name, ex, val))
        endtime = timelib.now()
        minutes, seconds = divmod(endtime - teststarttime, 60.0)
        hours, minutes = divmod(minutes, 60.0)
        self.info("Time elapsed: %02.0f:%02.0f:%02.2f" % (hours, minutes, seconds))
        return self._finalize(rv)

    def _initialize(self, rv):
        try:
            self.initialize()
        except:
            ex, val, tb = sys.exc_info()
            self.diagnostic("%s (%s)" % (ex, val))
            if self._debug:
                debugger.post_mortem(tb, ex, val)
            rv = self.abort("Test initialization failed!")
        return rv

    # run user's finalize() and catch exceptions. If an exception occurs
    # in the finalize() method (which is supposed to clean up from the
    # test and leave the DUT in the same condition as when it was entered)
    # then alter the return value to abort(). 
    def _finalize(self, rv):
        try:
            self.finalize()
        except:
            ex, val, tb = sys.exc_info()
            self.diagnostic("%s (%s)" % (ex, val))
            if self._debug:
                debugger.post_mortem(tb, ex, val)
            rv = self.abort("Test finalize failed!")
        return rv

    def logfilename(self, ext="log"):
        """Return a standardized log file name with a timestamp that should be
        unique enough to not clash with other tests, and also able to correlate
        it later to the test report via the time stamp."""
        return "%s-%s.%s" % (self.test_name, timelib.strftime("%Y%m%d%H%M%S", timelib.localtime(self.starttime)), ext)

    # Tests expose the scheduler interface also
    def sleep(self, secs):
        """Sleep method simply sleeps for specified number of seconds."""
        return scheduler.sleep(secs)

    def schedule(self, delay, cb):
        """Schedule a callback to run 'delay' seconds in the future."""
        return scheduler.add(delay, callback=cb)

    def timed(self, function, args=(), kwargs={}, timeout=30):
        """Call a method with a failsafe timeout value."""
        sched = scheduler.get_scheduler()
        return sched.timeout(function, args, kwargs, timeout)

    def timedio(self, function, args=(), kwargs={}, timeout=30):
        """Call a method with a failsafe timeout value."""
        sched = scheduler.get_scheduler()
        return sched.iotimeout(function, args, kwargs, timeout)

    def run_subtest(self, _testclass, *args, **kwargs):
        """Runs a test test class with the given arguments. """
        inst = _testclass(self.config)
        return apply(inst, args, kwargs)

    def debug(self):
        """Enter the debugger... at will."""
        debugger.set_trace(2)

    def set_debug(self, onoff=1):
        """Turn on or off the DEBUG flag."""
        ov = self._debug
        self._debug = self.config.flags.DEBUG = onoff
        return ov

    def set_verbose(self, onoff=1):
        """Turn on or off the VERBOSE flag."""
        ov = self._verbose
        self._verbose = self.config.flags.VERBOSE = onoff
        return ov

    def prerequisites(self):
        "Get the list of prerequisites, which could be empty."
        return getattr(self, "PREREQUISITES", [])

    # the overrideable methods
    def initialize(self):
        "Hook method to initialize a test. Override if necessary."
        pass

    def finalize(self):
        "Hook method when finalizing a test. Override if necessary."
        pass

    def execute(self, *args, **kw):
        """Overrided this method in a subclass to implement a specific test."""
        return self.incomplete('you must define a method named "execute" in your subclass.')

    # result reporting methods
    def passed(self, msg=NO_MESSAGE):
        """Call this and return if the execute() passed. If part of
        a suite, subsequent tests may continue."""
        self._report.passed(msg)
        return PASSED

    def failed(self, msg=NO_MESSAGE):
        """Call this and return if the execute() failed, but can continue
        the next test."""
        self._report.failed(msg)
        return FAILED

    def incomplete(self, msg=NO_MESSAGE):
        """Test could not complete."""
        self._report.incomplete(msg)
        return INCOMPLETE

    def abort(self, msg=NO_MESSAGE):
        """Some drastic error occurred, or some condition is not met, and the suite cannot continue."""
        self._report.abort(msg)
        raise TestSuiteAbort

    def info(self, msg):
        """Call this to record non-critical information in the report object."""
        self._report.info(msg)

    def verboseinfo(self, msg):
        """Call this to record really non-critical information in the report
        object that is only emitted when the VERBOSE flag is enabled in the
        configuration."""
        if self._verbose:
            self._report.info(msg)

    def diagnostic(self, msg):
        """Call this one or more times if a failed condition is detected, and
        you want to record in the report some pertinent diagnostic information.
        Then return with a FAIL message."""
        self._report.diagnostic(msg)

    def datapoint(self, val):
        """Adds data to the list of collected data.  A time stamp is added."""
        self.datapoints.extend((timelib.now(), val))
    
    def get_datapoints(self):
        "Accessor method to return copy of datapoints list."
        return self.datapoints[:]

    # assertion methods make it convenient to check conditions.
    def assert_passed(self, arg, msg=None):
        if arg != PASSED:
            raise TestFailError, msg or "Did not pass test."

    def assert_failed(self, arg, msg=None):
        if arg != FAILED:
            raise TestFailError, msg or "Did not pass test."

    def assert_equal(self, arg1, arg2, msg=None):
        if arg1 != arg2:
            raise TestFailError, msg or "%s != %s" % (arg1, arg2)

    def assert_not_equal(self, arg1, arg2, msg=None):
        if arg1 == arg2:
            raise TestFailError, msg or "%s == %s" % (arg1, arg2)
    assert_notequal = assert_not_equal # alias

    def assert_true(self, arg, msg=None):
        if not arg:
            raise TestFailError, msg or "%s not true." % (arg,)

    def assert_false(self, arg, msg=None):
        if arg:
            raise TestFailError, msg or "%s not false." % (arg,)

    def assert_approximately_equal(self, arg1, arg2, fudge=None, msg=None):
        if fudge is None:
            fudge = arg1*0.05 # default 5% of arg1
        if abs(arg1-arg2) > fudge:
            raise TestFailError, msg or "%s and %s not within %s units of each other." % (arg1, arg2, fudge)

    # some logical aliases
    fail_if_equal = assert_not_equal
    fail_if_not_equal = assert_equal
    assert_not_true = assert_false
    assert_not_false = assert_true

    # user input methods. May only be used for tests flagged as INTERACTIVE.
    def user_input(self, prompt=None):
        if self.INTERACTIVE:
            return raw_input(BRIGHTWHITE+prompt+NORMAL)
        else:
            raise TestIncompleteError, "user input in non-interactive test."

    def choose(self, somelist, defidx=0):
        if self.INTERACTIVE:
            return cliutils.choose(somelist, defidx)
        else:
            raise TestIncompleteError, "user input in non-interactive test."
    
    def get_text(self, msg=None):
        if self.INTERACTIVE:
            return cliutils.get_text("> ", msg)
        else:
            raise TestIncompleteError, "user input in non-interactive test."

    def get_value(self, prompt, default=None):
        if self.INTERACTIVE:
            return cliutils.get_input(prompt, default)
        else:
            raise TestIncompleteError, "user input in non-interactive test."

    def yes_no(self, prompt, default=True):
        if self.INTERACTIVE:
            yesno = cliutils.get_input(prompt, IF(default, "Y", "N"))
            return yesno.upper().startswith("Y")
        else:
            raise TestIncompleteError, "user input in non-interactive test."



# --------------------


class PreReq(object):
    """A holder for test prerequiste."""
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.name, self.args, self.kwargs)

    def __str__(self):
        return repr_test(self.name, self.args, self.kwargs)


# holds an instance of a Test class and the parameters it will be called with.
# This actually calls the test, and stores the result value for later summary.
# It also supports pre-requisite matching.
class _TestEntry(object):
    def __init__(self, inst, args=None, kwargs=None):
        self.inst = inst
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.result = None

    def __call__(self):
        try:
            self.result = apply(self.inst, self.args, self.kwargs)
        except KeyboardInterrupt:
            self.result = ABORT
            raise
        return self.result

    def __eq__(self, other):
        return self.inst == other.inst

    def matches(self, name, args, kwargs):
        return (name, args, kwargs) == (self.inst.test_name, self.args, self.kwargs)

    def match_prerequisite(self, prereq):
        "Does this test match the specified prerequisite?"
        return (self.inst.test_name, self.args, self.kwargs) == (prereq.name, prereq.args, prereq.kwargs)

    def get_result(self):
        return self.result

    def prerequisites(self):
        return self.inst.prerequisites()

    def abort(self):
        self.result = self.inst.abort("Abort forced by suite runner.")
        return self.result

    def was_aborted(self):
        return self.result == ABORT

    def name(self):
        return self.inst.test_name

    def get_values(self):
        return self.inst.test_name, self.args, self.kwargs, self.result

    def __repr__(self):
        return repr_test(self.inst.test_name, self.args, self.kwargs)

class _SuiteEntry(_TestEntry):
    def get_result(self):
        # self.result is a list in this case
        self.results = self.inst.results()
        for res in self.results:
               if res != PASSED:
                   return res
        return PASSED

def repr_test(name, args, kwargs):
    args_s = IF(args, 
        IF(kwargs, "%s, ", "%s") % ", ".join(map(repr, args)),
        "")
    kws = ", ".join(map(lambda it: "%s=%r" % (it[0], it[1]), kwargs.items()))
    return "%s()(%s%s)" % (name, args_s, kws)


class TestSuite(object):
    """TestSuite(config)
A TestSuite contains a set of test cases (subclasses of Test class objects)
that are run sequentially, in the order added. It monitors abort status of each
test, and aborts the suite if required. 

To run it, create a TestSuite object (or a subclass with some methods
overridden), add tests with the 'add_test()' method, and then call the
instance. The 'initialize()' method will be run with the arguments given when
called.

    """
    def __init__(self, cf, nested=0):
        self.config = cf
        self.report = cf.report
        self._debug = cf.flags.DEBUG
        self._verbose = cf.flags.VERBOSE
        self._tests = []
        self._nested = nested
        self.suite_name = self.__class__.__name__
        cl = self.__class__
        self.test_name = "%s.%s" % (cl.__module__, cl.__name__)

    
    def __iter__(self):
        return iter(self._tests)

    def set_config(self, cf):
        self.config = cf

    def add_test(self, _testclass, *args, **kw):
        """add_test(Test, [args], [kwargs])
Appends a test object in this suite. The test's execute() will be called
with the arguments supplied here. If the test case has a prerequisite defined
it is checked for existence in the suite, and an exception is raised if it is
not found."""
        if _testclass.INTERACTIVE and self.config.flags.NOINTERACTIVE:
            print >>sys.stderr, "%s is an interactive test and NOINTERACTIVE is set. Skipping." % (_testclass.__name__,)
            return
        testinstance = _testclass(self.config)
        entry = _TestEntry(testinstance, args, kw)
        self._verify_new(entry)
        self._tests.append(entry)

    def _verify_new(self, entry):
        prereqs = entry.prerequisites()
        count = 0
        for prereq in entry.prerequisites():
            for te in self._tests:
                if te.match_prerequisite(prereq):
                    count += 1
        if count < len(prereqs):
            raise TestSuiteAbort, "unable to add test case %s, prerequisite not already added!" % (entry, )

    def add_suite(self, suite, *args, **kw):
        """add_suite(TestSuite, [args], [kwargs])
Appends an embedded test suite in this suite. """
        if type(suite) is type(Test): # class type
            suite = suite(self.config, 1)
        else:
            suite.config = self.config
            suite._nested = 1
        self._tests.append(_SuiteEntry(suite, args, kw))
        suite.test_name = "%s%s" % (suite.__class__.__name__,len(self._tests)-1)
        return suite

    def add(self, klass, *args, **kw):
        """add(classobj, [args], [kwargs])
Most general method to add test case classes or other test suites."""
        if issubclass(klass, Test):
            self.add_test(klass, *args, **kwargs)
        elif issubclass(klass, TestSuite):
            self.add_suite(klass, *args, **kwargs)
        else:
            raise ValueError, "TestSuite.add: invalid class type."

    def get_tests(self):
        """Return a list of the test objects currrently in this suite."""
        return self._tests[:]

    def get_test(self, name, *args, **kwargs):
        for entry in self._tests:
            if entry.matches(name, args, kwargs):
                return entry
        return None

    def info(self, msg):
        """info(msg)
Put in informational message in the test report."""
        self.report.info(msg)

    def prerequisites(self):
        """Get the list of prerequisites, which could be empty. Primarily
used by nested suites."""
        return getattr(self, "PREREQISITES", [])

    # this is the primary way to invoke a suite of tests. call the instance.
    # Any supplied parameters are passed onto the suite's initialize()
    # method.
    def __call__(self, *args, **kwargs):
        try:
            self._initialize(args, kwargs)
        except TestSuiteAbort, rv:
            self._finalize()
            return
        self.run_tests()
        self._finalize()
        return PASSED # suite ran without exception...

    def _initialize(self, args, kwargs):
        self.report.add_heading("Test suite: %s" % self.__class__.__name__, 1)
        # initialize the suite
        try:
            rv = self.initialize(*args, **kwargs)
        except KeyboardInterrupt:
            self.info("Suite aborted by user in initialize().")
            raise TestSuiteAbort
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
            self.info("Suite failed to initialize: %s (%s)" % (ex, val))
            raise TestSuiteAbort, val
        # run all the tests

    # verify any prerequisites are met at run time. Note that this
    # currently only checks this particular suite.
    def check_prerequisites(self, currententry, upto):
        for prereq in currententry.prerequisites():
            for entry in self._tests[:upto]:
                if entry.match_prerequisite(prereq):
                    if entry.result == PASSED:
                        continue
                    else:
                        self.report.add_heading(repr(currententry), 2)
                        self.info("WARNING: prerequisite of %s did not pass." % (currententry,))
                        self.info("%s: %s" % (prereq, entry.result))
                        currententry.result = INCOMPLETE
                        return False
        return True # no prerequisite

    def run_tests(self):
        #for test, testargs, testkwargs in self._tests:
        for i, entry in enumerate(self._tests):
            if not self.check_prerequisites(entry, i):
                continue
            try:
                self.config.logfile.note("%s: %r" % (timelib.localtimestamp(), entry))
                rv = entry()
            except KeyboardInterrupt:
                self.info("Test suite aborted by user.")
                if self._nested:
                    raise TestSuiteAbort, "aborted by user"
                else:
                    break
            except TestSuiteAbort, err:
                self.info("Suite aborted by test %s (%s)." % (entry.name(), err))
                entry.result = INCOMPLETE
                rv = ABORT
            # this should only happen with incorrectly written execute().
            if rv is None:
                self.report.diagnostic("warning: test returned None, assuming failed. "
                                      "Please fix the %s.execute()" % (entry.name()))
                rv = FAILED
            # keep return value in results
            # check for abort condition and abort if so
            if rv == ABORT:
                break

    def _finalize(self):
        # finalize the suite
        try:
            self.finalize()
        except KeyboardInterrupt:
            if self._nested:
                raise TestSuiteAbort, "Suite '%s' aborted by user in finalize()." % (self.suite_name,)
            else:
                self.info("Suite aborted by user in finalize().")
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                print
                debugger.post_mortem(tb, ex, val)
            self.info("Suite failed to finalize: %s (%s)" % (ex, val))
            if self._nested:
                raise TestSuiteAbort, "subordinate suite '%s' failed to finalize." % (self.test_name,)
        self._report_summary()

    def _report_summary(self):
        self.report.add_heading(
                    "Summarized results for %s." % self.__class__.__name__, 3)
        entries = filter(lambda te: te.result is not None, self._tests)
        self.report.add_summary(entries)
        # check and report suite level result
        result = PASSED
        for entry in self._tests:
            if entry.result in (FAILED, INCOMPLETE, ABORT):
                result = FAILED
                break
        self.result = result
        resultmsg = "Aggregate result for %r." % (self.test_name,)
        if not self._nested:
            if result == PASSED:
                self.report.passed(resultmsg)
            elif result == FAILED:
                self.report.failed(resultmsg)

    def results(self):
        return map(lambda t: t.get_result(), self._tests)

    def __str__(self):
        s = ["Tests in suite:"]
        s.extend(map(str, self._tests))
        return "\n".join(s)

    ### overrideable interface.
    def initialize(self, *args):
        """Override this if you need to do some initialization just before the
suite is run. """ 
        pass

    def finalize(self, *args):
        """Override this if you need to do some clean-up after the suite is run."""
        pass



