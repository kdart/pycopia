#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 and onwards, Keith Dart <keith@dartworks.biz>
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
CLI wrapper for SSL and CA activities.

TODO

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia.ssl import certs
from pycopia import CLI


class SSLCommands(CLI.BaseCommands):
    pass


class CertsCommands(CLI.BaseCommands):
    pass


def sslcli(argv):
    b"""sslcli [-?D]
Provides an interactive CLI for managing SSL certificates and CA operations.

Options:
   -?        = This help text.
   -D        = Debug on.
    """
    import os
    import getopt

    try:
        optlist, args = getopt.getopt(argv[1:], b"?hD")
    except getopt.GetoptError:
        print (sslcli.__doc__)
        return
    for opt, val in optlist:
        if opt in (b"-?", b"-h"):
            print (sslcli.__doc__)
            return
        elif opt == b"-D":
            from pycopia import autodebug

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    ui._env[b"PS1"] = b"SSL> "
    cmd = SSLCommands(ui)
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars(b"$HOME/.hist_sslcli"))
    parser.interact()


if __name__ == "__main__":
    import sys
    sslcli(sys.argv)
