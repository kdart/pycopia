#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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

"""
An interface for running test cases as unattended suites.
"""

from __future__ import print_function

import os
import logging

from pycopia import getopt
from pycopia.QA import testloader
from pycopia.db import models



SuiteRunnerInterfaceDoc = r"""
Invoke a test suite (TestSuite defined in the database) from a shell. 

You can define a suite in the database, give it a name, and run it given that
name. You may also supply its id value (if you know it). If none are specified
a menu will be presented.

Usage:

    %s [-hd?] suitename...

    Where the arguments are suite names or suite id.

    Options:
        -h -- Print this help text and return.
        -d -- Turn on debugging for tests.
        -D -- Turn on debugging for framework.
        -v -- Increase verbosity.
        -i -- Set flag to run interactive tests.
        -I -- Set flag to skip interactive tests.
        -c or -f <file> -- Merge in extra configuration file.
        -n <string> -- Add a comment to the test report.

    Long-style options are passed into the test suite configuration.
"""


class SuiteRunnerInterface(object):

    def __init__(self, testrunner):
        self.runner = testrunner
        self.dbsession = models.get_session()
        cf = self.runner.config
        cf.flags.DEBUG = 0
        cf.flags.VERBOSE = 0
        cf.flags.INTERACTIVE = False
        cf.userinterfacetype = "none"

    def __del__(self):
        self.dbsession.close()

    def __call__(self, argv):
        """Invoke the suite runner by calling it with argument list.
        """
        cf = self.runner.config
        optlist, extraopts, args = getopt.getopt(argv[1:], "h?dDviIc:f:n:")
        for opt, optarg in optlist:
            if opt in ("-h", "-?"):
                print (SuiteRunnerInterfaceDoc % (os.path.basename(argv[0]),))
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
        cf.arguments = [os.path.basename(argv[0])] + argv[1:]
        cf.argv = args
        self.runner.set_options(extraopts)
        if not args:
            from pycopia import cliutils
            choices = [(row.id, str(row)) for row in models.TestSuite.get_suites(self.dbsession)]
            choices.insert(0, (0, "Skip it"))
            chosen_id = cliutils.choose_key(dict(choices), 0, prompt="Suite? ")
            if chosen_id == 0:
                return
            args = [chosen_id]

        for testsuite in self.get_test_suites(args):
            suite = self.get_suite(testsuite)
            self.runner.initialize()
            self.runner.run_object(suite)
            self.runner.finalize()

    def get_suite(self, dbsuite):
        """Return a runnable and populated test suite from a TestSuite row object."""

        cf = self.runner.config
        suite = testloader.get_suite(dbsuite, cf)

        for dbtestcase in dbsuite.testcases:
            testclass = testloader.get_test_class(dbtestcase)
            if testclass is not None:
                suite.add_test(testclass)

        for subsuite in dbsuite.subsuites:
            suite.add_suite(self.get_suite(subsuite, cf))

        return suite

    def get_test_suites(self, args):
        """Generator that yields valid TestSuite records from the database.
        """
        TS = models.TestSuite
        for suiteid in args:
            try:
                suiteid = int(suiteid)
            except ValueError:
                pass
            try:
                if type(suiteid) is int:
                    suite = self.dbsession.query(TS).get(suiteid)
                else:
                    suite = self.dbsession.query(TS).filter(models.and_(TS.name==suiteid, TS.valid==True)).one()
            except models.NoResultFound:
                logging.warn("No TestSuite with id or name %r" % suiteid)
                continue
            else:
                yield suite


