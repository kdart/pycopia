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

    def add(self, argv):
        """add column=value ...
    Add a new row."""
        args, kwargs = CLI.breakout_args(argv[1:], self._environ)
        inst = self._obj(*args, **kwargs)
        _session.add(inst)
        _session.commit()

    def create(self, argv):
        """create
    Start an interactive row creator."""
        cmd = self.clone(CreateCommands)
        cmd._setup(self._obj(), "Create:%s> " % (self._obj.__name__,))
        raise CLI.NewCommand(cmd)


class QueryCommands(CLI.BaseCommands):

    def all(self, argv):
        """all
    Perform the query and show all results."""
        for row in self._obj.all():
            self._print(row)

    def show(self, argv):
        """show
    Show the current SQL."""
        self._print(self._obj.statement)

    def one(self, argv):
        """one
    Get one unique row from query, or throw exception."""
        self._print(self._obj.one())

    def scalar(self, argv):
        """scalar
    Get one unique row from query."""
        self._print(self._obj.one())

    def filter(self, argv):
        """filter
    Apply filters by keyword arguments."""
        args, kwargs = CLI.breakout_args(argv[1:], vars(self._obj))
        self._obj = self._obj.filter_by(**kwargs)

    def count(self, argv):
        """count
    Show the count of the query."""
        self._print(self._obj.count())
        raise CLI.CommandQuit


class CreateCommands(CLI.BaseCommands):

    def set(self, argv):
        """set <name>=<value> ...
    Set the column <name> to <value>."""
        args, kwargs = CLI.breakout_args(argv[1:], self._environ)
        for name, value in kwargs.items():
            setattr(self._obj, name, value)

    def unset(self, argv):
        """unset <name> ...
    Unset the column <name>."""
        for name in argv[1:]:
            delattr(self._obj, name)

    def show(self, argv):
        """show
    Print current object's string."""
        args = argv[1:]
        if args:
            for arg in args:
                self._print(getattr(self._obj, arg))
        else:
            self._print(str(self._obj))

    def commit(self, argv):
        """commit
    Commit the new instance."""
        _session.add(self._obj)
        _session.commit()
        raise CLI.CommandQuit


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


