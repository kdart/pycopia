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
Pycopia name server control module.
"""
from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division


from pycopia.remote import pyro


def print_listing(listing):
    for name, uri in sorted(listing.items()):
        if len(uri) > 45:
            print("{:>35.35s} --> \n{:>79.79s}".format(name, uri))
        else:
            print("{:>35.35s} --> {}".format(name, uri))


_DOC = """nsc [-h?]

Control or query the name server.

Subcommands:
    list - show current objects.
    ping - No error if server is reachable.
    remove <name> - remove the named agent entry.

"""

def nsc(argv):
    import getopt
    try:
        optlist, args = getopt.getopt(argv[1:], "h?")
    except getopt.GetoptError:
        print(_DOC)
        return 2

    for opt, optarg in optlist:
        if opt in ("-h", "-?"):
            print(_DOC)
            return

    try:
        subcmd = args[0]
    except IndexError:
        print(_DOC)
        return 2

    args = args[1:]
    nameserver = pyro.locate_nameserver()
    if subcmd.startswith("li"):
        if args:
            print_listing(nameserver.list(prefix=args[0]))
        else:
            print_listing(nameserver.list())
    elif subcmd.startswith("pi"):
        nameserver.ping()
        print("Name server is alive.")
    if subcmd.startswith("rem"):
        if args:
            nameserver.remove(name=args[0])
        else:
            print(_DOC)
            return 2


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    nsc(sys.argv)

