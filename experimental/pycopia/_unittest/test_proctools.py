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
Test the proctools module.

"""

import qatest

import proctools

class ProctoolsBaseTest(qatest.Test):
    pass

# XXX
class ProctoolsLSTest(ProctoolsBaseTest):
    def test_method(self):
        self.info("**** normal 'ls' test")
        ls = proctools.spawnpipe("ls /usr/bin")
        self.info(ls.stat())
        files = ls.read()
        self.assert_true(files)
        self.verboseinfo(repr(files))
        self.info("errors:")
        self.assert_false(ls.readerr())
        ls.close()
        es = ls.stat()
        if es: # ExitStatus
            return self.passed(es)
        else:
            return self.failed(es)

class ProctoolsLSErrorsTest(ProctoolsBaseTest):
    def test_method(self):
        self.info("***** ls with errors ")
        ls = proctools.spawnpipe("ls /usr/binxx", merge=0)
        self.info("output:")
        self.info(ls.read())
        self.info("errors:")
        self.info(ls.readerr())
        ls.close()
        ls.wait()
        es = ls.stat()
        if es: # should be abnormal exit
            self.diagnostic(es)
            return self.failed("normal exit.")
        else:
            return self.passed("'ls' exited abnormally as expected.")

class ReadlineTest(ProctoolsBaseTest):
    def test_method(self):
        self.info("**** readline test")
        lspm = proctools.spawnpipe("ls /bin")
        lines = lspm.readlines()
        self.assert_true(lines)
        self.info(lspm.exitstatus)
        lspm.close()
        es = lspm.stat()
        if es:
            return self.passed(es)
        else:
            return self.failed(es)

class PipelineTest(ProctoolsBaseTest):
    def test_method(self):
        ptest = proctools.spawnpipe("cat /etc/hosts | sort")
        hosts = ptest.read()
        self.assert_true(hosts)
        self.assert_false(ptest.readerr())
        ptest.close()
        es = ptest.stat()
        if es:
            return self.passed(es)
        else:
            return self.failed(es)

def _sub_function():
    import scheduler
    scheduler.sleep(5)
    return None

def _co_function():
    import sys, scheduler
    sys.stdout.write("hello from co_function\n")
    scheduler.sleep(5)
    return None

class BasicSubProcessTest(ProctoolsBaseTest):
    def test_method(self):
        sub = proctools.subprocess(_sub_function)
        self.info("childpid: %s (will exit in 5 seconds)" % (sub.childpid,))
        es = sub.wait()
        if es:
            return self.passed("subprocess started and exited")
        else:
            self.diagnostic(es)
            return self.failed("subprocess failed.")

class BasicCoProcessTest(ProctoolsBaseTest):
    def test_method(self):
        sub = proctools.coprocess(_co_function)
        self.info("childpid: %s (will exit in 5 seconds)" % (sub.childpid,))
        line = sub.readline()
        es = sub.wait()
        if es:
            if line == "hello from co_function\r\n": # CR added by pty
                return self.passed("coprocess started and exited")
            else:
                self.diagnostic(repr(line))
                return self.failed("bad string returned.")
        else:
            self.diagnostic(es)
            return self.failed("coprocess failed.")


### suite ###
class ProctoolsSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = ProctoolsSuite(conf)
    suite.add_test(ProctoolsLSTest)
    suite.add_test(ProctoolsLSErrorsTest)
    suite.add_test(ReadlineTest)
#   suite.add_test(PipelineTest)
    suite.add_test(BasicSubProcessTest)
    suite.add_test(BasicCoProcessTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()

