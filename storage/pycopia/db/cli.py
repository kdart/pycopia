#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 2010 Keith Dart <keith@kdart.com>
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
from decimal import Decimal

from pycopia import CLI
from pycopia import tty
from pycopia import passwd
from pycopia.aid import NULL

from pycopia.db import types
from pycopia.db import models
from pycopia.db import config

from sqlalchemy import and_, or_
from sqlalchemy.orm.exc import NoResultFound

_session = None


class DBSessionCommands(CLI.BaseCommands):

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

    def flush(self, argv):
        """flush
    Commits and uncommitted data."""
        self._obj.flush()

    def expire(self, argv):
        """expire
    Expire local caches."""
        self._obj.expire_all()

    def rollback(self, argv):
        """rollback
    Roll back edits to the database."""
        self._obj.rollback()

    def use(self, argv):
        """use <table>
    Use the given table. Name is class name of mapped table."""
        name = argv[1] 
        t = getattr(models, name)
        cls = _TABLE_EDITOR_MAP.get(name, TableCommands)
        cmd = self.clone(cls)
        cmd._setup(t, cls.get_prompt(t))
        raise CLI.NewCommand(cmd)

    edit = use # alias

    def sql(self, argv):
        """sql <query>
    Pass raw SQL to table. display results.
    """
        self._ui.printf("%IEnter SQL%N:")
        sql = self._ui.get_text()
        res = self._obj.execute(sql)
        for row in res:
            self._print(row)

    def ls(self, argv):
        """ls
    List persistent objects."""
        self._print_list(list(models.class_names()))

    def users(self, argv):
        """users
    Enter User editor mode."""
        cmd = self.clone(UserCommands)
        cmd._setup(models.User, "%YUsers%N> ")
        raise CLI.NewCommand(cmd)

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
        cmd._setup(models.Network, "%BNetwork%N> ")
        raise CLI.NewCommand(cmd)


class RowCommands(CLI.GenericCLI):

    @classmethod
    def get_prompt(cls, dbrow):
        cls._metadata = sorted(models.get_metadata(dbrow.__class__))
        mapper = models.class_mapper(dbrow.__class__)
        pkname = str(mapper.primary_key[0].name)
        return "%%I%s%%N:%s> " % (getattr(dbrow, pkname), dbrow)

    def show(self, argv):
        """show
    show the selected rows data."""
        if len(argv) > 1:
            colname = argv[1]
            self._print("%20.20s: %s" % (colname, getattr(self._obj, colname)))
        else:
            for metadata in self._metadata:
                self._print("%20.20s: %s" % (metadata.colname, getattr(self._obj, metadata.colname)))

    ls = show

    def edit(self, argv):
        """edit [<fieldname>]
    Edit this row object."""
        if len(argv) > 1:
            for fname in argv[1:]:
                for metadata  in models.get_metadata(self._obj.__class__):
                    if metadata.colname == fname:
                        editor = _EDITORS.get(metadata.coltype)
                        if editor:
                            editor(self._ui, self._obj.__class__, metadata, self._obj)
                        else:
                            self._ui.error("No user interface for %r of type %r." % (metadata.colname, metadata.coltype))
        else:
            edit(self._obj.__class__, self._obj, self._ui)

    def commit(self, argv):
        """commit
    Commit the changes."""
        try:
            _session.commit()
        except:
            _session.rollback()
            ex, val, tb = sys.exc_info()
            self._ui.error("%s: %s" % (ex, val))
        else:
            raise CLI.CommandQuit

    def abort(self, argv):
        """abort
    Abort this edit, don't commit changes."""
        _session.rollback()
        raise CLI.CommandQuit


class SessionRowCommands(RowCommands):

    @classmethod
    def get_prompt(cls, dbrow):
        cls._metadata = sorted(models.get_metadata(dbrow.__class__))
        return "%%ISession%%N:%s> " % (dbrow.session_key,)


