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

Provides a persistent storage of objects for Pycopia applications. 

This is based on Durus:

http://www.mems-exchange.org/software/durus/

"""


import sys, os, re, itertools

from durus.client_storage import ClientStorage
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict
# Pycopia extension
from pycopia.durusplus.persistent_attrdict import PersistentAttrDict

from pycopia.aid import removedups
from pycopia.dictlib import AttrDict

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 2972


class Container(object):
    """Wrapper for a persistent dictionary providing attribute-style access.
    This class should be completely polymorphic with the
    durusplus.PersistentAttrDict class."""
    def __init__(self, container):
        self.__dict__["_container"] = container

    def __repr__(self):
        return "<Container>"

    # wrap any obtained PersistentDict objects to Container objects.
    def __getitem__(self, key):
        obj = self._container[key]
        if isinstance(obj, (PersistentDict, PersistentAttrDict)):
            return Container(obj)
        else:
            return obj

    def __setitem__(self, key, value):
        self._container[key] = value

    def __delitem__(self, key):
        del self._container[key]

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def _get_dict(self, name):
        d = self._container
        path = name.split(".")
        for part in path[:-1]:
            d = d[part]
        return d, path[-1]

    def getpath(self, key, default=None):
        d, key  = self._get_dict(key)
        if d is self._container:
            obj = self._container[key]
        else:
            try:
                obj = getattr(d, key)
            except (KeyError, AttributeError, NameError):
                return default
        if isinstance(obj, (PersistentDict, PersistentAttrDict)):
            return Container(obj)
        else:
            return obj

    def set(self, key, obj):
        self._container[key] = obj

    def delete(self, key):
        del self._container[key]

    def rename(self, oldkey, newkey):
        obj = self._container[oldkey]
        self._container[newkey] = obj
        del self._container[oldkey]

    # attribute-style access to container contents
    def __getattribute__(self, key):
        try:
            return super(Container, self).__getattribute__(key)
        except AttributeError:
            try:
                return self.__dict__["_container"].__getattribute__( key)
            except AttributeError:
                try:
                    obj = self.__dict__["_container"].__getitem__(key)
                    if isinstance(obj, (PersistentDict, PersistentAttrDict)):
                        return Container(obj) # wrap the returned mapping object also
                    else:
                        return obj
                except KeyError:
                    raise AttributeError, "Container: No attribute or key '%s' found." % (key, )

    def __setattr__(self, key, obj):
        if self.__class__.__dict__.has_key(key): # to force property access
            type.__setattr__(self.__class__, key, obj)
        elif self.__dict__.has_key(key): # existing local attribute
            self.__dict__[key] =  obj
        else:
            self.__dict__["_container"].__setitem__(key, obj)

    def __delattr__(self, key):
        try: # to force handling of properties
            self.__dict__["_container"].__delitem__(key)
        except KeyError:
            object.__delattr__(self, key)


class RootContainer(object):
    """The root container is special, it contains the computed methods, and a
    local writeable cache. It also supports path access using the dot as path separator. """
    def __init__(self, connection, container, cache=None):
        self.__dict__["_connection"] = connection
        self.__dict__["_container"] = container
        self.__dict__["_cache"] = cache or AttrDict() # local, non-persistent cache for computed and read-in values
        # cache-able objects
        self._cache._report = None
        self._cache._logfile = None
        self._cache._configurator = None

    def __repr__(self):
        return "<RootContainer>"

    def commit(self):
        self._connection.commit()

    def abort(self):
        self._connection.abort()

    def pack(self):
        self._connection.pack()

    # attribute-style access to container contents, also prefer the local cache.
    def __getattribute__(self, key):
        try:
            return super(RootContainer, self).__getattribute__(key)
        except AttributeError:
            try:
                return self.__dict__["_container"].__getattribute__( key)
            except AttributeError:
                try:
                    # check the local cache first, overrides persistent storage
                    obj = self.__dict__["_cache"].__getitem__(key)
                    if isinstance(obj, (PersistentDict, PersistentAttrDict)):
                        return Container(obj)
                    else:
                        return obj
                except KeyError:
                    pass
                try:
                    obj = self.__dict__["_container"].__getitem__(key) # the persistent container
                    if isinstance(obj, (PersistentDict, PersistentAttrDict)):
                        return Container(obj)
                    else:
                        return obj
                except KeyError:
                    raise AttributeError, "RootContainer: No attribute or key '%s' found." % (key, )

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

    def copy(self):
        return self.__class__(self._connection, self._container.copy(), self._cache.copy())

    # can get dot-delimited names from the root, for convenience.
    def _get_dict(self, name):
        d = self._container
        path = name.split(".")
        for part in path[:-1]:
            d = d[part]
        return d, path[-1]

    def __getitem__(self, key):
        try:
            return getattr(self._cache, key)
        except (AttributeError, KeyError, NameError):
            pass
        d, key  = self._get_dict(key)
        if d is self._container:
            obj = self._container[key]
        else:
            try:
                obj = getattr(d, key)
            except (KeyError, AttributeError, NameError):
                raise KeyError, "RootContainer: key %r not found." % (key,)
        if isinstance(obj, (PersistentDict, PersistentAttrDict)):
            return Container(obj)
        else:
            return obj

    def __setitem__(self, key, value):
        if self._cache.has_key(key):
            self._cache[key] = value
        else:
            d, key = self._get_dict(key)
            d[key] = value

    def __delitem__(self, key):
        if self._cache.has_key(key):
            del self._cache[key]
        else:
            d, key = self._get_dict(key)
            del d[key]

    def get(self, name, default=None):
        try:
            obj = self._cache[name]
        except KeyError:
            d, name  = self._get_dict(name)
            if d is self._container:
                #obj = self._container.get(name, default)
                try:
                    obj = getattr(self, name)
                except (KeyError, AttributeError, NameError):
                    return default
            else:
                try:
                    obj = d[name]
                except KeyError:
                    return default
        if isinstance(obj, (PersistentDict, PersistentAttrDict)):
            return Container(obj)
        else:
            return obj

    def set(self, key, obj):
        d, key = self._get_dict(key)
        d[key] = obj

    def delete(self, key):
        d, key = self._get_dict(key)
        del d[key]

    def keys(self):
        return removedups(self._container.keys()+self._cache.keys())

    def has_key(self, key):
        return self._container.has_key(key) or self._cache.has_key(key)

    def iteritems(self):
        return itertools.chain(self._cache.iteritems(), self._container.iteritems())

    def iterkeys(self):
        return itertools.chain(self._cache.iterkeys(), self._container.iterkeys())

    def itervalues(self):
        return itertools.chain(self._cache.itervalues(), self._container.itervalues())

    def add_container(self, name):
        obj = PersistentAttrDict()
        self._container[name] = obj
        self._connection.commit()
        return obj

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
            # Use setattr for attribute-dicts, properties, and other objects.
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
                #v = eval(v, vars(self), vars(self._container))
            except:
                if __debug__:
                    ex, val, tb = sys.exc_info()
                    print >>sys.stderr, "RootContainer conversion warning:", ex, val
                    print >>sys.stderr, repr(v)
        d = self._cache
        path = k.split(".") # allows for keys with dot-path 
        for part in path[:-1]:
            d = d[part]
        # Use setattr for attribute-dicts, properties, and other objects.
        setattr(d, path[-1], v) 

    def evalupdate(self, other):
        for k, v in other.items():
            self.evalset(k, v)

    ### computed attributes and properties follow

    changed = property(lambda s: bool(s._connection.changed))
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
        from pycopia import reports # XXX pycopia-QA dependency not listed
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


    # perform shell-like variable expansion
    _var_re = re.compile(r'\$([a-zA-Z0-9_\?]+|\{[^}]*\})')
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

##### end of RootContainer ######

class DB(object):
    def get_root(self, cache=None):
        root = self._connection.get_root()
        if len(root) == 0: # auto-initialize empty storage
            _initialize(root)
            self._connection.commit()
        return RootContainer(self._connection, root, cache)

    connection = property(lambda s: s._connection)
    root = property(get_root)
    changed = property(lambda s: bool(s._connection.changed))

    def commit(self):
        self._connection.commit()

    def abort(self):
        self._connection.abort()

    def pack(self):
        self._connection.pack()

    def add_container(self, dst, name):
        obj = PersistentAttrDict()
        dst[name] = obj
        self._connection.commit()
        return obj

class DBClient(DB):
    def __init__(self, host, port):
        self._connection = Connection(ClientStorage(host=host, port=port))

class DBFile(DB):
    def __init__(self, filename):
        self._connection = Connection(FileStorage(filename))


# client constructor
def get_client():
    from pycopia import basicconfig
    cf = basicconfig.get_config("storage.conf")
    host = cf.get("host", DEFAULT_HOST)
    port = cf.get("port", DEFAULT_PORT)
    del cf
    return DBClient(host, port)

def get_database(filename=None):
    if not filename:
        from pycopia import basicconfig
        cf = basicconfig.get_config("storage.conf")
        filename = cf.get("dbfile")
        del cf
    return DBFile(os.path.expandvars(os.path.expanduser(filename)))



def get_config(extrafiles=None, initdict=None, **kwargs):
    """get_config([extrafiles=], [initdict=], [**kwargs])
