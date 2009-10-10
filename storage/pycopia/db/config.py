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

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from pycopia import aid
from pycopia.db import models

Config = models.Config


class ConfigError(Exception):
  pass


def get_root(session):
    c = session.query(Config).filter(and_(
            Config.name=="root", Config.parent_id==None, Config.user==None)).one()
    return c


class Container(object):
    """Make a relational table quack like a dictionary."""
    def __init__(self, session, configrow):
        self.__dict__["session"] = session
        self.__dict__["node"] = configrow

    def __str__(self):
        if self.node.value is aid.NULL:
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
            item = models.create(Config, name=name, value=value, container=me, user=me.user,
                testcase=me.testcase, testsuite=me.testsuite)
            self.session.add(item)
            self.session.commit()
        else:
            item.value = value
            #self.session.update(item) # SA says deprecated.
            self.session.add(item)
            self.session.commit()

    def __getitem__(self, name):
        try:
            item = self.session.query(Config).filter(and_(Config.parent_id==self.node.id,
                Config.name==name)).one()
        except NoResultFound:
            raise KeyError(name)
        if item.value is aid.NULL:
            return Container(self.session, item)
        return item.value

    def __delitem__(self, name):
        item = self.__getitem__(name)
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

    def add_container(self, name):
        me = self.node
        if me.value is aid.NULL:
            new = models.create(Config, name=name, value=aid.NULL, container=me, user=me.user,
                testcase=me.testcase, testsuite=me.testsuite)
            self.session.add(new)
            self.session.commit()
            return Container(self.session, new)
        else:
            raise ConfigError("Cannot add container to value pair.")

    def get_container(self, name):
        me = self.node
        c = session.query(Config).filter(and_(
                Config.name==name, 
                Config.value==aid.NULL, 
                Config.parent_id==me.id, 
                Config.user==me.user)).one()
        return Container(self.session, c)

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
            if item.value is aid.NULL:
                return Container(self.session, item)
            else:
                return item.value
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
                if item.value is aid.NULL:
                    return Container(session, item)
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
        q = session.query(Config).filter(and_(
                Config.name==key,
                Config.parent_id==me.id,
                Config.testcase==me.testcase,
                Config.testsuite==me.testsuite,
                Config.user==me.user))
        return q.count() > 0


def get_item(session, node, key):
    return session.query(Config).filter(and_(Config.container==node, Config.name==key)).one()


# entry point for basic configuration model.
def get_config():
    session = models.get_session()
    container = get_root(session)
    return Container(session, container)


