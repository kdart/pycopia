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

"""

# $Id$

import sys
import qatest

import termtools
import terminal
import ANSIterm

import proctools

# A common base class for all tests in a module is useful for common helper
# methods.
class ANSITermBaseTest(qatest.Test):
    pass

class ANSITermTest(ANSITermBaseTest):
    def test_method(self):
        fo = open("termtest1.txt")
        term = ANSIterm.get_ansiterm(NULL)
        for line in fo.readlines():
            t = eval(line) # remove quotes, expand escapes
            # cheating - not the usual interface
            term.fsm.process_string(t)
        fo.close()
        print term
        return self.passed("no exceptions.")

# this is an interactive test
class VTTest(ANSITermBaseTest):
    def initialize(self):
        pm  = proctools.get_procmanager()
        proc = pm.spawnpty("vttest")
        self.term = ANSIterm.get_ansiterm(proc, 24, 80, terminal.ReprPrinter(sys.stdout))
        self.term.printer.set_file(self.config.logfile)

    def test_method(self):
        fd = sys.stdin.fileno()
        mode = termtools.tcgetattr(fd)
        try:
            while 1:
                print self.term
                c = sys.stdin.read(1)
                try:
                    self.term.write(c)
                except EOFError:
                    termtools.tcsetattr(fd, termtools.TCSANOW, mode)
                    return self.passed("vttest finished")
        finally:
            termtools.tcsetattr(fd, termtools.TCSANOW, mode)

    def finalize(self):
        #self.term.close()
        del self.term

class InteractiveTest(ANSITermBaseTest):
    def initialize(self):
        pm  = proctools.get_procmanager()
        proc = pm.spawnpty("cat")
        self.term = ANSIterm.get_ansiterm(proc, 24, 80, terminal.ReprPrinter(sys.stdout))
        self.term.printer.set_file(self.config.logfile)

    def test_method(self):
        fd = sys.stdin.fileno()
        mode = termtools.tcgetattr(fd)
        try:
            while 1:
                print self.term
                c = termtools.get_key()
                if c == "q":
                    break
                self.term.fsm.process_string(c)
        finally:
            termtools.tcsetattr(fd, termtools.TCSANOW, mode)
        return self.passed(" finished")

    def finalize(self):
        del self.term

####### suite ###############
class ANSITermSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = ANSITermSuite(conf)
    suite.add_test(ANSITermTest)
    suite.add_test(InteractiveTest)
    suite.add_test(VTTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