class InterfaceRowCommands(RowCommands):

    def maskbits(self, argv):
        """maskbits [newbits]
    Show the number of mask bits in the ipaddr."""
        addr = self._obj.ipaddr
        if addr is not None:
            self._print("Mask bits:", addr.maskbits)
            try:
                newbits = argv[1]
            except IndexError:
                pass
            else:
                addr.maskbits = int(newbits)
                self._obj.ipaddr = addr
                _session.commit()
                self._print("New mask bits:", addr.maskbits)
        else:
            self._print("No ipaddr set.")



class NetworkRowCommands(RowCommands):

    def fixinterfaces(self, argv):
        """fixinterfaces
    Fix all attached interfaces to have the same mask bits as this network."""
        maskbits = self._obj.ipnetwork.maskbits
        for intf in self._obj.interfaces:
            addr = intf.ipaddr
            if addr is not None:
                addr.maskbits = maskbits
                intf.ipaddr = addr
        _session.commit()

    def interfaces(self, argv):
        """interfaces
    Show list of attached interfaces."""
        for intf in self._obj.interfaces:
            self._print(repr(intf))


class TestResultRowCommands(RowCommands):

    def parent(self, argv):
        """parent
    Move to parent record."""
        if self._obj.parent is not None:
            cmd = self.clone(TestResultRowCommands)
            cmd._setup(self._obj.parent, TestResultRowCommands.get_prompt(self._obj.parent))
            raise CLI.NewCommand(cmd)
        else:
            self._print("No parent.")


class RowWithAttributesCommands(RowCommands):

    def attrib(self, argv):
        """attrib get|set|del|list name [value]
    Get, set, delete an attribute. You can also list available attributes."""
        cmd = argv[1]
        if cmd.startswith("get"):
            name = argv[2]
            v = self._obj.get_attribute(_session, name)
            self._print(v)
        elif cmd.startswith("set"):
            name = argv[2]
            value = CLI.clieval(argv[3])
            self._obj.set_attribute(_session, name, value)
        elif cmd.startswith("del"):
            name = argv[2]
            self._obj.del_attribute(_session, name)
        elif cmd.startswith("show"):
            for attr in self._obj.attributes:
                self._print(attr)
        elif cmd.startswith("lis"):
            self._print("Possible attributes:")
            for name, basetype in self._obj.__class__.get_attribute_list(_session):
                self._print("   %s (%s)" % (name, basetype))
        else:
            raise CLI.CLISyntaxError("Invalid subcommand.")


class EquipmentRowCommands(RowWithAttributesCommands):

    def interface(self, argv):
        """interface [add-options] <add|del|show|edit|create|attach> name 
    Addd a new interface to this equipment. When adding, specify interface
    parameters with long options:
        --ipaddr=<ipaddr> 
        --macaddr=<macaddr>
        --iftype=<iftype>
        --network=<netname>
        --ifindex=<ifindex>
    when deleting simply specify the name.
    The attach command will attach an already existing interface where the
    parameters are the selector.
    """
        opts, longopts, args = self.getopt(argv, "")
        for opt, arg in opts:
            pass
        cmd = args[0]
        if cmd.startswith("add"):
            name = args[1]
            self._obj.add_interface(_session, name, 
                ifindex=int(longopts.get("ifindex", 1)), 
                interface_type=longopts.get("iftype", "ethernetCsmacd"), 
                macaddr=longopts.get("macaddr"), 
                ipaddr=longopts.get("ipaddr"), 
                network=longopts.get("network"))
        elif cmd.startswith("del"):
            name = args[1]
            if self._ui.yes_no("Delete interface %s, are you sure?" % (name,)):
                self._obj.del_interface(_session, name)
        elif cmd.startswith("sho"):
            try:
                name = args[1]
            except IndexError:
                for intf in self._obj.interfaces.values():
                    self._print(intf)
            else:
                self._print(self._obj.interfaces[name])
        elif cmd.startswith("edi"):
            name = args[1]
            intf = self._obj.interfaces[name]
            cmd = self.clone(InterfaceRowCommands)
            cmd._setup(intf, InterfaceRowCommands.get_prompt(intf))
            raise CLI.NewCommand(cmd)
        elif cmd.startswith("crea"):
            intf = create(models.Interface, self._ui)
            intf.equipment = self._obj
            _session.add(intf)
            _session.commit()
        elif cmd.startswith("att"):
            if len(args) > 1:
                longopts["name"] = args[1]
            self._obj.attach_interface(_session, **longopts)


    def connect(self, argv):
        """connect [-f] <ifname> <networkname>
    Connect an interface to a network."""
        force = False
        opts, longopts, args = self.getopt(argv, "f")
        for opt, arg in opts:
            if opt == "-f":
                force = True
        ifname = args[0]
        network = args[1]
        self._obj.connect(_session, ifname, network, force)

    def disconnect(self, argv):
        """disconnect <ifname>
    Disconnect an interface from its network."""
        ifname = argv[1]
        self._obj.disconnect(_session, ifname)


