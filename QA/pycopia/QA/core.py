#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# LICENSE: LGPL

# Copied from Pycopia test automation framework, and modified for Google Gtest.
# Copied from Gtest, and modified for powerdroid test automation framework.
# Copied from powerdroid back into Pycopia test automation framework.


from __future__ import print_function

"""Provides base classes for test cases and suites.

This module defines a Test class, which is the base class for all test case
implementations. This class is not substantiated itself, but a subclass is
defined that overrides the `execute` method.

Your `execute` should return the value that the `passed` or
`failed` methods return, as appropriate.

All test related errors are based on the `TestError` exception. You may
also use the built-in `assert` statement. There are also various assertion
methods you may use. If a test cannot be completed for some reason you may
also raise a 'TestIncompleteError' exception.

Usually, a set of test cases is collected in a TestSuite object, and run
sequentially by calling the suite instance.

"""

__author__ = 'keith@kdart.com (Keith Dart)'


import sys
import os

from pycopia import scheduler
from pycopia import timelib
from pycopia import debugger
from pycopia import UserFile
from pycopia import dictlib
from pycopia import module
from pycopia import methods
from pycopia.QA import constants
from pycopia.db.config import ConfigError


# exception classes that may be raised by test methods.
class TestError(AssertionError):
    """TestError() Base class of testing errors.

    This is based on AssertionError so the same assertion catcher can be
    used to indicate test failure.
    """

class TestFailError(TestError):
    """Test case failed to meet the pass criteria."""

class TestIncompleteError(Exception):
    """Test case disposition could not be determined."""

class TestSuiteAbort(Exception):
    """Entire test suite must be aborted."""

class TestPrerequisiteError(Exception):
    """Error in prerequisite calculation."""


class TestResult(object):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return "Result: %s" % self._value

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._value)

    def __nonzero__(self):
        return self._value == constants.PASSED

    def __int__(self):
        return int(self._value)

    def is_passed(self):
        return self._value == constants.PASSED

    def not_passed(self):
            return self._value in (constants.FAILED, constants.EXPECTED_FAIL,
                    constants.INCOMPLETE, constants.ABORT)

    def is_failed(self):
        return self._value == constants.FAILED

    def is_incomplete(self):
        return self._value == constants.INCOMPLETE


class TestOptions(object):
    """A descriptor that forces OPTIONS to be class attributes that are not
    overridable by instances.
    """
    def __init__(self, initdict):
        # Default option value is empty iterable (evaluates false).
        self.OPTIONS = dictlib.AttrDictDefault(initdict, default=())

    def __get__(self, instance, owner):
        return self.OPTIONS

    # This is here to make instances not able to override options, but does
    # nothing else. Attempts to set testinstance.OPTIONS are simply ignored.
    def __set__(self, instance, value):
        pass


def insert_options(klass, **kwargs):
    if type(klass) is type and issubclass(klass, Test):
        if not klass.__dict__.has_key("OPTIONS"):
            klass.OPTIONS = TestOptions(kwargs)
    else:
        raise ValueError("Need Test class.")


