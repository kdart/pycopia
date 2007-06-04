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
Pyro client for config server.

"""

import sys

import Pyro.core
Pyro.config.PYRO_MULTITHREADED = 0
Pyro.config.PYRO_STORAGE = "/var/tmp"


def get_client(name="nmsconfig"):
    Pyro.core.initClient(banner=0)
    return Pyro.core.getAttrProxyForURI("PYRONAME://%s" % (name,))

def _test(argv):
    cl = get_client()
    print cl.default

if __name__ == "__main__":
    _test(sys.argv)