class TableCommands(CLI.BaseCommands):

    @classmethod
    def get_prompt(cls, table):
        return "%%M%s%%N> " % table.__name__

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
        try:
            rowobj = create(self._obj, self._ui)
        except KeyboardInterrupt:
            _session.rollback()
            self._print("")
        else:
            _session.add(rowobj)
            _session.commit()

    def delete(self, argv):
        """delete ...
    Delete the selected row."""
        dbrow = self._select_one(argv)
        if dbrow is not None:
            if self._ui.yes_no("Delete %s, are you sure?" % (dbrow,)):
                _session.delete(dbrow)
                _session.commit()

    def select(self, argv):
        """select <query>
    Display rows matching query parameters.
    """
        q = self._get_query(argv)
        for dbrow in q:
            self._print(dbrow)

    def ls(self, argv):
        """ls [<criteria>]
    List all current entries, or entries filtered by criteria.
    Criteria can be a simple expression of groups of name, operator, and
    value. a name prefixed by "=" means order by that name.
    """
        mapper = models.class_mapper(self._obj)
        pkname = str(mapper.primary_key[0].name)
        q = self._get_query(argv)
        if q._statement is None:
            q = q.order_by(pkname)
        heading = models.get_rowdisplay(self._obj)
        self._print("\t\t", "\t".join(heading))
        for item in q.all():
            self._print(getattr(item, pkname), "\t:", "\t".join([str(getattr(item, hn)) for hn in heading]))

    def describe(self, argv):
        """describe
    Desribe the table columns."""
        for metadata in sorted(models.get_metadata(self._obj)):
            if metadata.coltype == "RelationshipProperty":
                self._print("%20.20s: %s (%s) m2m=%s, nullable=%s, uselist=%s, collection=%s" % (
                        metadata.colname, metadata.coltype, metadata.default, 
                        metadata.m2m, metadata.nullable, metadata.uselist, metadata.collection))
            else:
                self._print("%20.20s: %s (%s)" % (
                        metadata.colname, metadata.coltype, metadata.default))

    def inspect(self, argv):
        """inspect ...
    Inspect a row."""
        dbrow = self._select_one(argv)
        if dbrow is not None:
            cls = _ROW_EDITOR_MAP.get(self._obj.__name__, RowCommands)
            cmd = self.clone(cls)
            cmd._setup(dbrow, cls.get_prompt(dbrow))
            raise CLI.NewCommand(cmd)

    def show(self, argv):
        """show ...
    Show the selected row."""
        dbrow = self._select_one(argv)
        if dbrow is not None:
            for metadata in sorted(models.get_metadata(self._obj)):
                self._print("%20.20s: %s" % (metadata.colname, getattr(dbrow, metadata.colname)))

    def edit(self, argv):
        """edit ...
    Edit a row object from the table."""
        dbrow = self._select_one(argv)
        if dbrow is not None:
            try:
                edit(self._obj, dbrow, self._ui)
            except KeyboardInterrupt:
                _session.rollback()
                self._print("")
            else:
                _session.commit()

    def commit(self, argv):
        """commit
    Commit any table changes."""
        try:
            _session.commit()
        except:
            _session.rollback()
            raise

    def rollback(self, argv):
        """rollback
    Roll back any table changes."""
        _session.rollback()

    def expire(self, argv):
        """expire
    Expire local caches."""
        _session.expire_all()

    def _select_one(self, argv):
        if len(argv) == 2:
            try:
                rowid = int(argv[1]) # for integer PKs
            except ValueError:
                pass
            else:
                q = _session.query(self._obj)
                return q.get(rowid)
        q = self._get_query(argv)
        try:
            return q.first()
        except:
            _session.rollback()
            raise

    def _get_query(self, argv):
        mapper = models.class_mapper(self._obj)
        args, kwargs = _query_args(argv[1:], self._environ)
        q = _session.query(self._obj)
        if args:
            grps, left = divmod(len(args), 3)
            if grps:
                for name, op, val in _by_three(args[:grps*3]):
                    col = getattr(self._obj, name)
                    opm = {"=": col.__eq__, 
                            ">": col.__gt__, 
                            "<": col.__lt__, 
                            "match": col.match, 
                            #"contains": col.contains, 
                            "like": col.like}.get(op)
                    if opm:
                        if op == "like":
                            val = val.replace("*", "%")
                            val = val.replace(".", "_")
                            if "%" not in val:
                                val = "%" + val + "%"
                        q = q.filter(opm(val))
            for name in args[grps*3:]:
                if name.startswith("="):
                    q = q.order_by(name[1:])
        if kwargs:
            for name, value in kwargs.items():
                col = getattr(self._obj, name)
                value = CLI.clieval(value)
                q = q.filter(col.__eq__(value))
        return q


