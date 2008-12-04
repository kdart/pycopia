#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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

"""


import sys, os, re, itertools
import cPickle as pickle

from pycopia import aid
from pycopia import dictlib
from pycopia import urlparse


DEFAULT_URL = "postgres://pycstorage@localhost/pycstorage"

# types
OBJECT, INTEGER, STRING, FLOAT, LONG, CONTAINER = aid.Enums(
    "OBJECT", "INTEGER", "STRING", "FLOAT", "LONG", "CONTAINER")

class Container(object):
    """Wrapper for a persistent dictionary providing attribute-style access.
    ."""
    def __init__(self, container):
        self.__dict__["_container"] = container

    def __repr__(self):
        return "<Container>"

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def get(self, key, default=None):
        pass

    def getpath(self, key, default=None):
        pass

    def set(self, key, obj):
        pass

    def delete(self, key):
        pass

    def rename(self, oldkey, newkey):
        pass

    # attribute-style access to container contents
    def __getattribute__(self, key):
        try:
            return super(Container, self).__getattribute__(key)
        except AttributeError:
            pass # XXX

    def __setattr__(self, key, obj):
        pass

    def __delattr__(self, key):
        pass

    # attribute-style access to container contents, also prefer the local cache.
    def __getattribute__(self, key):
        try:
            return super(RootContainer, self).__getattribute__(key)
        except AttributeError:
            pass # XXX

    def __setattr__(self, key, obj):
        pass
        if key in self.__class__.__dict__:
            type.__setattr__(self.__class__, key, obj)
        elif key in self.__dict__:
            self.__dict__[key] =  obj
        else:
            self.__dict__["_cache"].__setitem__(key, obj)

    def __delattr__(self, key):
        try:
            self.__dict__["_cache"].__delitem__(key)
        except KeyError:
            object.__delattr__(self, key)

    def copy(self):
        pass

    def __getitem__(self, key):
        try:
            return getattr(self._cache, key)
        except (AttributeError, KeyError, NameError):
            pass
        pass # XXX

    def __setitem__(self, key, value):
        if key in self._cache:
            self._cache[key] = value
        else:
            pass # XXX

    def __delitem__(self, key):
        if key in self._cache:
            del self._cache[key]
        else:
            pass # XXX

    def get(self, name, default=None):
        try:
            obj = self._cache[name]
        except KeyError:
            pass # XXX

    def set(self, key, obj):
        pass

    def delete(self, key):
        pass

    def keys(self):
        pass

    def has_key(self, key):
        pass

    def iteritems(self):
        pass

    def iterkeys(self):
        pass

    def itervalues(self):
        pass

    def add_container(self, name):
        pass

    # files update the local cache only. 
    def mergefile(self, filename):
        if os.path.isfile(filename):
            gb = dict(self._container)
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
            m = self._var_re.search(value, i)
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


class RootContainer(Container):
    """The root container is special, it contains the computed methods, and a
    local writeable cache. It also supports path access using the dot as path separator. """
    def __init__(self, connection, cache):
        super(RootContainer, self).__init__(connection)
        self.__dict__["_cache"] = cache
        # cacheable objects
        self._cache._report = None
        self._cache._logfile = None

    def __repr__(self):
        return "<RootContainer>"

    def commit(self):
        self._connection.commit()

    def abort(self):
        self._connection.rollback()

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

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
            params = map(self._report_param_expand, params)
        else:
            params = self._report_param_expand(params)
        return reports.get_report( params )

    # reconstruct the report parameter list with dollar-variables expanded.
    def _report_param_expand(self, tup):
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

##### end of RootContainer ######


def connect(url):
    url = urlparse.UniversalResourceLocator(url, True)
    scheme = url.scheme
    if scheme == "postgres":
        global psycopg
        import psycopg2
        def _connectpg(host, database, user, password):
            if password:
                return psycopg2.connect("dbname=%r user=%r host=%r password=%r" % (
                    database, user, host, password))
            else:
                return psycopg2.connect("dbname=%r user=%r host=%r" % (
                    database, user, host))
        try:
            return _connectpg(url.host, url.path[1:], url.user, url.password)
        except psycopg2.OperationalError:
            print >>sys.stderr, "No database, creating: %r" % (url,)
            create_db(url)
            db = _connectpg(url.host, url.path[1:], url.user, url.password)
            _initialize(db)
            return db
    elif scheme == "mysql":
        raise NotImplementedError
    elif scheme == "sqlite":
        raise NotImplementedError

def create_db(url):
    url = urlparse.UniversalResourceLocator(url, True)
    scheme = url.scheme
    if scheme == "postgres":
        cmd = 'sudo su postgres -c "createuser --host %s --createdb --no-superuser --no-createrole %s"' % (url.host, url.user)
        os.system(cmd)
        cmd = 'sudo su postgres -c "createdb --host %s --owner %s --encoding utf-8 %s"' % (url.host, url.user, url.path[1:])
        os.system(cmd)
    else:
        raise NotImplementedError


def get_config(_extrafiles=None, initdict=None, **kwargs):
    """get_config([extrafiles], [initdict=], [**kwargs])
