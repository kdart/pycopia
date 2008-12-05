#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# Copyright The Android Open Source Project

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at 
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Module that defines test loaders.

The objects here are responsible for taking a desired test, or set of
tests, looking in the database for implementations and dependencies, and
constructing a runnable test objects. It also provides utility functions
for listing and instantiating runnable test objects.
"""


__author__ = 'keith@kdart.com (Keith Dart)'
__original_author__ = 'dart@google.com (Keith Dart)'


import sys
import os

from pycopia.aid import newclass
from pycopia.textutils import identifier

from pycopia.QA import core
from pycopia import module


class Error(Exception):
    """Base class for test loader errors."""

class NoImplementationError(Error):
    """Raised when a test object has no automated implementation defined."""

class InvalidObjectError(Error):
    """Raised when an attempt is made to instantiate a test object from the
    database, but the object in the database is marked invalid.
    """

class InvalidTestError(Error):
    """Raised when a test is requested that cannot be run for some
    reason.
    """

def get_test_class(dbcase):
    """Return the implementation class of a TestCase, or None if not found.
    """
    if dbcase.automated and dbcase.valid:
        impl = dbcase.testimplementation
        if impl:
            obj = module.get_object(impl)
            if type(obj) is type and issubclass(obj, core.Test):
                return obj
            else:
                raise InvalidTestError("%r is not a Test class object." % (obj,))
        else:
            raise NoImplementationError(
                                        "No implementation defined for test %r." % (dbcase.name,))
    else:
        return None


def new_testsuite(dbsuite):
    """Return a runnable Suite converted from a stored TestSuite."""
    if dbsuite.valid:
        return newclass(identifier(dbsuite.name), core.TestSuite)
    else:
        raise InvalidObjectError("%s is not runnable (not valid)." % (dbsuite,))


def get_module_file(mod):
    """Find the source file for a module. Give the module, or a name of one.

    Returns:
        Full path name of Python source file. Returns None if not found."""
    if type(mod) is str:
        mod = module.get_module(mod)
    try:
        basename, ext = os.path.splitext(mod.__file__)
    except AttributeError: # C modules don't have a __file__ attribute
        return None
    testfile = basename + ".py"
    if os.path.isfile(testfile):
        return testfile
    return None


def get_module_list():
    """Get list of test modules.

    Used by user interfaces to select a module to run. All automated test
    implementations are located in a base package called "testcases".

    Returns:
        A complete list of module names found in the "testcases" package, as
        strings. This includes sub-packages.
    """
    import testcases
    # callback for testdir walker
    def filternames(flist, dirname, names):
        for name in names:
            if name.endswith(".py") and not name.startswith("_"):
                flist.append(os.path.join(dirname, name[:-3]))
    testhome = os.path.dirname(testcases.__file__)
    modnames = []
    os.path.walk(testhome, filternames, modnames)
    testhome_index = len(os.path.dirname(testhome)) + 1
    names = map(lambda n: n[testhome_index:].replace("/", "."), modnames)
    names.sort()
    return names

# store type objects here for speed
ModuleType = type(core)
FunctionType = type(get_module_list)


#### The command-line interface object. ####


# not in a docstring since docstrings don't exist in optimize mode.
TestRunnerInterfaceDoc = r"""
Invoke a test or test suite from a shell.

Usage:

    %s [-hdviIcf] [-n <string>] arg...

    Where the arguments are test suite or test case names. If none are
    supplied a menu is presented.

    Options:
        Tells the runner what test modules to run, and sets the flags in the
        configuration. Options are:

            -h -- Print help text and return.
            -d -- Turn on debugging for tests.
            -D -- Turn on debugging for framework.
            -v -- Increase verbosity.
            -i -- Set flag to run interactive tests.
            -I -- Set flag to skip interactive tests.
            -c or -f <file> -- Merge in extra configuration file.
            -n <string> -- Add a comment to the test report.
"""

class TestRunnerInterface(object):
    """A Basic CLI interface to a TestRunner object.

    Instantiate with an instance of a TestRunner.

    Call the instance of this with an argv list to instantiate and run the
    given tests.
    """
    def __init__(self, testrunner):
        self.runner = testrunner

    def __call__(self, argv):
        """Run the test runner.

        Invoke the test runner by calling it.
        """
        cf = self.runner.config
        # this getopt() is a lightweight getopt that only considers
        # traditional options as options (e.g. -x). Any long-option form (e.g.
        # --reportname=default) is converted into a dictionary and is used to
        # update the configuration. This allows the user or test runner to
        # provide or alter configuration parameters at run time without
        # needing a pre-defined list to getopt().
        from pycopia import getopt
        optlist, extraopts, args = getopt.getopt(argv[1:], "h?dDviIc:f:n:")
        for opt, optarg in optlist:
            if opt in ("-h", "-?"):
                print TestRunnerInterfaceDoc % (os.path.basename(argv[0]),)
                return
            if opt == "-d":
                cf.flags.DEBUG += 1
            if opt == "-D":
                from pycopia import autodebug # top-level debug for framework bugs
            if opt == "-v":
                cf.flags.VERBOSE += 1
            if opt == "-i":
                cf.flags.INTERACTIVE = True
            if opt == "-I":
                cf.flags.INTERACTIVE = False
            if opt == "-c" or opt == "-f":
                cf.mergefile(optarg)
            if opt == "-n":
                cf.comment = optarg
        cf.update(extraopts)
        # original command line arguments saved for the report
        cf.arguments = [os.path.basename(argv[0])] + argv[1:]
        # Save extra options for overriding configuration after a mergefile
        # because command line options should have highest precedence.
        self.runner.set_options(extraopts)

        if not args:
            from pycopia import cliutils
            l = get_module_list()
            l.insert(0, None)
            arg = cliutils.choose(l, prompt="Select test")
            if arg is None:
                return
            args = [arg]
        objects, errors = module.get_objects(args)
        if errors:
            print >>sys.stderr, "Errors found while loading test object:"
            for error in errors:
                print >>sys.stderr, error
        if objects:
            cf.argv = args
            self.runner.initialize()
            self.runner.run_objects(objects)
            self.runner.finalize()



