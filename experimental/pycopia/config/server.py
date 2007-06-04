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
Serves pyNMS configuration as a Pyro object.

"""

import sys, os

import Pyro.core
import Pyro.naming

Pyro.config.PYRO_MULTITHREADED = 0
Pyro.config.PYRO_STORAGE = "/var/tmp"

class ConfigServer(Pyro.core.ObjBase, object):
    pass

def start(cf, name="nmsconfig"):
    
    Pyro.core.initServer(banner=0, storageCheck=0)
    ns = Pyro.naming.NameServerLocator().getNS()

    daemon=Pyro.core.Daemon()
    daemon.useNameServer(ns)

    try:
        ns.unregister(name)
    except:
        pass

    proxy = Pyro.core.ObjBase()
    proxy.delegateTo(cf)

    uri=daemon.connect(proxy, name)
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print "Shutting down."
    daemon.disconnect(proxy)
    daemon.shutdown()

def _test(argv):
    import config
    cf = config.get_config()
    start(cf)

if __name__ == "__main__":
    _test(sys.argv)

