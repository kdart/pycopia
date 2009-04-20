#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 2009 Keith Dart <keith@kdart.com>
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
CLI interface to Pycopia database storage.

"""

import sys
import os

from pycopia import CLI
from pycopia.db import models


_session = None


class SessionCommands(CLI.BaseCommands):

#'add', 'add_all', 'begin', 'begin_nested', 'clear', 'close', 'commit',
#'delete', 'execute', 'expire', 'expire_all', 'expunge', 'expunge_all',
#'flush', 'get_bind', 'is_modified', 'merge', 'query', 'refresh',
#'rollback', 'save', 'save_or_update', 'scalar', 'update'

    def close(self, argv):
        """close
    Close the database."""
        self._obj.close()
        raise CLI.CommandQuit

    def begin(self, argv):
        """begin
    Begin a transaction."""
        self._obj.begin()

    def commit(self, argv):
        """commit
    Commit edits to the database."""
        self._obj.commit()

    def rollback(self, argv):
        """rollback
    Roll back edits to the database."""
        self._obj.rollback()

    def edit(self, argv):
        """edit <table>
    Edit the given table. Name is class name of mapped table."""
        name = argv[1] 
        t = getattr(models, name)
        cmd = self.clone(TableCommands)
        cmd._setup(t, "%s> " % (name,))
        raise CLI.NewCommand(cmd)

    def ls(self, argv):
        """ls
    List persistent objects."""
        self._print_list(list(models.class_names()))


class TableCommands(CLI.BaseCommands):

    def query(self, argv):
        """query
    Start a query editor."""
        q = _session.query(self._obj)
        cmd = self.clone(QueryCommands)
        cmd._setup(q, "Query:%s> " % (self._obj.__name__,))
        raise CLI.NewCommand(cmd)


class QueryCommands(CLI.BaseCommands):

    def perform(self, argv):
        """run
    Perform the query and show the results."""
        for row in self._obj.all():
            self._print(row)

    def show(self, argv):
        """show
    Show the current SQL."""
        self._print(self._obj.statement)



# main program
def dbcli(argv):
    """dbcli [-?] [<database_url>]

Provides an interactive session to the database.
The argument may be a database URL. If not provide the URL specified on
"storage.conf" is used.

Options:
   -?        = This help text.

"""
    global _session
    from pycopia import getopt

    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "?")
    except getopt.GetoptError:
            print dbcli.__doc__
            return
    for opt, val in optlist:
        if opt == "-?":
            print dbcli.__doc__
            return

    if args:
        database = args[0]
    else:
        from pycopia import basicconfig
        cf = basicconfig.get_config("storage.conf")
        database = cf.database
        del basicconfig, cf

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    cmd = SessionCommands(ui)
    _session = models.get_session(database)
    cmd._setup(_session, "db> ")
    parser = CLI.CommandParser(cmd, 
            historyfile=os.path.expandvars("$HOME/.hist_dbcli"))
    if args:
        for arg in args:
            try:
                parser.parse(arg)
            except KeyboardInterrupt:
                break
    else:
        parser.interact()


