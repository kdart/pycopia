#!/usr/bin/python2.4
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


import sys, os, re

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from pycopia.db import models
from pycopia import dictlib
from pycopia import urlparse
from pycopia import aid

Config = models.Config


class ConfigError(Exception):
  pass

# container node marker, containers contain no useful value.
#CONTAINER = aid.NULLType("CONTAINER", (type,), {})


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
            self.session.update(item)
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

    def copy(self):
        return self.__class__(self._session, self.node) # XXX

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


class RootContainer(Container):
    """RootContainer is the primary configuration holder.

    The root container is special. It contains special object
    constructor methods, and a local writeable cache. It also supports
    path access using the dot as path separator. 
    """

    def __init__(self, session, container, cache):
        super(RootContainer, self).__init__(session, container)
        self.__dict__["_cache"] = cache
        # cacheable objects
        cache._report = None
        cache._logfile = None
        cache._environment = None
        cache._configurator = None
        cache._UI = None

    def __repr__(self):
        return "<RootContainer>"

    def __getattribute__(self, key):
        try:
            return super(RootContainer, self).__getattribute__(key)
        except AttributeError:

            try:
                # check the local cache first, overrides persistent storage
                obj = self.__dict__["_cache"].__getitem__(key)
                return obj
            except KeyError:
                pass
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
            self.__dict__["_cache"].__setitem__(key, obj)

    def __delattr__(self, key):
        try:
            self.__dict__["_cache"].__delitem__(key)
        except KeyError:
            object.__delattr__(self, key)

    def __getitem__(self, key):
        try:
            return getattr(self._cache, key)
        except (AttributeError, KeyError, NameError):
            pass
        return super(RootContainer, self).__getitem__(key)

    def __setitem__(self, key, value):
        if self._cache.has_key(key):
            self._cache[key] = value
        else:
            return super(RootContainer, self).__setitem__(key, value)

    def __delitem__(self, key):
        if self._cache.has_key(key):
            del self._cache[key]
        else:
            super(RootContainer, self).__delitem__(key)

    def has_key(self, key):
        return self._cache.has_key(key) or super(RootContainer, self).has_key(key)


    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    # files update the local cache only. 
    def mergefile(self, filename):
        if os.path.isfile(filename):
            gb = dict(list(self.items()))
            execfile(filename, gb, self._cache)

    # Updates done from external dicts only update the local cache. If you
    # want it persistent, enter it into the persistent store another way.
    def update(self, other):
        for k, v in other.items():
            d = self._cache
            path = k.split(".") # allows for keys with dot-path 
            for part in path[:-1]:
                d = d[part]
            # Use setattr for the sake of attribute-dicts, properties, and other objects.
            setattr(d, path[-1], v) 

    def setdefault(self, key, val):
        d = self._cache
        path = key.split(".")
        for part in path[:-1]:
            d = d[part]
        return d.setdefault(path[-1], val) 

    def evalset(self, k, v):
        """Evaluates the (string) value to convert it to an object in the
        storage first. Useful for specifying objects from string-sources, such
        as the command line. """
        if type(v) is str:
            try:
                v = eval("self.%s" % (v,))
            except:
                pass
        d = self._cache
        path = k.split(".") # allows for keys with dot-path 
        for part in path[:-1]:
            d = d[part]
        # Use setattr for attribute-dicts, properties, and other objects.
        setattr(d, path[-1], v) 

    def evalupdate(self, other):
        for k, v in other.items():
            self.evalset(k, v)

    _var_re = re.compile(r'\$([a-zA-Z0-9_\?]+|\{[^}]*\})')

    # perform shell-like variable expansion
    def expand(self, value):
        if '$' not in value:
            return value
        i = 0
        while 1:
            m = RootContainer._var_re.search(value, i)
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

    reportpath = property(lambda s: os.path.join(s.reportdir, s.reportbasename))

    # report object constructor
    def get_report(self):
        if self._cache._report is None:
            rep = self._build_report(None)
            self._cache._report = rep
            return rep
        else:
            return self._cache._report

    def _build_report(self, name):
        from pycopia import reports # XXX pycopia-QA circular dependency.
        if name is None:
            name = self.get("reportname", "default")
        params = self.reports.get(name, (None,))
        if type(params) is list:
            params = map(self._param_expand, params)
        else:
            params = self._param_expand(params)
        return reports.get_report( params )

    # reconstruct the report parameter list with dollar-variables expanded.
    def _param_expand(self, tup):
        rv = []
        for arg in tup:
            if type(arg) is str:
                rv.append(self.expand(arg))
            else:
                rv.append(arg)
        return tuple(rv)

    def set_report(self, reportname):
        if type(reportname) is str:
            rep = self._build_report(reportname)
            self._cache._report = rep
        else:
            self._cache._report = reportname # hopefully a report object already

    def del_report(self):
        self._cache._report = None

    report = property(get_report, set_report, del_report, "report object")

    def get_logfile(self):
        from pycopia import logfile
        if self._cache._logfile is None:
            logfilename = self.get_logfilename()
            try:
                lf = logfile.ManagedLog(logfilename, self.get("logfilesize", 1000000))
                if self.flags.VERBOSE:
                    print "Logging to:", logfilename
            except:
                ex, val, tb = sys.exc_info()
                print >>sys.stderr, "get_logfile: Could not open log file."
                print >>sys.stderr, ex, val
                self._cache._logfile = None
                return None
            else:
                self._cache._logfile = lf
                return lf
        else:
            return self._cache._logfile

    def set_logfile(self, lf=None):
        self._cache._logfile = lf

    def del_logfile(self):
        try:
            self._cache._logfile.close()
        except:
            pass
        self._cache._logfile = None

    logfile = property(get_logfile, set_logfile, del_logfile, "ManagedLog object")

    def get_logfilename(self):
        return os.path.join(os.path.expandvars(self.logfiledir), self.logbasename)

    logfilename = property(get_logfilename, None, None, "The logfile object's path name.")

    def _get_environment(self):
        """Get the Environment object defined by the test configuration.
        """
        if self._cache.get("_environment") is None:
            name = self.get("environmentname", "default")
            if name:
                db = self._dbsession
                env = db.query(models.Environment).filter(models.Environment.name==name).one()
                self._cache["_environment"] = env
            else:
                raise ConfigError, "Bad environment %r." % (name,)
        return self._cache["_environment"]

    def _del_environment(self):
        self._cache["_environment"] = None

    environment = property(_get_environment, None, _del_environment)

    # user interface for interactive tests.
    def get_userinterface(self):
        if self._cache.get("_UI") is None:
            ui = self._build_userinterface()
            self._cache["_UI"] = ui
            return ui
        else:
            return self._cache["_UI"]

    def _build_userinterface(self):
        from pycopia import UI
        uitype = self.get("userinterfacetype", "default")
        params = self.userinterfaces.get(uitype)
        if params:
            params = self._param_expand(params)
        else:
            params = self.userinterfaces.get("default")
        return UI.get_userinterface(*params)

    def del_userinterface(self):
        """Remove the UI object from the cache.    """
        ui = self._cache.get("_UI")
        self._cache["_UI"] = None
        if ui:
            try:
                ui.close()
            except:
                pass

    UI = property(get_userinterface, None, del_userinterface, 
                        "User interface object used for interactive tests.")


##### end of RootContainer ######



def get_config(_extrafiles=None, initdict=None, **kwargs):
    """get_config([extrafiles], [initdict=], [**kwargs])
Returns a RootContainer instance containing configuration parameters.
An extra dictionary may be merged in with the 'initdict' parameter.
And finally, extra options may be added with keyword parameters when calling
this.  """
    files = []
    files.append(os.path.join(os.environ["HOME"], ".pycopiarc"))

    if type(_extrafiles) is str:
        _extrafiles = [_extrafiles]
    if _extrafiles:
        files.extend(_extrafiles)
    session = models.get_session()
    container = get_root(session)
    cache = dictlib.AttrDict()
    cf = RootContainer(session, container, cache)
    for f in files:
        if os.path.isfile(f):
            cf.mergefile(f)
    if type(initdict) is dict:
        cf.evalupdate(initdict)
    cf.update(kwargs)
    return cf


if __name__ == "__main__":
    from pycopia import autodebug
    if sys.flags.interactive:
        from pycopia import interactive
    sess = models.get_session()
    cf = get_config()
    print cf
    #print cf.flags
    #print cf.flags.DEBUG
    #cf.reportname = "default"
    print cf.get("reportname")
    print cf.report



