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
Base class for webdriver test suites. Pre-instantiates a webdriver
instance and fetches the DUT service target.
"""

from selenium import webdriver

from pycopia.QA import core

CAPS = {
    "firefox": webdriver.DesiredCapabilities.FIREFOX,
    "chrome": webdriver.DesiredCapabilities.CHROME,
    "ie": webdriver.DesiredCapabilities.INTERNETEXPLORER,
}

class WebdriverSuite(core.TestSuite):
    """Webdriver test suite. 

    Add webdriver test cases to this suite. The "webdriver" object will be
    at the root of the configuration.
    """

    def initialize(self):
        cf = self.config
        target_host = cf.environment.get_role("selenium")
        target_url = cf.environment.DUT.get_url(cf.get("serviceprotocol"), 
                cf.get("servicepath"))
        remote_url = "http://{ip}:4444/wd/hub".format(ip=target_host["hostname"])
        self.info("Remote URL is: %s" % (remote_url,))
        self.info("Target URL is: %s" % (target_url,))
        cf.webdriver = webdriver.Remote(remote_url,
                CAPS[cf.get("browser", "firefox")])
        cf.webdriver.get(target_url)

    def finalize(self):
        wd = self.config.webdriver
        del self.config.webdriver
        wd.quit()