def _query_args(argv, env):
    args = []
    kwargs = {}
    for argv_arg in argv:
        if argv_arg.find("=") > 0:
            [kw, kwarg] = argv_arg.split("=")
            kwargs[kw.strip()] = env.expand(kwarg)
        else:
            args.append(env.expand(argv_arg))
    return args, kwargs


def _by_three(arglist):
    one, two, three = arglist[:3]
    del arglist[:3]
    yield one, two, three


class NetworkCommands(CLI.BaseCommands):
    pass

# TODO network connections


class TableWithAttributesCommands(TableCommands):

    def attrib(self, argv):
        """attrib list
    List available attributes."""
        cmd = argv[1]
        if cmd.startswith("lis"):
            self._print("Possible attributes:")
            for name, basetype in self._obj.get_attribute_list(_session):
                self._print("   %s (%s)" % (name, basetype))
        else:
            raise CLI.CLISyntaxError("Invalid subcommand.")


class SessionCommands(TableCommands):

    def expired(self, argv):
        """expired
    Show expired sessions."""
        for sess in self._obj.get_expired(_session):
            self._print(sess)

    def clean(self, argv):
        """clean
    Clean out all expired sessions."""
        self._obj.clean(_session)


class TestSuiteRowCommands(RowCommands):

    def results(self, argv):
        """results
    Show latest test results for this test suite."""
        tr = self._obj.get_latest_result(_session)
        if tr is not None:
            cmd = self.clone(TestResultRowCommands)
            cmd._setup(tr, TestResultRowCommands.get_prompt(tr))
            raise CLI.NewCommand(cmd)
        else:
            self._print("No results found.")


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
    """Interactively build up a complex query.
    """

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
        if args:
            self._obj = self._obj.filter(" ".join(args))
        if kwargs:
            for k, v in kwargs.iteritems():
                self._obj = self._obj.filter(getattr(self._obj, k) == v)

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
        """delete <name>
    Delete the named configuration item."""
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
        return _session.query(models.Config).filter(and_(
                    models.Config.name==name,
                    models.Config.container==self._obj,
                    models.Config.user==self._obj.user,
                    models.Config.testcase==self._obj.testcase,
                    models.Config.testsuite==self._obj.testsuite,
                    )).scalar()

    def rename(self, argv):
        """rename <key> <newkey>
    Rename a key name to another name."""
        oldname = argv[1]
        newname = argv[2]
        row = self._get(oldname)
        if row is not None:
            row.name = newname
            _session.commit()
        else:
            self._ui.error("No such item.")



