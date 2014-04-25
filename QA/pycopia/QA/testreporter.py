#!/usr/bin/python2
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""
Report on tests, and maintain database synchronization.
"""

import sys
import os

from pycopia import methods
from pycopia.db import models
from pycopia.QA import core
from pycopia.QA import testinspector

ModuleType = type(sys)
TypeType = type


class TestReporterError(Exception):
    pass


REPORT_MODULE="""
Test module named "{name}",
code loaded from file {file}.  """

REPORT_TESTSUITE = """
A test suite object {objname}, from module "{module}", named "%Y{name}%N", """

REPORT_TEST = """
A test named {module}.%y{name}%N.
The execute method signature is '{sig}'.
It may be added to a suite like this:
    suite.add_test({name}, {args})"""

REPORT_CLASS = """
A class {module}.%g{name}%N,
The file where it is defined is {file}.  """

REPORT_GLOBAL = """
The base directory where test run artifacts are placed is {resultsdirbase!r}.
The base of the URL where a web browser may access them is {baseurl!r}.
The 'documentroot' value, where other web pages are placed, is {documentroot!r}.
"""


class TestReporter(object):
    """Reports on test objects.

    The style is similar to a test runner, but instead of running runnable
    objects it reports on them to the userinterface object.
    """
    def __init__(self, config):
        self.config = config
        config.username = os.environ["USER"]

    def report_global(self):
        """Report common information.
        Send some information to the user interface about the available
        parameters that a user may provide to run a test.
        """
        cf = self.config
        db = cf.session
        ui = cf.UI
        ui.printf("%YAvailable report names for the '%G--reportname=%N' %Yoption%N:")
        ui.print_list(sorted(cf.reports.keys()))
        ui.Print("\n")
        ui.printf("%YAvailable environment names for the '%G--environmentname=%N' %Yoption%N:")
        ui.print_list(sorted([env.name for env in db.query(models.Environment).all()]))
        ui.printf(REPORT_GLOBAL.format(
                resultsdirbase=cf.get("resultsdirbase"),
                baseurl=cf.get("baseurl"),
                documentroot=cf.get("documentroot"),
            ))


    def report_objects(self, objects):
        for obj in objects:
            objecttype = type(obj)
            if objecttype is ModuleType and hasattr(obj, "run"):
                self.report_module(obj)
            elif objecttype is TypeType and issubclass(obj, core.Test):
                self.report_test(obj)
            elif objecttype is TypeType and hasattr(obj, "run"):
                # A bare class uses as a subcontainer of test or suite
                # constructor, typically a UseCase class.
                self.report_class(obj)
            elif isinstance(obj, core.TestSuite):
                self.report_testsuite(obj)
            else:
                self.config.UI.warning("{!r} is not a runnable object.".format(obj))

    def report_tests(self, testcaselist):
        for tc in testcaselist:
            self.report_test(tc)
            self.config.UI.Print("\n")

    def report_errors(self, errlist):
        ui = self.config.UI
        ui.error('Some modules failed to load.')
        for err in errlist:
            ui.Print("  ", err)

    def report_module(self, mod):
        ui = self.config.UI
        ui.printf(REPORT_MODULE.format(name=mod.__name__, file=mod.__file__))
        ui.Print("This module defines the following test cases.")
        clsdict = testinspector.find_classes(mod.__name__, findall=False)
        for name, params in clsdict.items():
            ui.printf("  %y{name}%N {using}".format(name=name, using="with config parameters:" if params else "using no config parameters."))
            if params:
                for var, cname, defaultval in params:
                    ui.Print('    variable "{var}" is "{cname}" from the config, default value is {default!r}'.format(
                        var=var,
                        cname=cname,
                        default=defaultval,
                        ))
        if self.config.flags.VERBOSE:
            if hasattr(mod, "get_suite"):
                ui.Print("This module builds the following test suite.")
                suite = mod.get_suite(self.config)
                self.report_testsuite(suite)
            else:
                ui.Print("No get_suite function in this module.")

    def report_class(self, usecase):
        ui = self.config.UI
        ui.printf(REPORT_CLASS.format(name=usecase.__name__, module=usecase.__module__,
                file=sys.modules[usecase.__module__].__file__))
        if hasattr(usecase, "get_suite"):
            ui.Print("It has a suite constructor (method named 'get_suite').")
            if self.config.flags.VERBOSE:
                ui.Print("It returns:")
                suite = usecase.get_suite(self.config)
                self.report_testsuite(suite)
        else:
            ui.Print("Some class that we don't know what to do with.")

    def report_testsuite(self, suite, level=1):
        ui = self.config.UI
        indent = "  " * level
        cls = suite.__class__
        ui.printf(REPORT_TESTSUITE.format(objname=cls.__name__, name=suite.test_name, module=cls.__module__))
        ui.Print("  "*(level-1), "Suite has the following test cases added.")
        for tcentry in suite:
            ui.Print(indent, repr(tcentry))
            if isinstance(tcentry, core.SuiteEntry):
                ui.Print(indent, "Nested suite:")
                self.report_testsuite(tcentry.inst, level+1)

    def report_test(self, testcase):
        ui = self.config.UI
        exm = getattr(testcase, "execute")
        sig = methods.MethodSignature(exm)
        ui.printf(REPORT_TEST.format(
                name=testcase.__name__,
                module=testcase.__module__,
                sig=sig,
                args=", ".join(map(str, sig.args)+map(lambda t: "%s=%r" % t, sig.kwargs.items())),
        ))
        params = testinspector.get_class(testcase)
        if params:
            ui.Print("  parameters from config:")
            for var, cname, defaultval in params:
                ui.Print('    variable "{var}" is "{cname}" from the config, default value is {default!r}'.format(
                    var=var,
                    cname=cname,
                    default=defaultval,
                    ))
        else:
            ui.Print("  no config parameters used.")




