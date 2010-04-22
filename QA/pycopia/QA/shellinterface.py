#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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


#### The command-line interface object. ####

import sys
import os
import logging

from pycopia import getopt
from pycopia import module


def get_module_list():
    """Get list of test modules.

    Used by user interfaces to select a module to run. All automated test
    implementations are located in a base package called "testcases".

    Returns:
        A complete list of module names found in the "testcases" package, as
        strings. This includes sub-packages.
    """
    try:
        import testcases
    except ImportError:
        logging.warn("Cannot find 'testcases' base package.")
        return []
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


# not in a docstring since docstrings don't exist in optimize mode.
TestRunnerInterfaceDoc = r"""
Invoke a test or test suite from a shell.

Usage:

    %s [-hdviIcf] [-n <string>] arg...

    Where the arguments are test suite or test case names. If none are
    supplied a menu is prese/home/kdart/bin/runtestnted.

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
/home/kdart/bin/runtest
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
        cf.evalupdate(extraopts)
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