# Maps table names to editor classes
_TABLE_EDITOR_MAP = {
    "User": UserCommands,
    "Session": SessionCommands,
    "Equipment": TableWithAttributesCommands,
    "EquipmentModel": TableWithAttributesCommands,
    "Environment": TableWithAttributesCommands,
    "Software": TableWithAttributesCommands,
    "Corporation": TableWithAttributesCommands,
}

_ROW_EDITOR_MAP = {
    "Equipment": EquipmentRowCommands,
    "EquipmentModel": RowWithAttributesCommands,
    "Environment": RowWithAttributesCommands,
    "Software": RowWithAttributesCommands,
    "Corporation": RowWithAttributesCommands,
    "Network": NetworkRowCommands,
    "Interface": InterfaceRowCommands,
    "Session": SessionRowCommands,
    "TestResult": TestResultRowCommands,
    "TestSuite": TestSuiteRowCommands,
}


def create(modelclass, ui):
    data = {}
    for metadata in sorted(models.get_metadata(modelclass)):
        ctor = _CREATORS.get(metadata.coltype)
        if ctor:
            data[metadata.colname] = ctor(ui, modelclass, metadata)
        else:
            ui.error("No user interface for %r of type %r." % (metadata.colname, metadata.coltype))
    dbrow =  models.create(modelclass)
    return update_row(modelclass, dbrow, data)


def update_row(modelclass, dbrow, data):
    for metadata in models.get_metadata(modelclass):
        value = data.get(metadata.colname)
        if not value and metadata.nullable:
            value = None
        if metadata.coltype == "RelationshipProperty":
            relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
            if isinstance(value, list):
                if not value:
                    continue
                t = _session.query(relmodel).filter(relmodel.id.in_(value)).all()
                if metadata.collection == "MappedCollection":
                    setattr(dbrow, metadata.colname, dict((o.name, o) for o in t))
                else:
                    setattr(dbrow, metadata.colname, t)
            elif value is None:
                if metadata.uselist:
                    if metadata.collection == "MappedCollection":
                        value = {}
                    else:
                        value = []
                setattr(dbrow, metadata.colname, value)
            else:
                related = _session.query(relmodel).get(value)
                setattr(dbrow, metadata.colname, related)

        elif metadata.coltype == "PickleText":
            if value is None:
                if metadata.nullable:
                    setattr(dbrow, metadata.colname, value)
                else:
                    setattr(dbrow, metadata.colname, "")
            else:
                try:
                    value = eval(value, {}, {})
                except: # allows use of unquoted strings.
                    pass
                setattr(dbrow, metadata.colname, value)
        else:
            setattr(dbrow, metadata.colname, value)
    return dbrow


def new_textarea(ui, modelclass, metadata):
    ui.printf("%%nEnter %%I%s%%N:" % metadata.colname)
    return ui.get_text().strip()

def new_key(ui, modelclass, metadata):
    return ui.get_key("Press a key for %r: " % (metadata.colname,))

def _new_pytype(ui, modelclass, metadata, pytype):
    while 1:
        raw = ui.get_value("%s? (%s) " % (metadata.colname, pytype.__name__), default=str(metadata.default))
        raw = raw.strip()
        if not raw and metadata.nullable:
            return None
        try:
            return pytype(raw)
        except ValueError:
            ui.error("Need a %s." % pytype.__name__)

