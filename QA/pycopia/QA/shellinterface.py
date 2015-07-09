#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The command-line interface to a test runner or reporter.  Adapts options given
on a command line to paramters to test cases and operates the test runner.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os

from pycopia import logging
from pycopia import getopt
from pycopia import module


def choose_tests():
    try:
        import testcases
    except ImportError:
        logging.warn("Cannot find 'testcases' base package.")
        return None
    from pycopia import UI
    from pycopia.QA import core

    ui = UI.get_userinterface(themename="ANSITheme")
    ui.printf("Select any number of runnable objects. %n"
            "You can select %wmodules%N, %gUseCase%N objects, or single %yTest%N object.")
    # callback for testdir walker
    def filternames(flist, dirname, names):
        for name in names:
            if name.endswith(".py") and not name.startswith("_"):
                flist.append(os.path.join(dirname, name[:-3]))
    modnames = []
    runnables = []
    for testbase in testcases.__path__:
        mnlist = []
        os.path.walk(testbase, filternames, mnlist)
        testhome_index = len(os.path.dirname(testbase)) + 1
        modnames.extend(map(lambda n: n[testhome_index:].replace("/", "."), mnlist))
    modnames.sort()
    for modname in modnames:
        try:
            mod = module.get_module(modname)
        except module.ModuleImportError:
            ui.warning("  Warning: could not import '{}'".format(modname))
            continue
        if getattr(mod, "run", None) is not None:
            runnables.append(FormatWrapper(ui, modname, None, "%w%U%N"))
        for attrname in dir(mod):
            obj = getattr(mod, attrname)
            if type(obj) is type:
                if issubclass(obj, core.UseCase):
                    runnables.append(FormatWrapper(ui, modname, obj.__name__, "%U.%g%O%N"))
                if issubclass(obj, core.Test):
                    runnables.append(FormatWrapper(ui, modname, obj.__name__, "%U.%y%O%N"))
    return [o.fullname for o in ui.choose_multiple(runnables, prompt="Select tests")]


class FormatWrapper(object):
    """Wrap module path object with a format.

    The format string should have an '%O' component that will be expanded to
    the stringified object, and an '%U' component for the module name.
    """
    def __init__(self, ui, module, objname, format):
        self._ui = ui
        self.modname = module
        self.name = objname
        self._format = format

    @property
    def fullname(self):
        if self.name:
            return "{}.{}".format(self.modname, self.name)
        else:
            return self.modname

    def __str__(self):
        self._ui.register_format_expansion("O", self._str_name)
        self._ui.register_format_expansion("U", self._str_module)
        try:
            return self._ui.format(self._format)
        finally:
            self._ui.unregister_format_expansion("O")
            self._ui.unregister_format_expansion("U")

    def _str_name(self, c):
        return str(self.name)

    def _str_module(self, c):
        return str(self.modname)

    def __len__(self):
        return len(self.fullname)

    def __cmp__(self, other):
        return cmp(self.modname, other.modname)


# not in a docstring since docstrings don't exist in optimize mode.
TestRunnerInterfaceDoc = r"""
Invoke a test or test suite from a shell.

Usage:

    %s [-h?dDviIr] [-c|-f <configfile>] [-n <string>] arg...

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
            -n <string> -- Add a comment to the test report.
            -c or -f <file> -- Merge in extra configuration file.
            -r -- Report on test case or test suite specified. Don't run it.
                  Without arguments show the possible report and environment
                  names.

    Long options are passed as parameters to test cases, in the configuration
    object. Common long options are:

            --reportname=      -- The name of the report to use,
                                  defined in the config.reports area.
            --environmentname= -- Name of the environment to use.
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
        cf.flags.REPORT = False
        cf.flags.INTERACTIVE = False
        cf.flags.DEBUG = 0
        cf.flags.VERBOSE = 0
        optlist, extraopts, args = getopt.getopt(argv[1:], "h?dDviIrc:f:n:")
        for opt, optarg in optlist:
            if opt in ("-h", "-?"):
                print (TestRunnerInterfaceDoc % (os.path.basename(argv[0]),))
                return
            elif opt == "-d":
                cf.flags.DEBUG += 1
            elif opt == "-D":
                from pycopia import autodebug # top-level debug for framework bugs
            elif opt == "-v":
                cf.flags.VERBOSE += 1
            elif opt == "-i":
                cf.flags.INTERACTIVE = True
            elif opt == "-I":
                cf.flags.INTERACTIVE = False
            elif opt == "-c" or opt == "-f":
                cf.mergefile(optarg)
            elif opt == "-n":
                cf.comment = optarg
            elif opt == "-r":
                cf.flags.REPORT = True
        cf.evalupdate(extraopts)
        # original command line arguments saved for the report
        cf.arguments = [os.path.basename(argv[0])] + argv[1:]
        # Save extra options for overriding configuration after a mergefile
        # because command line options should have highest precedence.
        self.runner.set_options(extraopts)

        if not args:
            if cf.flags.REPORT:
                self.runner.report_global()
                return 0
            else:
                args = choose_tests()
        if not args:
            return 2
        objects, errors = module.get_objects(args)
        if errors:
            logging.warn("Errors found while loading test object:")
            for error in errors:
                logging.warn(error)
        if objects:
            cf.argv = args
            self.runner.initialize()
            rv = self.runner.run_objects(objects)
            self.runner.finalize()
            return not rv # inverted due to shell semantics (zero is good) being different from result code
        else:
            return int(bool(errors)) + 2


TestReporterInterfaceDoc = r"""
Report various information about a tests and suites.

Usage:

    %s [-hgdDv] [-c|-f <configfile>] arg...

    Where the arguments are test suite or test case names. If none are
    supplied a menu is presented.
    Options:
        Tells the runner what test modules to run, and sets the flags in the
        configuration. Options are:

            -h -- Print help text and return.
            -g -- Report on global configuration options.
            -d -- Turn on debugging for tests.
            -D -- Turn on debugging for tool itself.
            -v -- Increase verbosity, show more information.
            -c or -f <file> -- Merge in extra configuration file.

"""

class TestReporterInterface(object):
    """A Basic CLI interface to a TestReporter object.

    Instantiate with an instance of a TestReporter.

    Call the instance of this with an argv list to report on the given runnable items.
    """
    def __init__(self, testreporter):
        self.reporter = testreporter

    def __call__(self, argv):
        cf = self.reporter.config
        cf.flags.DEBUG = 0
        cf.flags.VERBOSE = 0
        optlist, extraopts, args = getopt.getopt(argv[1:], "h?gdDvc:f:")
        for opt, optarg in optlist:
            if opt in ("-h", "-?"):
                print (TestReporterInterfaceDoc % (os.path.basename(argv[0]),))
                return
            elif opt == "-g":
                self.reporter.report_global()
            elif opt == "-d":
                cf.flags.DEBUG += 1
            elif opt == "-D":
                from pycopia import autodebug # top-level debug for framework bugs
            elif opt == "-v":
                cf.flags.VERBOSE += 1
            elif opt == "-c" or opt == "-f":
                cf.mergefile(optarg)
        cf.evalupdate(extraopts)
        if not args:
            args = choose_tests()
        if not args:
            return
        objects, errors = module.get_objects(args)
        if errors:
            self.reporter.report_errors(errors)
        if objects:
            self.reporter.report_objects(objects)


