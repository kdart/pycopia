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
 publish
 build
 install
 develop
 list

NOTE: install requires sudo to be configured for you.

"""

import sys
import os


PACKAGES = [
"aid",
"utils",
"core",
"CLI",
"debugger",
"process",
"SMI",
"mibs",
"SNMP",
"storage",
"QA",
"net",
"audio",
"XML",
"WWW",
"vim",
]


def _do_commands(name, cmds, root):
    if root:
        sudo = "sudo "
    else:
        sudo = ""
    cmd = "%spython setup.py %s" % (sudo, " ".join(cmds))
    print "======================", cmd, "============================"
    os.chdir(name)
    try:
        os.system(cmd)
    finally:
        os.chdir("..")
        print "====================== END ============================"
        print

def do_sdist(name):
    _do_commands(name, ["sdist"], False)

def do_build(name):
    _do_commands(name, ["build"], False)

def do_list(name):
    print name,

#def do_register(name):
#    _do_commands(name, ["register"], False)

def do_develop(name):
    _do_commands(name, ["develop -s $HOME/bin"], False)

def do_publish(name):
    _do_commands(name, ['egg_info -RDb ""', "sdist", "register", "upload"], False)

def do_egg_info(name):
    _do_commands(name, ['egg_info'], False)

def do_install(name):
    _do_commands(name, ["install"], True)


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
    for name in (argv[2:] or PACKAGES):
        meth(name)
    print
    return 0

sys.exit(main(sys.argv))