def new_float(ui, modelclass, metadata):
    return _new_pytype(ui, modelclass, metadata, float)

def new_number(ui, modelclass, metadata):
    return _new_pytype(ui, modelclass, metadata, Decimal)

def new_integer(ui, modelclass, metadata):
    return _new_pytype(ui, modelclass, metadata, int)

def new_textinput(ui, modelclass, metadata):
    return ui.user_input(metadata.colname + "? ")

def new_boolean_input(ui, modelclass, metadata):
    return ui.yes_no(metadata.colname + "? ", bool(metadata.default))

def new_cidr(ui, modelclass, metadata):
    return ui.user_input("IP network for %r (e.g. 192.168.1.0/24): " % (metadata.colname,))

def new_inet(ui, modelclass, metadata):
    return ui.user_input("IP address for %r (e.g. 192.168.1.1/24): " % (metadata.colname,))

def new_datetime(ui, modelclass, metadata):
    return ui.get_value("Date and time for %r: " % (metadata.colname,), metadata.default)

def new_macaddr(ui, modelclass, metadata):
    return ui.get_value("MAC address for %r: " % (metadata.colname,), metadata.default)

def new_time(ui, modelclass, metadata):
    return ui.get_value("Time for %r: " % (metadata.colname,), metadata.default)

def new_date(ui, modelclass, metadata):
    return ui.get_value("Date for %r: " % (metadata.colname,), metadata.default)

def new_interval(ui, modelclass, metadata):
    return ui.user_input("Interval for %r: " % (metadata.colname,))

def new_pickleinput(ui, modelclass, metadata):
    if metadata.default is None:
        default = ""
    else:
        default = repr(metadata.default)
    return ui.get_value("Object for %r: " % (metadata.colname,), metadata.default)

def new_uuid(ui, modelclass, metadata):
    return ui.user_input("UUID for %r: " % (metadata.colname,))

def new_valuetypeinput(ui, modelclass, metadata):
    return ui.choose_key(dict(types.ValueType.get_choices()), 0, "%%I%s%%N" % metadata.colname)

def new_relation_input(ui, modelclass, metadata):
    choices = models.get_choices(_session, modelclass, metadata.colname, None)
    if not choices:
        ui.Print("%s has no choices." % metadata.colname)
        if metadata.uselist:
            return []
        else:
            return None
    if metadata.uselist:
        return ui.choose_multiple_from_map(dict(choices), None, "%%I%s%%N" % metadata.colname).keys()
    else:
        if metadata.nullable:
            choices.insert(0, (0, "Nothing"))
            default = 0
        else:
            default = choices[0][0]
        return ui.choose_key(dict(choices), default, "%%I%s%%N" % metadata.colname)

def new_testcasestatus(ui, modelclass, metadata):
    return ui.choose_key(dict(types.TestCaseStatus.get_choices()), 
            types.TestCaseStatus.get_default(), "%%I%s%%N" % metadata.colname)

def new_testcasetype(ui, modelclass, metadata):
    return ui.choose_key(dict(types.TestCaseType.get_choices()), 
            types.TestCaseType.get_default(), "%%I%s%%N" % metadata.colname)

def new_testpriority(ui, modelclass, metadata):
    return ui.choose_key(dict(types.TestPriorityType.get_choices()), 
            types.TestPriorityType.get_default(), "%%I%s%%N" % metadata.colname)


_CREATORS = {
    "ARRAY": None,
    "BIGINT": new_integer,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": new_boolean_input,
    "CHAR": new_key,
    "Cidr": new_cidr,
    "DATE": new_date,
    "TIMESTAMP": new_datetime,
    "FLOAT": new_float,
    "Inet": new_inet,
    "INTEGER": new_integer,
    "INTERVAL": new_interval,
    "MACADDR": new_macaddr,
    "NUMERIC": new_number,
    "SMALLINT": new_integer,
    "VARCHAR": new_textinput,
    "TEXT": new_textarea,
    "TIME": new_time,
    "UUID": new_uuid,
    "PickleText": new_pickleinput,
    "ValueType": new_valuetypeinput,
    "RelationshipProperty": new_relation_input,
    "TestCaseStatus": new_testcasestatus,
    "TestCaseType": new_testcasetype,
    "TestPriorityType": new_testpriority,
}


