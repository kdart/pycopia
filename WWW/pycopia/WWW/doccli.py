#!/usr/bin/python2.5
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Interactive document builder.

"""

import os

from pycopia import getopt
from pycopia.XML import POM
from pycopia.WWW import XHTML
from pycopia import CLI


class TopLevel(CLI.GenericCLI):

    def write(self, argv):
        """write <filename>
    Write current document model to a file."""
        if not self._environ["filename"]:
            fname = argv[1]
        else:
            fname = self._environ["filename"]
        fo = open(fname, "w")
        try:
            self._obj.emit(fo)
        finally:
            fo.close()

    def show(self, argv):
        """show
    Show current document object."""
        bw = POM.BeautifulWriter(self._ui)
        self._obj.emit(bw)

    def edit(self, argv):
        """edit <path>
    Enter in interactive command on the node given by <path>."""
        path = argv[1]
        node = self._obj.get_path(path)
        cmd = self.clone(NodeCommands)
        cmd._setup(node, "%s> " % (path,))
        raise CLI.NewCommand, cmd


class NodeCommands(CLI.GenericCLI):

    def write(self, argv):
        """write <filename>
    Write this node and children to a file."""
        fname = argv[1]
        fo = open(fname, "w")
        try:
            self._obj.emit(fo)
        finally:
            fo.close()

    def show(self, argv):
        """show
    Show current document object."""
        bw = POM.BeautifulWriter(self._ui)
        self._obj.emit(bw)



def doccli(argv):
    """doccli [-h?] [-D] [<filename>]
    Create and interactively edit an XHTML document.
    """
    filename = None
    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "?hD")
    except getopt.GetoptError:
        print doccli.__doc__
        return
    for opt, optarg in optlist:
        if opt in ("-?", "-h"):
            print doccli.__doc__
            return
        elif opt == "-D":
            from pycopia import autodebug
    if args:
        filename = args[0]

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    cmd = TopLevel(ui)
    cmd._environ["filename"] = filename
    if filename:
        doc = XHTML.get_document(filename)
    else:
        doc = XHTML.new_document()
    cmd._setup(doc, "doc> ")
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_doccli"))
    parser.interact()

