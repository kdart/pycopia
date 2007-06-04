#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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
Master builder (custom script).

Commands:
 sdist
 register
 publish

"""

import sys
import os


PACKAGES = [
"aid",
"core",
"CLI",
"debugger",
"process",
"utils",
"vim",
"mibs",
"SMI",
"SNMP",
"storage",
"QA",
"net",
"audio",
"XML",
"WWW",
]


def _do_commands(name, cmds):
    os.chdir(name)
    try:
        os.system("python setup.py %s" % (" ".join(cmds),))
    finally:
        os.chdir("..")


def do_sdist(name):
    _do_commands(name, ["sdist"])

def do_register(name):
    _do_commands(name, ["register"])

def do_publish(name):
    _do_commands(name, ["sdist", "upload"])


def main(argv):
    try:
        cmd = argv[1]
    except IndexError:
        print __doc__
        return 1
    try:
        meth = globals()["do_" + cmd]
    except KeyError:
        print __doc__
        return 2
    for name in PACKAGES:
        meth(name)
    return 0

sys.exit(main(sys.argv))