Returns a RootContainer instance containing configuration parameters.
An extra dictionary may be merged in with the 'initdict' parameter.
And finally, extra options may be added with keyword parameters when calling
this.  """
    from pycopia import socket
    SOURCES = []
    SOURCES.append(os.path.join(os.environ["HOME"], ".pycopiarc"))

    if type(extrafiles) is str:
        extrafiles = [extrafiles]
    if extrafiles:
        FILES = SOURCES + extrafiles
    else:
        FILES = SOURCES
    try:
        db = get_client()
    except socket.SocketError:
        db = get_database()
    cache = AttrDict()
    cf = db.get_root(cache)
    # copy default flags to cache so the don't get altered
    cache.flags = cf["flags"].copy()
    # initialize cache items to default values, so they can be altered at runtime.
    cf.update(cf["default"])
    for f in FILES:
        if os.path.isfile(f):
            cf.mergefile(f)
    if type(initdict) is dict:
        cf.evalupdate(initdict)
    cf.update(kwargs)
    return cf

# performs an initial set up of the persistent storage. This usually only
# runs once, when first installing. 
def _initialize(db):
    db["flags"] = PersistentAttrDict()
    db["flags"].VERBOSE = 0 # levels of verbosity
    db["flags"].DEBUG = 0 # levels of debugging
    db["flags"].NONOTE = False # Don't ask for a note in the testrunner
    db["flags"].NOINTERACTIVE = False # Run interactive tests also, by default
    # collections of objects defined in the netobjects module.
    db["users"] = PersistentAttrDict()    # for User objects
    db["traps"] = PersistentAttrDict()    # for traps
    db["devices"] = PersistentAttrDict()  # for Device subclasses
    db["networks"] = PersistentAttrDict() # For Network objects
    db["ipranges"] = PersistentAttrDict() # for IP range assignments
    db["testbeds"] = PersistentAttrDict() # for testbeds (collections of Devices)
    db["reports"] = PersistentAttrDict()  # For report constructors
    db["reports"].default = '("StandardReport", "-", "text/ansi")'
    db["default"] = PersistentAttrDict()  # for root default values
    db["default"].logbasename = "pycopia.log"
    db["default"].logfiledir = "/var/tmp"
    db["default"].reportbasename = "-"




