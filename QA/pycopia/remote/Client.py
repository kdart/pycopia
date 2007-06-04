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
The Client for Remote controllers.

"""
__all__ = ["get_remote", "remote_copy"]

import sys, os

import Pyro.util
import Pyro.core

from pycopia import basicconfig
cf = basicconfig.get_config("remote.conf")
Pyro.config.PYRO_NS_HOSTNAME = cf.nameserver
del cf, basicconfig

# some platform specific stuff. Should be minimal
if sys.platform == "linux2":
    from pycopia.remote.PosixClient import *

elif sys.platform == "cygwin":
    from pycopia.remote.PosixClient import *

elif sys.platform == "win32":
    from pycopia.remote.WindowsClient import *
del sys


def get_remote(name):
    Pyro.core.initClient(banner=0)
    if "." in name: # only use base name for agent name
        name =  name.split(".")[0]
    myname = ":Client.%s" % (name,)
    return Pyro.core.getProxyForURI("PYRONAME://%s" % (myname,))


def remote_copy(agent, remfile, dst):
    "Copies a file from the remote agent to the local file system."
    h = agent.fopen(remfile, "rb")
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(remfile))
    dest = open(dst, "wb")
    while 1:
        data = agent.fread(h, 1024)
        if not data:
            break
        dest.write(data)
    dest.close()
    agent.fclose(h)


