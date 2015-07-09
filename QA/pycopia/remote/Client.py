#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