### modify/editing  ####

def edit(modelclass, dbrow, ui):
    for metadata in sorted(models.get_metadata(modelclass)):
        editor = _EDITORS.get(metadata.coltype)
        if editor:
            editor(ui, modelclass, metadata, dbrow)
        else:
            ui.error("No user interface for %r of type %r." % (metadata.colname, metadata.coltype))

def edit_float(ui, modelclass, metadata, dbrow):
    return _edit_pytype(ui, modelclass, metadata, dbrow, float)

def edit_integer(ui, modelclass, metadata, dbrow):
    return _edit_pytype(ui, modelclass, metadata, dbrow, int)

def edit_number(ui, modelclass, metadata, dbrow):
    return _edit_pytype(ui, modelclass, metadata, dbrow, Decimal)

def _edit_pytype(ui, modelclass, metadata, dbrow, pytype):
    while 1:
        inp = ui.get_value("%s? (%s) " % (metadata.colname, pytype.__name__), getattr(dbrow, metadata.colname))
        if not inp and metadata.nullable:
            setattr(dbrow, metadata.colname, None)
        try:
            inp = pytype(inp)
        except ValueError:
            ui.error("Need a %s." % pytype.__name__)
        else:
            setattr(dbrow, metadata.colname, inp)
            return

def edit_text(ui, modelclass, metadata, dbrow):
    text = getattr(dbrow, metadata.colname)
    if text is None:
        text = ""
    text = ui.edit_text(text, metadata.colname).strip()
    if not text and metadata.nullable:
        text = None
    setattr(dbrow, metadata.colname, text)

def edit_bool(ui, modelclass, metadata, dbrow):
    val = getattr(dbrow, metadata.colname)
    new = ui.yes_no(metadata.colname + "? ", default=val)
    setattr(dbrow, metadata.colname, new)

def edit_key(ui, modelclass, metadata, dbrow):
    key = ui.get_key("Press a key for %r: " % (metadata.colname,))
    setattr(dbrow, metadata.colname, key)

def edit_field(ui, modelclass, metadata, dbrow):
    new = ui.get_value(metadata.colname + "? ", getattr(dbrow, metadata.colname))
    setattr(dbrow, metadata.colname, new)

def edit_relation_input(ui, modelclass, metadata, dbrow):
    choices = models.get_choices(_session, modelclass, metadata.colname, None)
    if not choices:
        ui.Print("%s has no choices." % metadata.colname)
        if metadata.uselist:
            if metadata.collection == "MappedCollection":
                setattr(dbrow, metadata.colname, {})
            else:
                setattr(dbrow, metadata.colname, [])
        else:
            setattr(dbrow, metadata.colname, None)
        return
    choices = dict(choices)
    current = getattr(dbrow, metadata.colname)
    relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
    if metadata.uselist:
        if metadata.collection == "MappedCollection":
            chosen = dict((crow.id, str(crow)) for crow in current.values())
        else:
            chosen = dict((crow.id, str(crow)) for crow in current)
        for chosenone in chosen:
            try:
                del choices[chosenone]
            except KeyError: # choice may have gone away.
                pass
        chosen = ui.choose_multiple_from_map(choices, chosen, "%%I%s%%N" % metadata.colname)
        if chosen:
            t = _session.query(relmodel).filter( relmodel.id.in_(chosen.keys())).all()
        else:
            t = []
        if not t and metadata.nullable:
            t = None
        if metadata.collection == "MappedCollection" and t is not None:
            col = getattr(dbrow, metadata.colname)
            for val in t:
                col.set(val)
        else:
            setattr(dbrow, metadata.colname, t)
    else:
        if metadata.nullable:
            choices[0] = "Nothing"
        chosen_id = ui.choose_key(choices, current.id if current is not None else 0, 
                "%%I%s%%N" % metadata.colname)
        if chosen_id == 0: # indicates nullable
            setattr(dbrow, metadata.colname, None)
        else:
            related = _session.query(relmodel).get(chosen_id)
            setattr(dbrow, metadata.colname, related)