Returns a RootContainer instance containing configuration parameters.
An extra dictionary may be merged in with the 'initdict' parameter.
And finally, extra options may be added with keyword parameters when calling
this.  """
    from pycopia import basicconfig
    files = []
    files.append(os.path.join(os.environ["HOME"], ".pycopiarc"))
    dbcf = basicconfig.get_config("storage.conf")
    if type(_extrafiles) is str:
        _extrafiles = [_extrafiles]
    if _extrafiles:
        files.extend(_extrafiles)
    url = dbcf.get("database", DEFAULT_URL)
    connection = connect(url)
    cache = dictlib.AttrDict()
    cf = RootContainer(connection, cache)
    #cache.flags = cf["flags"].copy()
    for f in files:
        if os.path.isfile(f):
            cf.mergefile(f)
    if type(initdict) is dict:
        cf.evalupdate(initdict)
    cf.update(kwargs)
    return cf


# performs an initial set up of the persistent storage. This usually only
# runs once, when first installing. This is the default structure for a
# new storage.
def _initialize(db):
    curs = db.cursor()
    curs.execute(
      """CREATE SEQUENCE public.config_seq_id INCREMENT 1 MINVALUE 1 MAXVALUE 2147483646 START 1 CACHE 1"""
    )
    curs.execute(
      """CREATE TABLE config (
        id integer NOT NULL DEFAULT nextval('public."config_seq_id"'), 
        key text NOT NULL, 
        type integer NOT NULL DEFAULT 0, 
        value text, 
        parent integer)"""
    )
#    flags = db["flags"] = PersistentAttrDict()
#    flags.VERBOSE = 0 # levels of verbosity
#    flags.DEBUG = 0 # levels of debugging
#    flags.INTERACTIVE = False # Don't run interactive tests also, by default
#    # collections of objects defined in the netobjects module.
#    db["users"] = PersistentAttrDict()    # for User objects
#    db["traps"] = PersistentAttrDict()    # for traps
#    db["devices"] = PersistentAttrDict()  # for Device subclasses
#    db["networks"] = PersistentAttrDict() # For Network objects
#    db["ipranges"] = PersistentAttrDict() # for IP range assignments
#    db["testbeds"] = PersistentAttrDict() # for testbeds (collections of Devices)
#    # default report spec
#    db["reports"] = PersistentAttrDict()  # For report constructors
#    db["reports"].default = ("StandardReport", "-", "text/ansi")
#    #
#    db["default"] = PersistentAttrDict()  # for root default values
#    db["default"].logbasename = "pycopia.log"
#    db["default"].logfiledir = "/var/tmp"
#    db["default"].reportbasename = "-"
#    # sub-package test configuration
#    unittests = db["unittests"] = PersistentAttrDict()  # For report constructors
#    unittests["aid"] = PersistentAttrDict()
#    unittests["utils"] = PersistentAttrDict() 
#    unittests["core"] = PersistentAttrDict()
#    unittests["CLI"] = PersistentAttrDict()
#    unittests["debugger"] = PersistentAttrDict()
#    unittests["process"] = PersistentAttrDict()
#    unittests["SMI"] = PersistentAttrDict()
#    unittests["mibs"] = PersistentAttrDict()
#    unittests["SNMP"] = PersistentAttrDict()
#    unittests["storage"] = PersistentAttrDict()
#    unittests["QA"] = PersistentAttrDict()
#    unittests["net"] = PersistentAttrDict()
#    unittests["audio"] = PersistentAttrDict()
#    unittests["XML"] = PersistentAttrDict()
#    unittests["WWW"] = PersistentAttrDict()
#    unittests["vim"] = PersistentAttrDict()


