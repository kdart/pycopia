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

import os

from pycopia import CLI
from pycopia import tty
from pycopia import passwd
from pycopia.aid import NULL

from pycopia.db import models
from pycopia.db import config

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

_session = None


class SessionCommands(CLI.BaseCommands):

#'add', 'add_all', 'begin', 'begin_nested', 'clear', 'close', 'commit',
#'delete', 'execute', 'expire', 'expire_all', 'expunge', 'expunge_all',
#'flush', 'get_bind', 'is_modified', 'merge', 'query', 'refresh',
#'rollback', 'save', 'save_or_update', 'scalar', 'update'

    def initialize(self):
        tables = list(models.class_names())
        self.add_completion_scope("use", tables)
        self.add_completion_scope("edit", tables)

    def close(self, argv):
        """close
    Close the database."""
        self._obj.close()
        raise CLI.CommandQuit

    def finalize(self):
        if bool(self._obj.dirty):
            if self._ui.yes_no("Changes have been made. Commit?"):
                self._obj.commit()
            else:
                self._obj.rollback()

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

    def use(self, argv):
        """use <table>
    Use the given table. Name is class name of mapped table."""
        name = argv[1] 
        t = getattr(models, name)
        cls = _EDITOR_MAP.get(name, TableCommands)
        cmd = self.clone(cls)
        cmd._setup(t, cls.get_prompt(t))
        raise CLI.NewCommand(cmd)

    edit = use # alias

    def ls(self, argv):
        """ls
    List persistent objects."""
        self._print_list(list(models.class_names()))

    def config(self, argv):
        """config
    Enter configuration table edit mode."""
        root = config.get_root(self._obj)
        cmd = self.clone(ConfigCommands)
        cmd._setup(root, "%%YConfig%%N:%s> " % (root.name,))
        raise CLI.NewCommand(cmd)

    def network(self, argv):
        """network
    Enter network configuration mode."""
        cmd = self.clone(NetworkCommands)
        cmd._setup(None, "%BNetwork%N> ")
        raise CLI.NewCommand(cmd)


class RowCommands(CLI.GenericCLI):

    @classmethod
    def get_prompt(cls, dbrow):
        cls._metadata = sorted(models.get_metadata(dbrow.__class__))
        return "%%I%s%%N:%s> " % (dbrow.id, dbrow)

    def show(self, argv):
        """show
    show the selected rows data."""
        for metadata in RowCommands._metadata:
            self._print("%20.20s: %s" % (metadata.colname, getattr(self._obj, metadata.colname)))



class TableCommands(CLI.BaseCommands):

    @classmethod
    def get_prompt(cls, table):
        return "%%B%s%%N> " % table.__name__

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

    def ls(self, argv):
        """ls [--<attribute>=<criteria>...]
    List all current entries."""
        opts, longopts, args = self.getopt(argv, "")
        q = _session.query(self._obj)
        for k, v in longopts.iteritems():
            q = q.filter(getattr(self._obj, k) == v)
        for item in q.all():
            self._print(item.id, ":", item)

    def describe(self, argv):
        """describe
    Desribe the table columns."""
        for metadata in sorted(models.get_metadata(self._obj)):
            self._print("%20.20s: %s (%s)" % (
                    metadata.colname, metadata.coltype, metadata.default))

    def edit(self, argv):
        """edit <id>
    Edit a row object from the table."""
        rowid = int(argv[1])
        dbrow = _session.query(self._obj).get(rowid)
        cls = RowCommands
        cmd = self.clone(cls)
        cmd._setup(dbrow, cls.get_prompt(dbrow))
        raise CLI.NewCommand(cmd)

    def show(self, argv):
        """show <id>
    show the row with the given id."""
        rowid = int(argv[1])
        dbrow = _session.query(self._obj).get(rowid)
        for metadata in sorted(models.get_metadata(self._obj)):
            self._print("%20.20s: %s" % (metadata.colname, getattr(dbrow, metadata.colname)))


class NetworkCommands(CLI.BaseCommands):
    pass
# TODO network connections

class UserCommands(TableCommands):

    @classmethod
    def get_prompt(cls, table):
        return "%%R%s%%N> " % table.__name__

    def add(self, argv):
        """add [--first_name=<firstname> --last_name=<lastname>] <username>
    Add a new user to the database."""
        args, kwargs = CLI.breakout_args(argv[1:], self._environ)
        username = args[0]
        try:
            pwent = passwd.getpwnam(username)
        except KeyError:
            pass
        else:
            models.create_user(_session, pwent)
            return
        grp = _session.query(models.Group).filter(models.Group.name=="testing").one()
        kwargs["username"] = username
        kwargs["authservice"] = "local"
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_superuser", False)
        if "first_name" not in kwargs:
            kwargs["first_name"] = self._user_input("First Name? ")
        if "last_name" not in kwargs:
            kwargs["last_name"] = self._user_input("Last Name? ")
        user = models.create(models.User, **kwargs)
        user.groups = [grp]
        _session.add(user)
        _session.commit()

    def passwd(self, argv):
        """passwd [-a <authservice> | -l | -s ] <username>
    Change the password for the given user. Also change the authorization method."""
        opts, longopts, args = self.getopt(argv, "a:sl")
        for opt, arg in opts:
            if opt == "-a":
                longopts["authservice"] = arg
            elif opt == "-l":
                longopts["authservice"] = "local"
            elif opt == "-s":
                longopts["authservice"] = "system"
        username = args[0]
        user = _session.query(models.User).filter(models.User.username==username).one()
        tries = 0
        while tries < 3:
            newpass = tty.getpass("New password for %s: " % (user,))
            newpass2 = tty.getpass("New password again: ")
            if newpass == newpass2:
                break
            tries += 1
        else:
            self._print("Password not updated.")
            return
        if newpass:
            user.password = newpass
            models.update(user, **longopts)
            _session.commit()
        else:
            self._print("No password, not updated.")

    def delete(self, argv):
        """delete <username>
    Delete a user from the database."""
        username = argv[1]
        try:
            user = _session.query(models.User).filter(models.User.username==username).one()
        except NoResultFound:
            self._ui.error("No user %r found." % (username,))
        else:
            if self._ui.yes_no("Delete %r, are you sure?" % (username,)):
                _session.delete(user)
                _session.commit()


