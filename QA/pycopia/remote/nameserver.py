#!/usr/bin/python2
# -*- coding: utf-8 -*-
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

"""
Pycopia instance of Pyro name server.
"""
from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
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
