#!/usr/bin/python2.5
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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

"""
Base class for selenium test suites. Simplifies running selenium tests.
Note that you should have a "selenium" section defined in the
configuration. You can add this with the dbcli tool:

    $ dbcli
    db> config
    Config:root> mkdir selenium
    Config:root> cd selenium
    Config:root.selenium> set host "localhost"
    Config:root.selenium> set port 4444
    Config:root.selenium> set browser "*firefox"

"""

from selenium import selenium

from pycopia.QA import core


class SeleniumSuite(core.TestSuite):
    """Selenium test suite. 

    Add selenium test cases to this suite. The "selenium" object will be
    at the root of the configuration.
    """

    def initialize(self):
        cf = self.config
        target_url = cf.environment.DUT.get_url(cf.get("serviceprotocol"), cf.get("servicepath"))
        selenium_server = cf.environment.selenium["hostname"]
        cf.selenium = selenium(
                selenium_server,
                cf.selenium.port,
                cf.selenium.browser,
                target_url,
        )
        cf.selenium.start()

    def finalize(self):
        sel = self.config.selenium
        del self.config.selenium
        sel.stop()


