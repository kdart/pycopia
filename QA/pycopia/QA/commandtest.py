#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@kdart.com>

"""
Module commandtest runs external commands, provides inputs, and checks outputs.

"""

from pycopia.QA import core
from pycopia import proctools


class TestCondition(object):
    """TestCondition holds test data for use by the test_command function.
Attributes are:

    - cmdline 
    - stdin 
    - expectedout 
    - expectederr 
    - expectedexit 
    - environ
    """
    __slots__ = ('cmdline', 'stdin', 'expectedout', 
                'expectederr', 'expectedexit', 'environ')
    def __init__(self, cmdline=None, environ=None, stdin=None, expectedout=None, expectederr=None, expectedexit=0):
        self.cmdline = cmdline
        self.stdin = stdin # what to write to programs stdin
        self.expectedout=expectedout # what is expected to come out
        self.expectederr=expectederr
        self.expectedexit=expectedexit # expected errorlevel value
        self.environ = environ # environment program will run with.

    def __repr__(self):
        return "%s(%r, %r, %r, %r, %r, %r)" % (self.__class__.__name__, 
            self.cmdline, self.environ, self.stdin, self.expectedout, 
            self.expectederr, self.expectedexit)

    def get_attributes(self):
        return self.__slots__


class CommandTest(core.Test):

    def run_command(self, ctx):
        """run_command(testcondition)
        Runs command and tests responses as defined by the TestCondition.
        """
        cmdline = ctx.cmdline
        stdin = ctx.stdin
        expectedout = ctx.expectedout
        expectederr = ctx.expectederr
        expectedexit = ctx.expectedexit
        environ = ctx.environ

        if expectederr:
            mergeerr = 0
        else:
            mergeerr = 1
        self.info("running: %s" % cmdline)
        p = proctools.spawnpipe(cmdline, env=environ, merge=mergeerr)
        if stdin:
            p.write(stdin)
        if expectedout:
            output = p.read()
        if expectederr:
            errors = p.readerr()
        p.wait()
        es = p.exitstatus
        if int(es) != expectedexit:
            return self.failed("bad exit value: expected %d, got %d" % (expectedexit, int(es)))

        if expectedout and (output != expectedout):
            return self.failed("bad output: %r" % (output))

        if expectederr and (errors != expectederr):
            return self.failed("bad error output: %r" % (errors))

        return self.passed("no errors")

    # default test case, may be overridden in a subclass.
    # remember to call the instance, not this method.
    execute = run_command


def get_suite(cf):
    suite = core.TestSuite()
    suite.add_test(CommandTest)
    return suite

def run(cf):
    suite = get_suite(cf)
    suite()

