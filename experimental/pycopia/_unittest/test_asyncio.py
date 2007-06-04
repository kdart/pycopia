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
Test asyncio methods. 

"""

import os
import qatest
import scheduler

import asyncio

class AsyncIOBaseTest(qatest.Test):
    pass

class GetPoller(AsyncIOBaseTest):
    def test_method(self):
        poller = asyncio.get_poller()
        assert poller is asyncio.poller
        return self.passed("Successfully fetched poller.")

class GetAsyncManager(AsyncIOBaseTest):
    def test_method(self):
        mgr = asyncio.get_manager()
        assert mgr is asyncio.manager
        return self.passed("Successfully fetched SIGIO manager.")


# helper for testing DirectoryNotifier object.
class DirectoryNotifyTester(asyncio.DirectoryNotifier):

    def initialize(self):
        self.added = []
        self.removed = []
        self.no_change_called = 0

    def entry_added(self, added):
        self.added = added

    def entry_removed(self, removed):
        self.removed = removed

    def no_change(self):
        self.no_change_called = 1


class DirectoryNotifyAddTest(AsyncIOBaseTest):
    def test_method(self):
        cwd = os.getcwd()
        if os.path.isfile("newfile.txt"): # remove possible leftover
            unlink("newfile.txt")
        # the the directory notifier and register it
        dn = DirectoryNotifyTester(cwd)
        manager = asyncio.get_manager()
        self.config.dirhandle = manager.register(dn)
        # create a new file. The directory notifier (dn) will store the name.
        open("newfile.txt", "w").write("testing\n")
        self.info("added files: %s" %(dn.added,))
        # give it all time to work
        self.config.sched.sleep(2)
        # test some assertions. we should have add one file.
        assert len(dn.added) == 1
        assert "newfile.txt" == dn.added[0]
        return self.passed("passed all assertions")

class DirectoryNotifyRemoveTest(AsyncIOBaseTest):
    PREREQUISITES = [qatest.PreReq("DirectoryNotifyAddTest")]
    def test_method(self):
        manager = asyncio.get_manager()
        os.unlink("newfile.txt")
        self.config.sched.sleep(2)
        dn = manager.get(self.config.dirhandle)
        self.info("removed files: %s" %(dn.removed,))
        manager.unregister(self.config.dirhandle)
        assert len(dn.removed) == 1
        assert "newfile.txt" == dn.removed[0]
        del dn
        return self.passed("passed all assertions")


class BasicFileWriteTest(AsyncIOBaseTest):
    def test_method(self):
        fo = asyncio.FileWrapper(file("testwrite.txt", "w"))
        fo.write("testing\n")
        fo.close()
        return self.passed("opened file for write")

class BasicFileReadTest(AsyncIOBaseTest):
    PREREQUISITES = [qatest.PreReq("BasicFileWriteTest")]
    def test_method(self):
        fo = asyncio.FileWrapper(file("testwrite.txt", "w"))
        fo.write("testing\n")
        fo.close()
        return self.passed("opened file for write")

####### suite
class AsyncIOSuite(qatest.TestSuite):
    def initialize(self):
        self.config.sched = scheduler.get_scheduler()
    
    def finalize(self):
        self.config.sched = None


def get_suite(conf):
    suite = AsyncIOSuite(conf)
    suite.add_test(GetPoller)
    suite.add_test(GetAsyncManager)
    suite.add_test(DirectoryNotifyAddTest)
    suite.add_test(DirectoryNotifyRemoveTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()

