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
Test driver for configuration modules.

"""



import qatest
import config

class ConfigTest(qatest.Test):
    def test_method(self):
        assert self.config.this_is_compareme == "compareme", "didn't read test config?"
        try:
            cf = config.get_config()
        except:
            import sys
            ex, val, tb = sys.exc_info()
            self.diagnostic("%s (%s)" % (ex, val))
            return self.failed("can't get config.")
        else:
            return self.passed("successfully fetched configuration.")


def get_suite(cf):
    return ConfigTest(cf)

def run(cf):
    t = get_suite(cf)
    t()

