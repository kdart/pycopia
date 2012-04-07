#!/usr/bin/python2.6
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2009  Keith Dart <keith@kdart.com>
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

Pycopia Configuration and Information storage
---------------------------------------------

Wrap the Config table in the database and make it look like a tree of
name-value pairs (mappings). 

"""

import re

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from pycopia.db import models
# The NULL value is used to flag a container node.
from pycopia.aid import NULL

Config = models.Config


class ConfigError(Exception):
  pass


def get_root(session):
    c = session.query(Config).filter(and_(
            Config.name=="root", Config.parent_id==None, Config.user==None)).one()
    return c


class Container(object):
    """Make a relational table quack like a dictionary."""
    def __init__(self, session, configrow, user=None, testcase=None, testsuite=None):
        self.__dict__["session"] = session
        self.__dict__["node"] = configrow
        self.__dict__["_user"] = user
        self.__dict__["_testcase"] = testcase
        self.__dict__["_testsuite"] = testsuite

    def __str__(self):
        if self.node.value is NULL:
            s = []
            for ch in self.node.children:
                s.append(str(ch))
            return "(%s: %s)" % (self.node.name, ", ".join(s))
        else:
            return str(self.node)

    def __setitem__(self, name, value):
        try:
            item = self.session.query(Config).filter(and_(Config.parent_id==self.node.id,
                Config.name==name)).one()
        except NoResultFound:
            me = self.node
            item = models.create(Config, name=name, value=value, container=me, user=self._user)
            self.session.add(item)
            self.session.commit()
        else:
            item.value = value
            #self.session.update(item) # SA says deprecated.
            self.session.add(item)
            self.session.commit()

    def __getitem__(self, name):
        try:
            item = self.session.query(Config).filter(self._get_item_filter(name)).one()
        except NoResultFound:
            raise KeyError(name)
        if item.value is NULL:
            return Container(self.session, item, 
                    user=self._user, testcase=self._testcase, testsuite=self._testsuite)
        return item.value

    def __delitem__(self, name):
        try:
            item = self.session.query(Config).filter(self._get_item_filter(name)).one()
        except NoResultFound:
            raise KeyError(name)
        self.session.delete(item)
        self.session.commit()

    value = property(lambda s: s.node.value)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            self.__setitem__(key, default)
            return default

    def iterkeys(self):
        for name, in self.session.query(Config.name).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield name

    def keys(self):
        return list(self.iterkeys())

    def iteritems(self):
        for name, value in self.session.query(Config.name, Config.value).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield name, value

    def items(self):
        return list(self.iteritems())

    def itervalues(self):
        for value, in self.session.query(Config.value).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield value

    def values(self):
        return list(self.itervalues())

    # for compatibility with real dictionaries, but this object is not a
    # true copy but only a new wrapper instance.
    def copy(self):
        return self.__class__(self.session, self.node)

    # Containers can be owned by a user. New containers created by a user are
    # owned by the same user. If the superuser creates a new container it is
    # not owned by anybody (set the ownership as a separate operation). Superuser
    # can see all containers, but regular users only see their own containers.
    # New containers created without a registered user inherit ownership from
    # parent node.
    # There might be some fancy SQL for all of this, but I'm better at Python than SQL. :[
    def _get_user(self):
        if self._user:
            if self._user.is_superuser:
                return None
            else:
                return self._user
        else: #inherit
            return self.node.user 

    def _get_item_filter(self, name):
        user = self._get_user()
        if user is not None:
            return and_(Config.name==name, Config.container==self.node, Config.user==user)
        else:
            return and_(Config.name==name, Config.container==self.node)

    def add_container(self, name):
        me = self.node
        if me.value is NULL:
            new = models.create(Config, name=name, value=NULL, container=me, 
                    user=self._get_user(),
                    testcase=self._testcase or me.testcase, 
                    testsuite=self._testsuite or me.testsuite)
            try:
                self.session.add(new)
                self.session.commit()
            except IntegrityError as err:
                self.session.rollback()
                raise ConfigError(str(err))
            return Container(self.session, new,
                    user=self._user, testcase=self._testcase, testsuite=self._testsuite)
        else:
            raise ConfigError("Cannot add container to value pair.")

    def get_container(self, name):
        c = self.session.query(Config).filter(self._get_item_filter(name)).one()
        if c.value is NULL:
            return Container(self.session, c,
                    user=self._user, testcase=self._testcase, testsuite=self._testsuite)
        else:
            raise ConfigError("Container %r not found." % (name,))

    def __contains__(self, key):
        return self.has_key(key)

    def __iter__(self):
        me = self.node
        self.__dict__["_set"] = iter(self.session.query(Config).filter(and_(
            Config.parent_id==me.id, 
            Config.user==me.user, 
            Config.testcase==me.testcase, 
            Config.testsuite==me.testsuite)))
        return self

    def next(self):
        try:
            item = self.__dict__["_set"].next()
            return item.name
        except StopIteration:
            del self.__dict__["_set"]
            raise

    def __getattribute__(self, key):
        try:
            return super(Container, self).__getattribute__(key)
        except AttributeError:
            node = self.__dict__["node"]
            session = self.__dict__["session"]
            try:
                item = session.query(Config).filter(and_(
                        Config.container==node, Config.name==key)).one()
                if item.value is NULL:
                    return Container(session, item,
                        user=self._user, testcase=self._testcase, testsuite=self._testsuite)
                else:
                    return item.value
            except NoResultFound, err:
                raise AttributeError("Container: No attribute or key '%s' found: %s" % (key, err))

    def __setattr__(self, key, obj):
        if self.__class__.__dict__.has_key(key): # to force property access
            type.__setattr__(self.__class__, key, obj)
        elif self.__dict__.has_key(key): # existing local attribute
            self.__dict__[key] =  obj
        else:
            self.__setitem__(key, obj)

    def __delattr__(self, key):
        try:
            self.__delitem__(key)
        except KeyError:
            object.__delattr__(self, key)

    def has_key(self, key):
        me = self.node
        q = self.session.query(Config).filter(and_(
                Config.name==key,
                Config.parent_id==me.id,
                Config.testcase==me.testcase,
                Config.testsuite==me.testsuite,
                Config.user==me.user))
        return q.count() > 0

    _var_re = re.compile(r'\$([a-zA-Z0-9_\?]+|\{[^}]*\})')

    # perform shell-like variable expansion
    def expand(self, value):
        if '$' not in value:
            return value
        i = 0
        while 1:
            m = Container._var_re.search(value, i)
            if not m:
                return value
            i, j = m.span(0)
            oname = vname = m.group(1)
            if vname.startswith('{') and vname.endswith('}'):
                vname = vname[1:-1]
            tail = value[j:]
            value = value[:i] + str(self.get(vname, "$"+oname))
            i = len(value)
            value += tail

    def expand_params(self, tup):
        rv = []
        for arg in tup:
            if isinstance(arg, basestring):
                rv.append(self.expand(arg))
            else:
                rv.append(arg)
        return tuple(rv)

    def set_owner(self, user):
        if self._user is not None and self._user.is_superuser:
            if self.node.container is not None:
                self.node.set_owner(self.session, user)
            else:
                raise ConfigError("Root container can't be owned.")
        else:
            raise ConfigError("Current user must be superuser to change ownership.")

    def register_user(self, username):
        if username is not None:
            if self.node.id == 1:
                raise ConfigError("Tried to register a user on root node.")
            if isinstance(username, basestring):
                self._user = models.User.get_by_username(self.session, username)
            elif isinstance(username, models.User):
                self._user = username
            else:
                raise ValueError("{!r} is not a valid type of user to register.".format(username))
        else:
            self._user = None

    def register_testcase(self, name):
        if name is not None:
            self._testcase = models.TestCase.get_by_implementation(self.session, name)
        else:
            self._testcase = None

    def register_testsuite(self, name):
        if name is not None:
            self._testsuite = models.TestSuite.get_by_implementation(self.session, name)
        else:
            self._testsuite = None


def get_item(session, node, key):
    return session.query(Config).filter(and_(Config.container==node, Config.name==key)).one()


# entry point for basic configuration model.
def get_config():
    session = models.get_session()
    root = get_root(session)
    return Container(session, root)