class Test(object):
    """Base class for all test cases.

    Subclass this to define a new test. The test should be as atomic as
    possible. A Test may be combined with other tests and may have
    dependencies (defined by the database).

    May send any of the following messages to the report object:
        TESTARGUMENTS     : string representation of supplied arguments.
        STARTTIME         : timestamp indicating when test was started.
        ENDTIME           : timestamp indicating when test ended.
        BUILD             : string indicating a build that was tested against
        add_heading       : Section heading.
        passed            : When test passed.
        failed            : When test failed.
        incomplete        : When test was not able to complete.
        diagnostic        : Add useful diagnostic information when a test fails.
        abort             : Abort suite, provides the reason.
        info              : Informational and progress messages.
    """
    # class level attributes that may be overridden in subclasses, or reset by test
    # runner from external information (database).

    OPTIONS = TestOptions({})
    PREREQUISITES = []

    def __init__(self, config):
        cl = self.__class__
        self.test_name = "%s.%s" % (cl.__module__, cl.__name__)
        self.config = config
        self._report = config.report
        self._debug = config.flags.DEBUG
        self._verbose = config.flags.VERBOSE

    @classmethod
    def set_test_options(cls):
        insert_options(cls)
        opts = cls.OPTIONS
        pl = []
        for prereq in cls.PREREQUISITES:
            if isinstance(prereq, basestring):
                pl.append(PreReq(prereq))
            elif type(prereq) is tuple:
                pl.append(PreReq(*prereq))
            else:
                raise ValueError("Bad prerequisite value.")
        opts.prerequisites = pl
        opts.bugid = None

    def __call__(self, *args, **kwargs):
        """Invoke the test.

        The test is "kicked-off" by calling this. Any arguments are passed to
        the test implementation (`execute` method).
        """
        self.config.register_testcase(self.test_name)
        self._report.add_heading(self.test_name, 2)
        if args or kwargs:
            self._report.add_message("TESTARGUMENTS", repr_args(args, kwargs), 2)
        self.starttime = timelib.now() # saved starttime in case initializer
                                                                     # needs to create the log file.
        self._initialize()
        # test elapsed time does not include initializer time.
        teststarttime = timelib.now()
        # run the execute() method and check for exceptions.
        try:
            rv = self.execute(*args, **kwargs)
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
            rv = self.incomplete("Caught incomplete exception: %s" % (errval,))
        # Test asserts and validation errors are based on this.
        except AssertionError as errval:
            rv = self.failed("failed assertion: %s" % (errval,))
        except TestSuiteAbort:
            self.config.register_testcase(None)
            raise # pass this one up to suite
        except debugger.DebuggerQuit: # set_trace "leaks" BdbQuit
            rv = self.incomplete("%s: Debugger exit." % (self.test_name, ))
        except ConfigError as cerr:
            rv = self.incomplete("Configuration error: {}".format(cerr))
            self.config.register_testcase(None)
            if self._debug:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
                tb = None
            raise TestSuiteAbort(cerr)
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                debugger.post_mortem(tb, ex, val)
                tb = None
            rv = self.incomplete("%s: Exception: (%s: %s)" % (self.test_name, ex, val))
        endtime = timelib.now()
        self.config.register_testcase(None)
        self._report.add_message("STARTTIME", teststarttime, 2)
        self._report.add_message("ENDTIME", endtime, 2)
        minutes, seconds = divmod(endtime - teststarttime, 60.0)
        hours, minutes = divmod(minutes, 60.0)
        self.info("Time elapsed: %02.0f:%02.0f:%02.2f" % (hours, minutes, seconds))
        return self._finalize(rv)

    def _initialize(self):
        """initialize phase handler.

        Run user-defined `initialize()` and catch exceptions. If an exception
        occurs in the `initialize()` method (which establishes the
        pre-conditions for a test) then alter the return value to abort()
        which will abort the suite. Invokes the debugger if the debug flag is
        set. If debug flag is not set then emit a diagnostic message to the
        report.
        """
        try:
            self.initialize()
        except:
            ex, val, tb = sys.exc_info()
            self.diagnostic("%s (%s)" % (ex, val))
            if self._debug:
                debugger.post_mortem(tb, ex, val)
            self.abort("Test initialization failed!")

    def _finalize(self, rv):
        """
        Run user-defined `finalize()` and catch exceptions. If an exception
        occurs in the finalize() method (which is supposed to clean up from
        the test and leave the UUT in the same condition as when it was
        entered) then alter the return value to abort() which will abort the
        suite. Invokes the debugger if the debug flag is set.
        """
        try:
            self.finalize(rv)
        except:
            ex, val, tb = sys.exc_info()
            self.diagnostic("%s (%s)" % (ex, val))
            if self._debug:
                debugger.post_mortem(tb, ex, val)
            self.abort("Test finalize failed!")
        return rv

    # utility methods - methods that are common to nearly all tests.

    def get_start_timestamp(self):
        return timelib.strftime("%m%d%H%M%S", timelib.localtime(self.starttime))

    def get_filename(self, basename=None, ext="log"):
        """Create a log file name.

        Return a standardized log file name with a timestamp that should be
        unique enough to not clash with other tests, and also able to correlate
        it later to the test report via the time stamp. The path points to the
        resultsdir location.
        """
        filename = "%s-%s.%s" % (basename or self.test_name.replace(".", "_"),
                self.get_start_timestamp(), ext)
        return os.path.join(self.config.resultsdir, filename)

    def get_file(self, basename=None, ext="log", mode="a+"):
        """Return a file object that you can write to in the results location."""
        fname = self.get_filename(basename, ext)
        return UserFile.UserFile(fname, mode)

    def sleep(self, Nsecs):
        """Sleep for N seconds.

        Sleep method simply sleeps for specified number of seconds.
        """
        return scheduler.sleep(Nsecs)

    def schedule(self, delay, cb):
        """Callback scheduler.

        Schedule a function to run 'delay' seconds in the future.
        """
        return scheduler.add(delay, callback=cb)

    def timed(self, function, args=(), kwargs={}, timeout=30):
        """Run a function with a failsafe timer.

        Call the provided function with a failsafe timeout value. The function
        will be interrupted if it takes longer than `timeout` seconds.
        """
        sched = scheduler.get_scheduler()
        return sched.timeout(function, args, kwargs, timeout)

    def timedio(self, function, args=(), kwargs={}, timeout=30):
        """Run a function that may block on I/O with a failsafe timer.

        Call the provided function with a failsafe timeout value. The function
        will be interrupted if it takes longer than `timeout` seconds. The
        method should be one that blocks on I/O.
        """
        sched = scheduler.get_scheduler()
        return sched.iotimeout(function, args, kwargs, timeout)

    def run_subtest(self, _testclass, *args, **kwargs):
        """Invoke another Test class in the same environment as this one.

        Runs another Test subclass with the given arguments passed to the
        `execute()`.

        The report object is overridden with A NullReport by
        default. Therefore you won't see output from subtests. If you want to
        see subtest output in the report give the verbose option to the test runner.
        """
        orig = self.config.get_report()
        if not self._verbose:
            # If verbose mode then use original report, otherwise temporarily
            # substitute NullReport.
            from pycopia import reports
            nr = reports.get_report(("NullReport",))
            self.config.set_report(nr)
        inst = _testclass(self.config)
        try:
            return inst(*args, **kwargs)
        finally:
            self.config.set_report(orig)

    def run_command(self, cmdline, env=None, timeout=None, logfile=None):
        """Run an external command.

        This method will block until the command returns. An optional timeout
        may be supplied to prevent hanging forever.

        Arguments::

            A string that is the command line to be run.
            A (optional) dictionary containing the environment variables.
            An (optional) timeout value that will forcibly return if the call
                takes longer than the timeout value.

        Returns::

           A tuple of ExitStatus object and stdout/stderr (string) of the program.
        """
        from pycopia import proctools
        p = proctools.spawnpipe(cmdline, logfile=logfile, env=env)
        try:
            if timeout:
                sched = scheduler.get_scheduler()
                text = sched.iotimeout(p.read, timeout=timeout)
            else:
                text = p.read()
        finally:
            p.wait()
            p.close()
        return p.exitstatus, text

    def debug(self):
        """Enter The Debugger (starring Bruce Li).

        Forceably enter the dubugger. Win the prize, escape with your life.
        Useful when developing tests.
        """
        debugger.set_trace(start=2)

    # runtime flag control
    def set_debug(self, onoff=1):
        """Turn on or off the DEBUG flag.

        Set the debug flag from a test method. Useful for setting debug flag
        only around questionable code blocks during test development.

        Args:
            onoff: flag (boolean) to set the debug state on or off.
        """
        ov = self._debug
        self._debug = self.config.flags.DEBUG = onoff
        return ov

    def set_verbose(self, level=1):
        """Turn on or off the VERBOSE flag.

        Make reports more, or less, verbose at run time.
        """
        ov = self._verbose
        self._verbose = self.config.flags.VERBOSE = level
        return ov

    # for checking verbosity in tests.
    verbose = property(lambda s: s._verbose, set_verbose)

    def _get_prerequisites(self):
        """Get the list of prerequisites.

        Returns current list of prerequisite tests, which could be empty.
        """
        return self.OPTIONS.prerequisites

    prerequisites = property(_get_prerequisites)

    ### the overrideable methods follow ###
    def initialize(self):
        """Hook method to initialize a test.

        Override if necessary. Establishes the pre-conditions of the test.
        """
        pass

    def finalize(self, result):
        """Hook method when finalizing a test.

        Override if necessary. Used to clean up any state in UUT.
        """
        pass

    def execute(self, *args, **kw):
        """The primary test method.

        Overrided this method in a subclass to implement a specific test. All
        primary test logic and control should go here.
        """
        return self.incomplete(
                'you must define a method named "execute" in your subclass.')

    # result reporting methods
    def passed(self, msg=constants.NO_MESSAGE):
        """Call this and return if the execute() passed.

        If your execute determined that the test passed, call this.
        In a execute, the pattern is: `return self.passed('message')`.
        """
        self._report.passed(msg, 2)
        return TestResult(constants.PASSED)

    def failed(self, msg=constants.NO_MESSAGE):
        """Call this and return if the execute() failed.

        Call this if your test logic determines a failure. Only call this if
        your test implementation in the execute is positively sure that it
        does not meet the criteria. Other kinds of errors should return
        `incomplete()`.

        In the execute method, the pattern is: `return self.failed('message')`.
        """
        if self.OPTIONS.bugid:
            self._report.diagnostic(
                            "This failure was expected. see bug: %s." % (self.OPTIONS.bugid,), 2)
            self._report.expectedfail(msg, 2)
            return TestResult(constants.EXPECTED_FAIL)
        else:
            self._report.failed(msg, 2)
            return TestResult(constants.FAILED)

    def expectedfail(self, msg=constants.NO_MESSAGE):
        """Call this and return if the execute() failed but that was expected.

        This is used primarily for exploratory testing where you may have a
        sequence of parameterized tests where some are expected to fail past a
        certain threshold. In other words, the test fails because the
        parameters are out of spec.

        In the execute method, the pattern is: `return self.expectedfail('message')`.
        """
        self._report.expectedfail(msg, 2)
        return TestResult(constants.EXPECTED_FAIL)

    def incomplete(self, msg=constants.NO_MESSAGE):
        """Test could not complete.

        Call this and return if your test implementation determines that the
        test cannot be completed for whatever reason.
        In a execute, the pattern is: `return self.incomplete('message')`.
        """
        self._report.incomplete(msg, 2)
        return TestResult(constants.INCOMPLETE)

    def abort(self, msg=constants.NO_MESSAGE):
        """Abort the test suite.

        Some drastic error occurred, or some condition is not met, and the
        suite cannot continue. Raises the TestSuiteAbort exception.
        """
        self._report.abort(msg, 2)
        raise TestSuiteAbort(msg)

    def info(self, msg, level=0):
        """Informational messages for the report.

        Record non-critical information in the report object.
        The message is not recorded if the given level is greater than the current verbosity level.
        """
        if level <= self._verbose:
            self._report.info(msg, 2)

    def diagnostic(self, msg):
        """Emit diagnostic message to report.

        Call this one or more times if a failed condition is detected, and you
        want to record in the report some pertinent diagnostic information.
        The diagnostic information is typically some ephemeral state of the
        UUT you want to record.
        """
        self._report.diagnostic(msg, 2)

    def manual(self):
        """Perform a purely manual test according to the instructions in the document string."""
        UI = self.config.UI
        UI.Print(self.test_name)
        UI.write(self.__class__.__doc__)
        UI.Print("\nPlease perform this test according to the instructions above.")
        completed = UI.yes_no("%IWas it completed%N?")
        if completed:
            passed = UI.yes_no("Did it pass?")
            msg = UI.user_input("%gComments%N? " if passed else "%rReason%N? ")
            if passed:
                return self.passed("OK, user reported passed. " + msg)
            else:
                if msg:
                    self.diagnostic(msg)
                return self.failed("User reported failure.")
        else:
            msg = UI.user_input("%YReason%N? ")
            return self.incomplete("Could not perform test. " + msg)

    def report_build(self, buildstring):
        """Report any build information. Usually a version or build number.

        The buildstring parameter must match the following pattern::

            <projectname>[ .:]<major>.<minor>.<subminor>.<build>
        """
        self._report.add_message("BUILD", buildstring, 1)

    # assertion methods make it convenient to check conditions. These names
    # match those in the standard `unittest` module for the benefit of those
    # people using that module.
    def assertPassed(self, arg, msg=None):
        """Assert a sub-test run by the `run_subtest()` method passed.

        Used when invoking test objects as a unit.
        """
        if int(arg) != constants.PASSED:
            raise TestFailError, msg or "Did not pass test."

    def assertFailed(self, arg, msg=None):
        """Assert a sub-test run by the `run_subtest()` method failed.

        Useful for "negative" tests.
        """
        if int(arg) not in (constants.FAILED, constants.EXPECTED_FAIL):
            raise TestFailError, msg or "Did not pass test."

    def assertEqual(self, arg1, arg2, msg=None):
        """Asserts that the arguments are equal,

        Raises TestFailError if arguments are not equal. An optional message
        may be included that overrides the default message.
        """
        if arg1 != arg2:
            raise TestFailError, msg or "%s != %s" % (arg1, arg2)

    def assertNotEqual(self, arg1, arg2, msg=None):
        """Asserts that the arguments are not equal,

        Raises TestFailError if arguments are equal. An optional message
        may be included that overrides the default message.
        """
        if arg1 == arg2:
            raise TestFailError, msg or "%s == %s" % (arg1, arg2)

    def assertGreaterThan(self, arg1, arg2, msg=None):
        """Asserts that the first argument is greater than the second
        argument.
        """
        if not (arg1 > arg2):
            raise TestFailError, msg or "%s <= %s" % (arg1, arg2)

    def assertGreaterThanOrEqual(self, arg1, arg2, msg=None):
        """Asserts that the first argument is greater or equal to the second
        argument.
        """
        if not (arg1 >= arg2):
            raise TestFailError, msg or "%s < %s" % (arg1, arg2)

    def assertLessThan(self, arg1, arg2, msg=None):
        """Asserts that the first argument is less than the second
        argument.
        """
        if not (arg1 < arg2):
            raise TestFailError, msg or "%s >= %s" % (arg1, arg2)

    def assertLessThanOrEqual(self, arg1, arg2, msg=None):
        """Asserts that the first argument is less than or equal to the second
        argument.
        """
        if not (arg1 <= arg2):
            raise TestFailError, msg or "%s > %s" % (arg1, arg2)

    def assertTrue(self, arg, msg=None):
        """Asserts that the argument evaluates to True by Python.

        Raises TestFailError if argument is not True according to Python truth
        testing rules.
        """
        if not arg:
            raise TestFailError, msg or "%s not true." % (arg,)

    failUnless = assertTrue

    def assertFalse(self, arg, msg=None):
        """Asserts that the argument evaluates to False by Python.

        Raises TestFailError if argument is not False according to Python truth
        testing rules.
        """
        if arg:
            raise TestFailError, msg or "%s not false." % (arg,)

    def assertApproximatelyEqual(self, arg1, arg2, fudge=None, msg=None):
        """Asserts that the numeric arguments are approximately equal.

        Raises TestFailError if the second argument is outside a tolerance
        range (defined by the "fudge factor").    The default is 5% of the first
        argument.
        """
        if fudge is None:
            fudge = arg1*0.05
        if abs(arg1-arg2) > fudge:
            raise TestFailError, \
                msg or "%s and %s not within %s units of each other." % \
                        (arg1, arg2, fudge)

    def assertRaises(self, exception, method, args=None, kwargs=None, msg=None):
        """Assert that a method and the given args will raise the given
        exception.

        Args:
            exception: The exception class the method should raise.
            method:    the method to call with the given arguments.
            args: a tuple of positional arguments.
            kwargs: a dictionary of keyword arguments
            msg: optional message string to be used if assertion fails.
        """
        args = args or ()
        kwargs = kwargs or {}
        try:
            rv = method(*args, **kwargs)
        except exception:
            return
        # it might raise another exception, which is marked INCOMPLETE
        raise TestFailError, msg or "%r did not raise %r." % (method, exception)

    # some logical aliases
    failIfEqual = assertNotEqual
    failIfNotEqual = assertEqual
    assertNotTrue = assertFalse
    assertNotFalse = assertTrue
    failUnlessRaises = assertRaises

    # data storage
    def save_text(self, text, filename=None):
        """Save some text into a file in the results location.

        This may be called multiple times and the file will be appended to.

        Arguments::

            text:  A blob of text as a string.
            filename:  the base name of the file to write. Default is test name plus timestamp.
        """
        if filename is None:
            filename = self.get_filename("saved", "txt")
        fo = UserFile.UserFile(filename, "a")
        try:
            fo.write(str(text))
        finally:
            fo.close()

    @classmethod
    def open_data_file(cls, fname):
        """Open a data file located in the same directory as the test case
        implmentation.

        Return the file object (actually a UserFile object). Make sure you
        close it.
        """
        fullname = os.path.join(
                    os.path.dirname(sys.modules[cls.__module__].__file__), fname)
        return UserFile.UserFile(fullname)

    def save_data(self, data, note=None):
        """Send an add_data message to the report.

        The object is serialized to JSON, so only use basic types.

        Arguments:
            data: any python object.
            note: A text note describing the data for future users (optional).
        """
        self._report.add_data(data, note)


