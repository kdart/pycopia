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
Test the xfce4 menu generation.

"""


import os
import qatest
from cStringIO import StringIO

import XML.POM as POM

import XML.xfce4 as xfce4

def pretty_string(obj):
    fo = StringIO()
    pp = POM.BeautifulWriter(fo)
    obj.emit(pp)
    s = fo.getvalue()
    return s


class XFCEMenuBaseTest(qatest.Test):
    pass

class NewMenuTest(XFCEMenuBaseTest):
    def test_method(self):
        menu = xfce4.new_menu()
        menu.add_title(name="My Title")
        self.info("\n%s" % (pretty_string(menu),))
        return self.passed("Got new menu")


class OpenMenuTest(XFCEMenuBaseTest):
    def test_method(self):
        menu = xfce4.open_menu("%s/.config/xfce4/desktop/menu.xml" % (os.environ["HOME"],))
        self.info("\n%s" % (pretty_string(menu),))
        assert type(menu.root) is xfce4.dtds.xfdesktop_menu.Xfdesktop_menu
        assert type(menu.root["separator"]) is xfce4.dtds.xfdesktop_menu.Separator
        return self.passed("Got existing menu")

class XFCEMenuSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = XFCEMenuSuite(conf)
    suite.add_test(NewMenuTest)
    suite.add_test(OpenMenuTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()