class QueryCommands(CLI.BaseCommands):

    def all(self, argv):
        """all
    Perform the query and show all results."""
        for row in self._obj.all():
            self._print(row)

    def one(self, argv):
        """one
    Get one unique row from query, or throw exception."""
        self._print(self._obj.one())

    def show(self, argv):
        """show
    Show the current SQL."""
        self._print(self._obj.statement)

    def filter(self, argv):
        """filter
    Apply filters by keyword arguments."""
        args, kwargs = CLI.breakout_args(argv[1:], vars(self._obj))
        self._obj = self._obj.filter(**kwargs)

    def count(self, argv):
        """count
    Show the count of the query."""
        self._print(self._obj.count())
        raise CLI.CommandQuit


class CreateCommands(CLI.BaseCommands):

    def _setup(self, obj, prompt):
        super(CreateCommands, self)._setup(obj, prompt)
        self._metadata = sorted(models.get_metadata(obj.__class__))

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
        for metadata in self._metadata:
            self._print("%20.20s: %s" % (metadata.colname, getattr(self._obj, metadata.colname)))

    def commit(self, argv):
        """commit
    Commit the new instance."""
        _session.add(self._obj)
        _session.commit()
        raise CLI.CommandQuit


class ConfigCommands(CLI.BaseCommands):

    def ls(self, argv):
        """ls
    Show container."""
        for ch in self._obj.children:
            self._print("  ", ch)

    def chdir(self, argv):
        """chdir/cd <container>
    Make <container> the current container."""
        name = argv[1]
        if name == "..":
            raise CLI.CommandQuit
        row = _session.query(models.Config).filter(and_(
                models.Config.name==name,
                models.Config.container==self._obj)).one()
        if row.value is NULL:
            pathname = ".".join([self._obj.name, row.name])
            cmd = self.clone(ConfigCommands)
            cmd._setup(row, "%%YConfig%%N:%s> " % pathname)
            raise CLI.NewCommand(cmd)
        else:
            self._print("%s: not a container." % (name,))

    cd = chdir

    def mkdir(self, argv):
        """mkdir <name>
    Make a new container here."""
        name = argv[1]
        container = config.Container(_session, self._obj)
        container.add_container(name)

    def set(self, argv):
        """set [-t <type>] <name> <value>
    Sets the named attribute to a new value. The value will be converted into a
    likely suspect, but you can specify a type with the -t flag.  """
        tval = CLI.clieval
        optlist, longoptdict, args = self.getopt(argv, "t:")
        for opt, optarg in optlist:
            if opt == "-t":
                tval = eval(optarg, {}, {})
                if type(tval) is not type:
                    self._ui.error("Bad type.")
                    return
        value = tval(*tuple(args[1:]))
        name = args[0]
        row = self._get(name)
        if row is None:
            myself = self._obj
            newrow = models.create(models.Config, 
                name=name, 
                value=value, 
                container=myself, 
                user=myself.user,
                testcase=myself.testcase,
                testsuite=myself.testsuite,
                )
            _session.add(newrow)
            self._print("Added %r with value %r." % (name, value))
        else:
            row.value = value
            self._print("Set %r to %r." % (name, value))
        _session.commit()

    def delete(self, argv):
        name = argv[1]
        row = self._get(name)
        if row is not None:
            _session.delete(row)
            _session.commit()
            self._print("%r deleted." % (name,))
        else:
            self._ui.error("No such item: %r." % (name,))

    def get(self, argv):
        """get/show <name>
    Show the value of <name>."""
        row = self._get(argv[1])
        if row is not None:
            self._print(repr(row.value))
        else:
            self._ui.error("No such item.")

    def _get(self, name):
        try:
            return _session.query(models.Config).filter(and_(
                    models.Config.name==name,
                    models.Config.container==self._obj,
                    models.Config.user==self._obj.user,
                    models.Config.testcase==self._obj.testcase,
                    models.Config.testsuite==self._obj.testsuite,
                    )).one()
        except NoResultFound:
            return None




# Maps table names to editor classes
_EDITOR_MAP = {
    "User": UserCommands,
}


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


if __name__ == "__main__":
    import sys
    dbcli(sys.argv)