# --------------------

class PreReq(object):
    """A holder for test prerequisite.

    Used to hold the definition of a prerequisite test. A prerequisite is a
    Test implementation class plus any arguments it may be called with.
    No arguments means ANY arguments.
    """
    def __init__(self, implementation, args=None, kwargs=None):
        self.implementation = str(implementation)
        self.args = args or ()
        self.kwargs = kwargs or {}

    def __repr__(self):
        return "%s(%r, args=%r, kwargs=%r)" % \
                (self.__class__.__name__, self.implementation,
                        self.args, self.kwargs)

    def __str__(self):
        return repr_test(self.implementation, self.args, self.kwargs)


class TestEntry(object):
    """Helper class used to run a Test with arguments and store the result.

    Holds an instance of a Test class and the parameters it will be called
    with.    This actually calls the test, and stores the result value for
    later summary.    It also supports pre-requisite checking.
    """
    def __init__(self, inst, args=None, kwargs=None, autoadded=False):
        self.inst = inst
        self.args = args or ()
        self.kwargs = kwargs or {}
        self._result = TestResult(constants.INCOMPLETE)
        self.autoadded = autoadded # True if automatically added as a prerequisite.

    def run(self, config=None):
        """Invoke the test with its arguments. The config argument is passed
        when run directly from a TestRunner, but not from a TestSuite. It is
        ignored here.
        """
        try:
            self._result = self.inst(*self.args, **self.kwargs)
        except KeyboardInterrupt:
            self._result = TestResult(constants.ABORT)
            raise
        return self._result

    def __eq__(self, other):
        return self.inst == other.inst

    def _setResult(self, val):
        self._result = val

    result = property(lambda s: s._result, _setResult,
                doc="The test rusult enumeration.")

    def match_test(self, name, args, kwargs):
        """Test signature matcher.

        Determine if a test name and set of arguments matches this test.
        """
        return (name, args, kwargs) == \
                    (self.inst.test_name, self.args, self.kwargs)

    def match_prerequisite(self, prereq):
        """Does this test match the specified prerequisite?

        Returns True if this test matches the supplied PreReq object.
        """
        return (self.inst.test_name, self.args, self.kwargs) == \
                    (prereq.implementation, prereq.args, prereq.kwargs)

    def _get_prerequisites(self):
        return self.inst.prerequisites

    prerequisites = property(_get_prerequisites)

    def get_signature(self):
        """Return a unique identifier for this test entry."""
        try:
            return self._signature
        except AttributeError:
            arg_sig = repr((self.args, self.kwargs))
            self._signature = (id(self.inst.__class__), arg_sig)
            return self._signature

    signature = property(get_signature, doc="unique signature string of test.")

    def abort(self):
        """Abort the test suite.

        Causes this this test, and the suite, to be aborted.
        """
        self._result = self.inst.abort("Abort forced by suite runner.")
        return self._result

    test_name = property(lambda s: s.inst.test_name)

    def __repr__(self):
        return repr_test(self.inst.test_name, self.args, self.kwargs)

    def __str__(self):
        return "%s: %s" % (self.__repr__(), self._result)


