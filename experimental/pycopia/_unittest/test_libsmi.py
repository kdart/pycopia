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
Unit tests the libsmi wrapper.

"""

import os
import qatest

# the library under test
import libsmi

# middle layer class that could contain some common methods
class LIBSMITests(qatest.Test):
    pass

class GetFlagsTest(LIBSMITests):
    def test_method(self):
        flags = libsmi.smiGetFlags()
        self.info(flags)
        return self.passed("got flags")

class SetFlagsTest(LIBSMITests):
    PREREQUISITES = [qatest.PreReq("GetFlagsTest")]
    def test_method(self):
        for flagname in [ 'SMI_FLAG_ERRORS', 'SMI_FLAG_MASK',
                        'SMI_FLAG_NODESCR', 'SMI_FLAG_RECURSIVE',
                        'SMI_FLAG_STATS', 'SMI_FLAG_VIEWALL',]:
            flag = getattr(libsmi, flagname)
            self.info("setting flag %s(%d)" % (flagname, flag))
            libsmi.smiSetFlags(flag)
            flagcheck = libsmi.smiGetFlags()
            self.assert_equal(flag, flagcheck)
        libsmi.smiSetFlags(0)
        self.info(libsmi.smiGetFlags())
        return self.passed("set flags")

class SetErrorLevelTest(LIBSMITests):
    """The smiSetErrorLevel() function sets the pedantic
level (0-9) of the SMI parsers of the SMI library."""
    def test_method(self):
        for level in range(10):
            libsmi.smiSetErrorLevel(level) 
        m = libsmi.smiGetModule("SNMPv2-MIB")
        libsmi.smiSetErrorLevel(0) 
        return self.passed("set error levels")

class GetPathTest(LIBSMITests):
    def test_method(self):
        smipath = libsmi.smiGetPath()
        self.assert_true(len(smipath) > 10) # some arbitrary length
        self.info("Got directories:")
        dirs = smipath.split(os.pathsep)
        for d in dirs:
            self.info(d)
        return self.passed("got path")

class ModuleTest(LIBSMITests):
    """Check that we can fetch a module object. Do some simple verifications.
    Note that we check the organization value and assert it is from the SNMPv2
    working group. That should not be a problem since we only need to test
    standard MIBs.  """
    def test_method(self, mibname):
        m = libsmi.smiGetModule(mibname)
        assert m.name == mibname
        self.info("path: %s" % (m.path,))
        self.info("organization: %s" % (m.organization,))
        #self.info("contactinfo: %s" % (m.contactinfo,))
        self.info("description: %s" % (m.description,))
        self.info("reference: %s" % (m.reference,))
        self.info("language: %s" % (m.language,))
        self.info("conformance: %s" % (m.conformance,))
        return self.passed("got module")

class LoadModuleTest(LIBSMITests):
    def test_method(self, mibname):
        name = libsmi.smiLoadModule(mibname) 
        self.assert_true(name == mibname)
        return self.passed("module %s loaded." % (name,))

class IsLoadedTest(LIBSMITests):
    PREREQUISITES = [qatest.PreReq("LoadModuleTest", "SNMPv2-MIB")]
    def test_method(self, mibname):
        self.assert_true(libsmi.smiIsLoaded(mibname))
        return self.passed("loaded check passed")

# the test suite - The collection of test cases
class libsmiSuite(qatest.TestSuite):
    def initialize(self):
        libsmi.Init("python")
    
    def finalize(self):
        libsmi.smiExit()

def get_suite(cf):
    s = libsmiSuite(cf)
    s.add_test(GetFlagsTest)
    s.add_test(SetFlagsTest)
    s.add_test(SetErrorLevelTest)
    s.add_test(GetPathTest)
    s.add_test(ModuleTest, "SNMPv2-SMI")
    s.add_test(ModuleTest, "SNMPv2-TC")
    s.add_test(ModuleTest, "SNMPv2-CONF")
    s.add_test(ModuleTest, "SNMPv2-MIB")
    s.add_test(ModuleTest, "TCP-MIB")
    s.add_test(LoadModuleTest, "SNMPv2-MIB")
    s.add_test(IsLoadedTest, "SNMPv2-MIB")
    return s


def run(cf):
    s = get_suite(cf)
    s()


if __name__ == "__main__":
    import config
    cf = config.get_config()
    run(cf)

