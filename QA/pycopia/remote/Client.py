#!/usr/bin/python2.7
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

"""
The Client for Remote controllers.

"""
__all__ = ["get_remote", "remote_copy", "get_controller"]

import sys, os

from pycopia.remote import pyro


# some platform specific stuff. Should be minimal
if sys.platform.startswith("linux"):
    from pycopia.remote.PosixClient import *

elif sys.platform == "cygwin":
    from pycopia.remote.PosixClient import *

elif sys.platform == "win32":
    from pycopia.remote.WindowsClient import *
del sys


class ProxyError(pyro.PyroError):
    pass


def get_remote(hostname, servicename=None):
    return pyro.get_remote(hostname, servicename)


def remote_copy(agent, remfile, dst):
    """Copies a file from the remote agent to the local file system."""
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


def get_controller(equipment, logfile=None, servicename="PosixAgent"):
    client = get_remote(equipment["hostname"], servicename)
    if logfile:
        logfile.write("Got remote.Client %s\n" % (client,))
    return client


if __name__ == "__main__":
    rem = get_remote("localhost", "PosixAgent")