class SuiteEntry(TestEntry):
    """Entry object that wraps other Suite objects.

    Used when sub-suites are run as test cases.
    """
    def _get_result(self):
        self._results = self.inst.results
        for res in self._results:
            if res.not_passed():
                self._result = res
                return res
        self._result = TestResult(constants.PASSED)
        return TestResult(constants.PASSED)

    def _setResult(self, val):
        self._result = val

    result = property(lambda s: s._get_result(),
                                        _setResult, None,
        """The test rusult enumeration PASSED if all tests in suite passed.""")

    results = property(lambda s: s._results, None, None,
        """The actual list of test results.""")


def PruneEnd(n, l):
    return l[:n]

class TestEntrySeries(TestEntry):
    """
    Provides an efficient means to add many test case instances without
    having to actually instantiate a TestEntry at suite build time.
    """
    def __init__(self, testinstance, N, chooser, filter, args, kwargs):
        from pycopia import combinatorics
        self.inst = testinstance
        self.args = args or ()
        self.kwargs = kwargs or {}
        self._sig = methods.MethodSignature(testinstance.execute)
        self.result = TestResult(constants.INCOMPLETE) # Aggregate of test results
        chooser = chooser or PruneEnd
        arglist = []
        if args:
            arglist.extend(args)
        if kwargs:
            for name, default in self._sig.kwarguments:
                try:
                    val = kwargs[name]
                except KeyError:
                    pass
                else:
                    arglist.append(val)
        self._counter = combinatorics.ListCounter( combinatorics.prune(N, arglist, chooser))
        if filter:
            assert callable(filter)
            self._filter = filter
        else:
            self._filter = lambda *args, **kwargs: True

    test_name = property(lambda s: s.inst.test_name)

    def match_prerequisite(self, prereq):
        """Does this test match the specified prerequisite?

        Returns True if this test name matches the supplied PreReq object.
        Only the name is checked for series tests, since the arguments may vary.
        """
        return self.inst.test_name == prereq.implementation

    def run(self, config=None):
        resultset = {constants.PASSED:0, constants.FAILED:0,
                constants.EXPECTED_FAIL:0, constants.INCOMPLETE:0}
        for argset in self._counter:
            kwargs = self._sig.get_keyword_arguments(argset)
            # kwargs also contains non-keyword args, but python maps them to
            # positional args anyway.
            if self._filter(**kwargs):
                entry = TestEntry(self.inst, (), kwargs)
                entryresult = entry.run()
                resultset[int(entryresult)] += 1
        if resultset[constants.FAILED] > 0:
            self.result = TestResult(constants.FAILED)
        elif resultset[constants.INCOMPLETE] > 0:
            self.result = TestResult(constants.INCOMPLETE)
        elif resultset[constants.PASSED] > 0:
            self.result = TestResult(constants.PASSED)
        return self.result


