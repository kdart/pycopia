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
Pycopia instance of Pyro name server.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys

# Must be before Pyro4 import, even if not used here.
import logging
import logging.config

logging.config.fileConfig("/etc/pycopia/logging.cfg")


import Pyro4
from Pyro4 import naming

# Pyro config is still weird.
def set_p4_config():
    from pycopia import basicconfig
    p4conf = basicconfig.get_config("pyro4.conf")
    pcf = Pyro4.config
    for name in pcf.__slots__:
        setattr(pcf, name, p4conf.get(name, getattr(pcf, name)))
    # name server specific overrides
    pcf.DOTTEDNAMES = False
set_p4_config()
del set_p4_config


_DOC = """qanameserverd [-nh?]

Starts the name server daemon (QA object broker).

Where:
    -n = Do NOT run as a daemon, but stay in foreground.

"""

def qanameserverd(argv):
    import getopt
    do_daemon = True
    try:
        optlist, args = getopt.getopt(argv[1:], "nh?")
    except getopt.GetoptError:
        print(_DOC)
        sys.exit(2)

    for opt, optarg in optlist:
        if opt in ("-h", "-?"):
            print(_DOC)
            return
        elif opt == "-n":
            do_daemon = False

    if do_daemon:
        from pycopia import daemonize
        daemonize.daemonize()

    naming.startNSloop()


if __name__ == "__main__":
    from pycopia import autodebug
    qanameserverd(["qanameserverd", "-n"])
