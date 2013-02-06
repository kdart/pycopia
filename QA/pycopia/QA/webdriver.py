#!/usr/bin/python2.7
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 Keith Dart <keith@dartworks.biz>
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
instance and stashes it in the config object.
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


from pycopia.QA import core

CAPS = {
    "firefox": webdriver.DesiredCapabilities.FIREFOX,
    "chrome": webdriver.DesiredCapabilities.CHROME,
    "ie": webdriver.DesiredCapabilities.INTERNETEXPLORER,
}

class WebdriverRemoteSuite(core.TestSuite):
    """Webdriver test suite.

    This suite initializer creates a selenium remote control object. The target
    is the environment's "selenium" role.  Add webdriver test cases to this
    suite. The "webdriver" object will be at the root of the configuration.
    """

    def initialize(self):
        cf = self.config
        target_host = cf.environment.get_role("selenium")
        remote_url = "http://{ip}:4444/wd/hub".format(ip=target_host["hostname"])
        self.info("Remote control URL is: {}".format(remote_url))
        cf.webdriver = webdriver.Remote(remote_url, CAPS[cf.get("browser", "firefox")])

    def finalize(self):
        wd = self.config.webdriver
        del self.config.webdriver
        wd.quit()


class WebdriverSuite(core.TestSuite):
    """Webdriver test suite.

    This suite initializer creates a selenium control object.
    """

    def initialize(self):
        cf = self.config
        profile_dir = cf.userconfig.get("firefox_profile")
        self.info("Firefox profile dir: {}".format(profile_dir))
        profile = webdriver.FirefoxProfile(profile_dir)
        profile.accept_untrusted_certs = True
        cf.webdriver = webdriver.Firefox(profile)

    def finalize(self):
        wd = self.config.webdriver
        del self.config.webdriver
        wd.quit()


