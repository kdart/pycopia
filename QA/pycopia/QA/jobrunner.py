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
An interface for running test cases as unattended jobs.
"""

import sys
import os

from pycopia import aid
from pycopia import shparser
from pycopia.QA import testloader
from pycopia.db import models



def _parse_parameters(text):

    def _ParserCB(d, argv):
        for param in argv:
            if param.find("=") > 0:
                key, value = param.split("=", 1)
                d[key] = value

    d = {}
    p = shparser.ShellParser(aid.partial(_ParserCB, d))
    p.feed(text)
    p.feed("\n")
    return d


def get_test_jobs(args):
    dbsession = models.get_session()
    TJ = models.TestJob
    for jobid in args:
        try:
            jobid = int(jobid)
        except ValueError:
            pass
        try:
            if type(jobid) is int:
                testjob = dbsession.query(TJ).get(jobid)
            else:
                testjob = dbsession.query(TJ).filter(TJ.name==jobid).one()
        except models.NoResultFound:
            warnings.warn("No TestJob with id %r" % jobid)
            continue
        else:
            yield testjob


class JobRunnerInterface(object):
    """
    """
    def __init__(self, testrunner):
        self.runner = testrunner
        cf = self.runner.config
        cf.flags.DEBUG = 0
        cf.flags.VERBOSE = 0
        cf.flags.INTERACTIVE = False
        cf.userinterfacetype = "none"

    def __call__(self, argv):
        """Invoke the job runner by calling it with argument list.
        """
        cf = self.runner.config

        for testjob in get_test_jobs(argv[1:]):
            if testjob is None:
                continue

            if testjob.parameters:
                params = _parse_parameters(testjob.parameters)
                cf.arguments = testjob.parameters.split()
            else:
                params = {}
            cf.argv = [testjob.suite.name]
            cf.comment = "Automated test job %s(%s)." % (testjob.name, testjob.id)
            cf.environmentname = testjob.environment.name
            cf.reportname = testjob.reportname
            self.runner.set_options(params)

            suite = get_suite(testjob.suite, cf)

            self.runner.initialize()
            self.runner.run_object(suite)
            self.runner.finalize()


def get_suite(dbsuite, config):

    suite = testloader.get_suite(dbsuite, config)

    for dbtestcase in dbsuite.testcases:
        testclass = testloader.get_test_class(dbtestcase)
        if testclass is not None:
            suite.add_test(testclass)

    for subsuite in dbsuite.subsuites:
        suite.add_suite(get_suite(subsuite, config))

    return suite

