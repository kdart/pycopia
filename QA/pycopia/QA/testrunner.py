#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


"""Top level test runner.

This module provides the primary test runner for the automation framework.

"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import os
import shutil
from errno import EEXIST

from pycopia import logging
from pycopia import timelib
from pycopia.QA import core
from pycopia.QA import constants
from pycopia import reports

# for object type checking
ModuleType = type(sys)
TypeType = type


class Error(Exception):
    """Testrunner errors."""
    pass

class TestRunnerError(Error):
    """Raised for a runtime error of the test runner."""


class TestRunner(object):
    """Runs test objects.

    Handled running objects, generating the report, and other overhead of
    running tests and cleaning up afterwards.
    """
    def __init__(self, config):
        self.config = config
        self.config.options_override = {}
        self.config.arguments = []
        if config.flags.DEBUG:
            logging.loglevel_debug()
        else:
            logging.loglevel_warning()

    def set_options(self, opts):
        if isinstance(opts, dict):
            self.config.options_override = opts
        else:
            raise ValueError("Options must be dictionary type.")

    def run_object(self, obj):
        """Run a test object (object with run() function or method).

        Arguments:
            obj:
                A Python test object.    This object must have a `run()` function
                or method that takes a configuration object as it's single
                parameter. It should also have a `test_name` attribute.

        Messages:
            May send any of the following messages to the report object:
                RUNNERARGUMENTS:
                    command-line arguments given to test runner.
                logfile:
                    name of the log file from the configuration.
                COMMENT:
                    User supplied comment given when test object was invoked.
                RUNNERSTART:
                    Timestamp when test runner started.
                RUNNEREND:
                    Timestamp when test runner ends.
                add_url:
                    Location where any generated data files, logs, and reports can
                    be found.

        """
        cf = self.config
        basename = "_".join(obj.test_name.split("."))
        cf.reportfilename = basename
        cf.logbasename = basename + "-" + cf.runnertimestamp + ".log"
        # resultsdir is where you would place any resulting data files. This
        # is also where any report object or log files are placed.
        cf.resultsdir = os.path.join(
            os.path.expandvars(cf.get("resultsdirbase", "/var/tmp")),
            "%s-%s-%s" % (cf.reportfilename, cf.username, cf.runnertimestamp))
        cf.evalupdate(cf.options_override)
        self._create_results_dir()
        self._set_report_url()
        cf.report.logfile(cf.logfilename)
        # run the test object!
        return obj.run(cf)

    def run_objects(self, objects):
        """Invoke the `run` method on a list of mixed runnable objects.

        Arguments:
            objects:
                A list of runnable objects. A runnable object is basically
                something that has a callable named "run" that takes a
                configuration object as a parameter.

        May raise TestRunnerError if an object is not runnable by this test
        runner.
        """
        rv = 0
        testcases = []
        for obj in objects:
            objecttype = type(obj)
            if objecttype is ModuleType and hasattr(obj, "run"):
                rv = self.run_module(obj)
            elif objecttype is TypeType and issubclass(obj, core.Test):
                testcases.append(obj)
            elif isinstance(obj, core.TestSuite):
                rv = self.run_object(obj)
            elif objecttype is type and hasattr(obj, "run"):
                # a bare class uses as a subcontainer of test or suite constructor.
                rv = self.run_class(obj)
            else:
                logging.warn("%r is not a runnable object." % (obj,))
        if testcases:
            if len(testcases) > 1:
                rv = self.run_tests(testcases)
            else:
                args = []
                kwargs = {}
                opts = self.config.options_override.copy()
                for name, value in opts.items():
                    if name.startswith("arg"):
                        try:
                            index = int(name[3]) # use --arg1=XXX to place argument XXX
                        except (ValueError, IndexError):
                            logging.warn("{!r} not converted to argument.".format(name))
                        else:
                            try:
                                args[index] = value
                            except IndexError:
                                need = index - len(args)
                                while need:
                                    args.append(None)
                                    need -= 1
                                args.append(value)
                        del self.config.options_override[name]
                        del self.config[name]
                    elif name.startswith("kwarg_"): # use --kwarg_XXX to place keyword argument XXX
                        kwargs[name[6:]] = value
                        del self.config.options_override[name]
                        del self.config[name]
                rv = self.run_test(testcases[0], *args, **kwargs)
        return rv

    def run_class(self, cls):
        """Run a container class inside a module.

        The class is run as if it were a module, using the classes containing
        module. The class is just a container, and the run method should be a
        static method or class method.

        Arguments:
            class with run method:
                A class object with a run() method that takes a configuration
                object as it's single parameter.

        Returns:
            The return value of the class's run() method, or FAILED if the
            module raised an exception.
        """
        rpt = self.config.report
        cls.test_name = ".".join([cls.__module__, cls.__name__])
        ID = get_module_version(sys.modules[cls.__module__])
        rpt.add_message("MODULEVERSION", ID)
        rpt.add_message("USECASESTARTTIME", timelib.now())
        try:
            rv = self.run_object(cls)
        except KeyboardInterrupt:
            rpt.add_message("MODULEENDTIME", timelib.now())
            rpt.incomplete("Module aborted by user.")
            raise
        except:
            ex, val, tb = sys.exc_info()
            if self.config.flags.DEBUG:
                from pycopia import debugger
                debugger.post_mortem(tb, ex, val)
            rpt.add_message("MODULEENDTIME", timelib.now())
            rpt.incomplete("Test container exception: %s (%s)" % (ex, val))
            return constants.INCOMPLETE
        else:
            rpt.add_message("MODULEENDTIME", timelib.now())
            return rv

    def run_module(self, mod):
        """Run a test module.

        Prepares the configuration with module configuration, sends report
        messages appropriate for modules, and reports pass or fail.

        Arguments:
            mod:
                A module object with a run() function that takes a configuration
                object as it's single parameter.

        Returns:
            The return value of the module's Run() function, or FAILED if the
            module raised an exception.
        """
        cf = self.config
        # make the module look like a test.
        mod.test_name = mod.__name__
        ID = get_module_version(mod)
        cf.report.add_message("MODULEVERSION", ID)
        cf.report.add_message("USECASESTARTTIME", timelib.now())
        try:
            rv = self.run_object(mod)
        except KeyboardInterrupt:
            cf.report.add_message("MODULEENDTIME", timelib.now())
            cf.report.incomplete("Module aborted by user.")
            raise
        except:
            ex, val, tb = sys.exc_info()
            if cf.flags.DEBUG:
                from pycopia import debugger
                debugger.post_mortem(tb, ex, val)
            rv = constants.FAILED
            cf.report.add_message("MODULEENDTIME", timelib.now())
            cf.report.failed("Module exception: %s (%s)" % (ex, val))
        else:
            cf.report.add_message("MODULEENDTIME", timelib.now())
            if rv is None:
                # If module run() function returns None we take that to mean that
                # it runs a TestSuite itself. Report PASSED value.
                return 1
            elif type(rv) is core.TestResult:
                return bool(rv)
            # If the module returns something else we take that to mean that
            # it is reporting some true/false value to report as pass/fail.
            elif rv:
                return cf.report.passed("Return evaluates True.")
            else:
                return cf.report.failed("Return evaluates False.")

    def run_suite(self, suite):
        """Run a TestSuite object.

        Given a pre-populated TestSuite object, run it after initializing
        configuration and report objects.

        Arguments:
            suite:
                An instance of a core.TestSuite class or subclass. This should
                already have Test objects added to it.

        Returns:
            The return value of the suite. Should be PASSED or FAILED.

        """
        if not isinstance(suite, core.TestSuite):
            raise TestRunnerError("Must supply TestSuite object.")
        return self.run_object(suite)

    def run_test(self, testclass, *args, **kwargs):
        """Run a test single test class with arguments.

        Runs a single test class with the provided arguments. Test class
        is placed in a temporary TestSuite.

        Arguments:
            testclass:
                A class that is a subclass of core.Test. Any extra arguments given
                are passed to the `execute()` method when it is invoked.

        Returns:
            The return value of the Test instance. Should be PASSED, FAILED,
            INCOMPLETE, or ABORT.
        """

        suite = core.TestSuite(self.config, name="%sSuite" % testclass.__name__)
        suite.add_test(testclass, *args, **kwargs)
        return self.run_object(suite)

    def run_tests(self, testclasses):
        """Run a list of test classes.

        Runs a list of test classes. Test classes are placed in a temporary
        TestSuite.

        Arguments:
            testclasses:
                A list of classes that are subclasses of core.Test.

        Returns:
            The return value of the temporary TestSuite instance.
        """

        suite = core.TestSuite(self.config, name="RunTestsTempSuite")
        suite.add_tests(testclasses)
        return self.run_object(suite)

    def _create_results_dir(self):
        """Make results dir, don't worry if it already exists."""
        try:
            os.mkdir(self.config.resultsdir)
        except OSError as error:
            if error[0] == EEXIST:
                pass
            else:
                raise

    def _set_report_url(self):
        """Construct a URL for finding the report and test produced data.

        If the configuration has a `baseurl` and `documentroot` defined then
        the results location is available by web server and a URL is sent to
        the report. If not, the a directory location is sent to the report.
        """
        cf = self.config
        baseurl = cf.get("baseurl")
        documentroot = cf.get("documentroot")
        resultsdir = cf.resultsdir
        if baseurl and documentroot:
            cf.report.add_url("Results location.", baseurl + resultsdir[len(documentroot):])
        else:
            cf.report.add_url("Results location.", "file://" + resultsdir)

    def initialize(self):
        """Perform any initialization needed by the test runner.

        Initializes report. Sends runner and header messages to the report.
        """
        cf = self.config
        cf.username = os.environ["USER"]
        os.chdir(cf.logfiledir) # Make sure runner CWD is a writable place.
        cf.runnerstarttime = starttime = timelib.now()
        cf.runnertimestamp = timelib.strftime("%Y%m%d%H%M%S",
                timelib.localtime(cf.runnerstarttime))
        try:
            rpt = cf.get_report()
        except reports.ReportFindError as err:
            cf.UI.error(str(err))
            cf.UI.printf("%YUse at least one of the following%N:")
            cf.UI.print_list(cf.reports.keys())
            cf.UI.Print("\n")
            raise TestRunnerError("Cannot continue without report.")
        # Report file's names. save for future use.
        rpt.initialize(cf)
        cf.reportfilenames = rpt.filenames
        rpt.add_title("Test Results for %r." % " ".join(cf.get("argv", ["unknown"])))
        arguments = cf.get("arguments")
        # Report command line arguments, if any.
        if arguments:
            rpt.add_message("RUNNERARGUMENTS", " ".join(arguments))
        # Report comment, if any.
        comment = cf.get("comment")
        if comment:
            rpt.add_message("COMMENT", comment)
        # Report build here, if given.
        build = cf.get("build")
        if build:
            rpt.add_message("BUILD", build)
        rpt.add_message("RUNNERSTARTTIME", starttime, 0)

    def finalize(self):
        """Perform any finalization needed by the test runner.
        Sends runner end messages to report. Finalizes report.
        """
        cf = self.config
        rpt = cf.report
        rpt.add_message("RUNNERENDTIME", timelib.now(), 0)
        rpt.finalize()
        # force close of report and logfile between objects. these are
        # `property` objects and deleting them makes them close and clears the
        # cache.
        del rpt
        del cf.report
        del cf.logfile
        del cf.UI
        del cf.environment
        if cf.has_key("resultsdir"):
            for fname in cf.reportfilenames:
                if not fname.startswith("<"): # a real file, not builtin stdio
                    if os.path.isfile(fname):
                        shutil.move(fname, cf.resultsdir)
            for suffix in ("", ".1", ".2", ".3", ".4", ".5"): # log may have rotated
                fname = cf.logfilename + suffix
                if os.path.isfile(fname):
                    if os.path.getsize(fname) > 0:
                        shutil.move(fname, cf.resultsdir)
                    else:
                        os.unlink(fname)
            # If resultsdir ends up empty, remove it.
            if not os.listdir(cf.resultsdir): # TODO, stat this instead
                os.rmdir(cf.resultsdir)

    def report_global(self):
        """Report common information.
        Send some information to the user interface about the available
        parameters that a user may provide to run a test.
        """
        from pycopia.db import models
        cf = self.config
        ui = cf.UI
        ui.printf("%YAvailable report names for the '%G--reportname=%N' %Yoption%N:")
        ui.print_list(sorted(cf.reports.keys()))
        ui.Print("\n")
        ui.printf("%YAvailable environment names for the '%G--environmentname=%N' %Yoption%N:")
        db = cf.session
        ui.print_list(sorted([env.name for env in db.query(models.Environment).all()]))



def get_module_version(mod):
    try:
        return mod.__version__[1:-1].split(":")[-1].strip()
    except (AttributeError, IndexError): # Should be there, but don't worry if it's not.
        return "unknown"