def repr_test(name, args, kwargs):
    """Produce repr form of test case signature.

    Returns a Test instantiation plus arguments as text (repr).
    """
    return "%s()(%s)" % (name, repr_args(args, kwargs))

def repr_args(args, kwargs):
    """Stringify a set of arguments.

    Arguments:
        args: tuple of arguments as a function would see it.
        kwargs: dictionary of keyword arguments as a function would see it.
    Returns:
        String as you would write it in a script.
    """
    args_s = (("%s, " if kwargs else "%s") % ", ".join(map(repr, args))) if args else ""
    kws = ", ".join(map(lambda it: "%s=%r" % (it[0], it[1]), kwargs.items()))
    return "%s%s" % (args_s, kws)


def parse_args(arguments):
    """Take a string of arguments and keyword arguments and convert back to
    objects.
    """
    # Try a possibly icky method of constructing a temporary function string
    # and exec it (leverage Python parser and argument handling).
    ANY = None # To allow "ANY" keyword in prereq spec.
    def _ArgGetter(*args, **kwargs):
        return args, kwargs
    funcstr = "args, kwargs = _ArgGetter(%s)\n" % arguments
    exec funcstr in locals()
    return args, kwargs # set by exec call


def timestamp(t):
    """standard timesstamp string creator."""
    return timelib.strftime("%a, %d %b %Y %H:%M:%S %Z", timelib.localtime(t))