def edit_valuetype(ui, modelclass, metadata, dbrow):
    vt = ui.choose_key(dict(types.ValueType.get_choices()), getattr(dbrow, metadata.colname), 
            "%%I%s%%N" % metadata.colname)
    setattr(dbrow, metadata.colname, types.ValueType.validate(vt))


def edit_testcasestatus(ui, modelclass, metadata, dbrow):
    current = int(getattr(dbrow, metadata.colname))
    choices = dict(types.TestCaseStatus.get_choices())
    chosen_id = ui.choose_key(choices, current, "%%I%s%%N" % metadata.colname)
    setattr(dbrow, metadata.colname, types.TestCaseStatus.validate(chosen_id))

def edit_testcasetype(ui, modelclass, metadata, dbrow):
    current = getattr(dbrow, metadata.colname)
    choices = dict(types.TestCaseType.get_choices())
    chosen_id = ui.choose_key(choices, current, "%%I%s%%N" % metadata.colname)
    setattr(dbrow, metadata.colname, types.TestCaseType.validate(chosen_id))

def edit_testpriority(ui, modelclass, metadata, dbrow):
    current = getattr(dbrow, metadata.colname)
    choices = dict(types.TestPriorityType.get_choices())
    chosen_id = ui.choose_key(choices, current, "%%I%s%%N" % metadata.colname)[0]
    setattr(dbrow, metadata.colname, types.TestPriorityType.validate(chosen_id))

def edit_pickleinput(ui, modelclass, metadata, dbrow):
    current = getattr(dbrow, metadata.colname)
    value = ui.get_value(metadata.colname + ":\n", default=repr(current))
    try:
        value = eval(value, {}, {})
    except: # allows use of unquoted strings.
        pass
    setattr(dbrow, metadata.colname, value)


_EDITORS = {
    "ARRAY": None,
    "BIGINT": edit_integer,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": edit_bool,
    "CHAR": edit_key,
    "Cidr": edit_field,
    "Inet": edit_field,
    "DATE": edit_field,
    "TIMESTAMP": edit_field,
    "FLOAT": edit_float,
    "INTEGER": edit_integer,
    "INTERVAL": edit_field,
    "MACADDR": edit_field,
    "NUMERIC": edit_number,
    "SMALLINT": edit_integer,
    "VARCHAR": edit_text,
    "TEXT": edit_text,
    "TIME": edit_field,
    "UUID": edit_text,
    "PickleText": edit_pickleinput,
    "ValueType": edit_valuetype,
    "RelationshipProperty": edit_relation_input,
    "TestCaseStatus": edit_testcasestatus,
    "TestCaseType": edit_testcasetype,
    "TestPriorityType": edit_testpriority,
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
    cmd = DBSessionCommands(ui)
    _session = models.get_session(database)
    cmd._setup(_session, "db> ")
    cmd._environ["session"] = _session
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

def dbconfig(argv):
    """dbconfig [-?] [<database_url>]

Provides an interactive session to the database configuration table.
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
            print dbconfig.__doc__
            return
    for opt, val in optlist:
        if opt == "-?":
            print dbconfig.__doc__
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
    cmd = ConfigCommands(ui)
    _session = models.get_session(database)
    root = config.get_root(_session)
    cmd._setup(root, "%%Ydbconfig%%N:%s> " % (root.name,))
    cmd._environ["session"] = _session
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_dbconfig"))
    parser.interact()


if __name__ == "__main__":
    dbcli(sys.argv)