class TestSuite(object):
    """A Test holder and runner.

    A TestSuite contains a set of test cases (subclasses of Test class) that
    are run sequentially, in the order added. It monitors abort status of
    each test, and aborts the suite if required.

    To run it, create a TestSuite object (or a subclass with some methods
    overridden), add tests with the `add_test()` method, and then call the
    instance. The 'initialize()' method will be run with the arguments given
    when called.
    """
    def __init__(self, cf, nested=0, name=None):
        self.config = cf
        self.report = cf.report
        self._debug = cf.flags.DEBUG
        self._tests = []
        self._testset = set()
        self._multitestset = set()
        self._nested = nested
        cl = self.__class__
        self.test_name = name or "%s.%s" % (cl.__module__, cl.__name__)
        self.result = None

    def __iter__(self):
        return iter(self._tests)

    def _get_results(self):
        return map(lambda t: t.result, self._tests)
    results = property(_get_results)

    def _add_with_prereq(self, entry, _auto=False):
        """Add a TestEntry instance to the list of tests.

        Also adds any prerequisites, if not already present, recursively.
        Don't automatically add prerequisites if debug level is 3 or more.
        """
        if self._debug < 3:
            for prereq in entry.inst.OPTIONS.prerequisites:
                impl = prereq.implementation
                # If only a class name is given, assume it refers to a class
                # in the same module as the defining test, and convert to full
                # path using that module.
                if "." not in impl:
                    impl = sys.modules[entry.inst.__class__.__module__].__name__ + "." + impl
                    prereq.implementation = impl
                pretestclass = module.get_object(impl)
                pretestclass.set_test_options()
                preentry = TestEntry(pretestclass(self.config), prereq.args, prereq.kwargs, True)
                presig, argsig = preentry.get_signature()
                if presig not in self._multitestset:
                    self._add_with_prereq(preentry, True)
        testcaseid = entry.get_signature()
        if not _auto:
            self._tests.append(entry)
        elif testcaseid not in self._testset:
                self._tests.append(entry)
        self._testset.add(testcaseid)


    def add_test(self, _testclass, *args, **kwargs):
        """Add a Test subclass and its arguments to the suite.

    Appends a test object in this suite. The test's `execute()` will be
    called (at the appropriate time) with the arguments supplied here. If
    the test case has a prerequisite defined it is checked for existence in
    the suite, and an exception is raised if it is not found.
    """
        if isinstance(_testclass, str):
            _testclass = module.get_class(_testclass)
        _testclass.set_test_options()
        testinstance = _testclass(self.config)
        entry = TestEntry(testinstance, args, kwargs, False)
        self._add_with_prereq(entry)

    def add_tests(self, _testclasslist, *args, **kwargs):
        """Add a list of tests at once.

        Similar to add_test method, but adds all test case classes found in the
        given list.  Arguments are common to all tests.
        If object is a tuple it should be a (testclass, tuple, dictionary) of
        positional and keyword arguments.
        """
        assert isinstance(_testclasslist, list)
        for testclass in _testclasslist:
            if type(testclass) is tuple:
                self.add_test(*testclass)
            else:
                self.add_test(testclass, *args, **kwargs)

    def add_test_from_result(self, dbtestresult):
        """Add a Test from information taken from stored test result.

        This basically means duplicate the test call that originated that test
        result.
        """
        testclass = module.get_class(dbtestresult.testimplementation)
        testclass.set_test_options()
        args, kwargs = parse_args(dbtestresult.arguments)
        testinstance = testclass(self.config)
        entry = TestEntry(testinstance, args, kwargs, False)
        self._add_with_prereq(entry)

    def add_test_series(self, _testclass, N=100, chooser=None, filter=None,
                                        args=None, kwargs=None):
        """Add a Test case as a series.

        The arguments must be lists of possible values for each parameter. The
        args and kwargs arguments are lists that are combined in all possible
        combinations, except pruned to N values. The pruning policy can be
        adjusted by the chooser callback, and the N value itself.

        Args:
            testclass (class): the Test class object (subclass of core.Test).

            N (integer): Maximum iterations to take from resulting set. Default
                    is 100 just to be safe.

            chooser (callable): callable that takes one number and a list
                    argument, returns a list of the specified (N) length.
                    Default is to chop off the top end of the list.

            filter (callable): callable that takes a set of arguments with the
                    same semantics as the Test.execute() method and returns True or
                    False to indicate if that combination should be included in the
                    test. You might want to set a large N if you use this.

            args (tuple): tuple of positional arguments, each argument is a list.
                                        example: args=([1,2,3], [4,5]) maps to positional
                                        argumnts of execute() method of Test class.

            kwargs (dict): Dictionary of keyword arguments, with list of values
                    as value.
                                        example: kwargs={"arg1":["a", "b", "c"]}
                                        maps to keyword arguments of execute() method of Test
                                        class.
        """
        if isinstance(_testclass, str):
            _testclass = module.get_class(_testclass)
        _testclass.set_test_options()
        testinstance = _testclass(self.config)
        try:
            entry = TestEntrySeries(testinstance, N, chooser, filter, args, kwargs)
        except ValueError, err: # ListCounter raises this if there is an empty list.
            self.info("addTestSeries Error: %s. Not adding %s as series." % (
                    err, _testclass.__name__))
        else:
            # series tests don't get auto-added (can't know what all the args
            # are, and even so the set could be large.)
            mysig, myargsig = entry.get_signature()
            self._multitestset.add(mysig) # only add by id.
            self._add_with_prereq(entry)

    def add_suite(self, suite, test_name=None):
        """Add an entire suite of tests to this suite.

    Appends an embedded test suite in this suite. This is called a sub-suite
    and is treated as a single test by this containing suite.
    """
        if isinstance(suite, str):
            suite = module.get_class(suite)
        if type(suite) is type(Test): # class type
            suite = suite(self.config, 1)
        else:
            suite.config = self.config
            suite._nested = 1
        self._tests.append(SuiteEntry(suite))
        # sub-tests need unique names
        if test_name:
            suite.test_name = test_name
        else:
            # Name plus index into suite list.
            suite.test_name = "%s-%s" % (suite.test_name, len(self._tests)-1)
        return suite

    def add(self, klass, *args, **kwargs):
        """Add a Suite or a Test to this TestSuite.

    Most general method to add test case classes or other test suites.
    """
        if type(klass) is type:
            if issubclass(klass, Test):
                self.addTest(klass, *args, **kwargs)
            elif issubclass(klass, TestSuite):
                self.add_suite(klass, *args, **kwargs)
            else:
                raise ValueError, "TestSuite.add: invalid class type."
        else:
                raise ValueError, "TestSuite.add: need a class type."

    def get_test_entries(self, name, *args, **kwargs):
        """Get a list of test entries that matches the signature.

        Return a list of Test entries that match the name and calling
        arguments.
        """
        for entry in self._tests:
            if entry.matches(name, args, kwargs):
                yield entry

    def add_arguments(self, name, args, kwargs):
        """Add calling arguments to an existing test entry that has no
        arguments.
        """
        for entry in self.get_test_entries(name):
            entry.add_arguments(args, kwargs)

    def info(self, msg):
        """Informational messages for the report.

        Record non-critical information in the report object.
        """
        self.report.info(msg, 1)

    def report_build(self, buildstring):
        """Report any build information. Usually a version or build number.

        The buildstring parameter must match the following pattern::

            <projectname>[ .:]<major>.<minor>.<subminor>.<build>
        """
        self.report.add_message("BUILD", buildstring, 1)

    def _get_prerequisites(self):
        """Get the list of prerequisites.

        This is here for polymorhism with Test objects. Always return empty list.
        """
        return ()

    prerequisites = property(_get_prerequisites)

    def run(self, config=None):
        """Define the runnable interface. May be called by the test runner."""
        if config is not None:
            self.config = config
            self.report = config.report
            self._debug = config.flags.DEBUG
        return self.__call__()

    def get_start_timestamp(self):
        return timelib.strftime("%m%d%H%M%S", timelib.localtime(self.starttime))

    def __call__(self, *args, **kwargs):
        """Invoke the test suite.

        Calling the instance is the primary way to invoke a suite of tests.
        Any supplied parameters are passed onto the suite's initialize()
        method.

        It will then run all TestEntry, report on interrupts, and check for
        abort conditions. It will also skip tests whose prerequisites did not
        pass. If the debug level is 2 or more then the tests are not skipped.

        If a Test returns None (Python's default), it is reported
        as a failure since it was not written correctly.
        """
        self.config.register_testsuite(self.test_name)
        self.starttime = timelib.now()
        try:
            self._initialize(*args, **kwargs)
        except TestSuiteAbort:
            self._finalize()
            rv = constants.INCOMPLETE
        else:
            self._run_tests()
            rv = self._finalize()
        endtime = timelib.now()
        self.config.register_testsuite(None)
        self.report.add_message("STARTTIME", self.starttime, 1)
        self.report.add_message("ENDTIME", endtime, 1)
        return rv

    def _initialize(self, *args, **kwargs):
        self.report.add_heading(self.test_name, 1)
        if self.config.flags.VERBOSE:
            s = ["Tests in suite:"]
            for i, entry in enumerate(self._tests):
                s.append("%3d. %r" % (i + 1, entry))
            self.report.info("\n".join(s), 1)
            del s
        try:
            self.initialize(*args, **kwargs)
        except KeyboardInterrupt:
            self.info("Suite aborted by user in initialize().")
            raise TestSuiteAbort("Interrupted in suite initialize.")
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
            self.info("Suite failed to initialize: %s (%s)" % (ex, val))
            raise TestSuiteAbort(val)

    def check_prerequisites(self, currententry, upto):
        """Verify that the prerequisite test passed.

        Verify any prerequisites are met at run time.
        """
        for prereq in currententry.prerequisites:
            for entry in self._tests[:upto]:
                if entry.match_prerequisite(prereq):
                    if entry.result.is_passed():
                        continue
                    else:
                        self.report.add_heading(currententry.inst.test_name, 2)
                        self.report.diagnostic("Prerequisite: %s" % (prereq,), 2)
                        self.report.incomplete("Prerequisite did not pass.", 2)
                        currententry.result = TestResult(constants.INCOMPLETE)
                        return False
        return True # No prerequisite or prereq passed.

    def _run_tests(self):
        for i, entry in enumerate(self._tests):
            if self._debug < 2 and not self.check_prerequisites(entry, i):
                continue
            # Add a note to the logfile to delimit test cases there.
            if self.config.flags.VERBOSE:
                self.config.logfile.note("%s: %r" % (timelib.localtimestamp(), entry))
            try:
                rv = entry.run()
            except KeyboardInterrupt:
                if self._nested:
                    raise TestSuiteAbort("Sub-suite aborted by user.")
                else:
                    if self.config.UI.yes_no("Test interrupted. Abort suite?"):
                        self.info("Test suite aborted by user.")
                        break
            except TestSuiteAbort, err:
                self.info("Suite aborted by test %s (%s)." % (entry.test_name, err))
                entry.result = TestResult(constants.INCOMPLETE)
                rv = constants.ABORT
                break
            # This should only happen with an incorrectly written execute() method.
            if rv is None:
                self.report.diagnostic(
                        "warning: test returned None, assuming INCOMPLETE. "
                        "Please fix the %s.execute() method." % (entry.test_name))
                rv = constants.INCOMPLETE
            # check for abort condition and break the loop if so
            if rv == constants.ABORT:
                break

    def _finalize(self):
        try:
            self.finalize()
        except KeyboardInterrupt:
            if self._nested:
                raise TestSuiteAbort(
                        "Suite {!r} aborted by user in finalize().".format(self.test_name))
            else:
                self.info("Suite aborted by user in finalize().")
        except:
            ex, val, tb = sys.exc_info()
            if self._debug:
                print # ensure debugger prompts starts on new line.
                debugger.post_mortem(tb, ex, val)
            self.info("Suite failed to finalize: %s (%s)" % (ex, val))
            if self._nested:
                raise TestSuiteAbort(
                        "subordinate suite {!r} failed to finalize.".format(self.test_name))
        self._summarize()
        self._report_summary()
        return self.result

    def _summarize(self):
        """Summarize the results.

        If any test failed, suite is also failed.
        If no failures, but any incomplete, suite is incomplete.
        If nothing passed (empty suite?) then suite is incomplete.
        If all tests passed, then suite is also passed.

        """
        resultset = {
            constants.FAILED: 0,
            constants.PASSED: 0,
            constants.INCOMPLETE: 0,
        }
        for entry in self._tests:
            if entry.result is None:
                resultset[constants.INCOMPLETE] += 1
            elif entry.result.is_failed():
                resultset[constants.FAILED] += 1
            elif entry.result.is_incomplete():
                resultset[constants.INCOMPLETE] += 1
            elif entry.result.is_passed():
                resultset[constants.PASSED] += 1
        if resultset[constants.FAILED] > 0:
            result = constants.FAILED
        elif resultset[constants.INCOMPLETE] > 0:
            result = constants.INCOMPLETE
        elif resultset[constants.PASSED] == 0:
            result = constants.INCOMPLETE
        else:
            result = constants.PASSED
        self.result = TestResult(result)

    def _report_summary(self):
        """Sends the summarized result to the report."""
        self.report.add_heading("Summarized results for %s." % self.__class__.__name__, 3)
        entries = filter(lambda te: te.result is not None, self._tests)
        self.report.add_summary(entries)
        resultmsg = "Aggregate result for %r." % (self.test_name,)
        result = int(self.result)
        if not self._nested:
            if result == constants.PASSED:
                self.report.passed(resultmsg)
            elif result == constants.FAILED:
                self.report.failed(resultmsg)
            elif result == constants.INCOMPLETE:
                self.report.incomplete(resultmsg)

    def __str__(self):
        s = ["Tests in suite:"]
        s.extend(map(str, self._tests))
        return "\n".join(s)

    ### overrideable interface. ###
    def initialize(self, *args, **kwargs):
        """initialize phase handler for suite-level initialization.

        Override this if you need to do some initialization just before the
        suite is run. This is called with the arguments given to the TestSuite
        object when it was called.
        """
        pass

    def finalize(self):
        """Run the finalize phase for suite level.

        Aborts the suite on error or interrupt. If this is a sub-suite then
        TestSuiteAbort is raised so that the top-level suite can handle it.

        Override this if you need to do some additional clean-up after the suite is run.
        """
        pass


class UseCase(object):
    """UseCase type.

    Used to define use cases, which typically involve constructing TestSuite
    and running it.  These are generally more complex operations, involving
    multiple steps. Each step can be made into a TestCase object, and assembled
    into a TestSuite using data from the configuration. Then run here.
    """
    @staticmethod
    def get_suite(config):
        return TestSuite(config, name="EmptySuite")

    @classmethod
    def run(cls, config):
        suite = cls.get_suite(config)
        suite.run()

