#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
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
Experimental persistent ConfigHolder.

"""

import sys, os

from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict

from basicconfig import ConfigHolder

class SECTION(PersistentDict):
    def __init__(self, name):
        self.__dict__["name"] = name
        super(SECTION, self).__init__()


class GenericConfiguration(PersistentDict):
    def __init__(self, init={}):
        self.__dict__["data"] = {}
        #PersistentDict.__init__(self, init)
        #super(GenericConfiguration, self).__init__(init)
        # "hidden" dictionary for caching objects. "special" attributes are cached here.
        #PersistentDict.__setattr__(self, "_cache", ConfigHolder() )
        super(GenericConfiguration, self).__setattr__("_cache", ConfigHolder() )
        self._cache._report = None
        self._cache._logfile = None
    
    def __getitem__(self, key):
         # You can specify the key by "path" name, dot delimited.
        if key.find(".") > 0:
            parts = key.split(".", 1)
            #top = PersistentDict.__getitem__(self, parts[0])
            top = super(GenericConfiguration, self).__getitem__(parts[0])
            return top.__getitem__(parts[1])
        try:
            #return PersistentDict.__getitem__(self, key)
            return super(GenericConfiguration, self).__getitem__(key)
        except KeyError:
            try:
                return self["default"][key]
            except KeyError:
                raise KeyError, "no item '%s' in configuration or default section." % (key,)

    def __setitem__(self, key, value):
        super(GenericConfiguration, self).__setitem__(key, value)
        #PersistentDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        super(GenericConfiguration, self).__delitem__(key)
        #PersistentDict.__delitem__(self, key)

    def __getattribute__(self, key):
        try:
            return super(GenericConfiguration, self).__getattribute__(key)
            #return PersistentDict.__getattribute__(self, key)
        except AttributeError:
            try:
                return self.__getitem__(key)
            except KeyError:
                raise AttributeError, "no attribute or key '%s' found." % (key,)

    def __setattr__(self, key, obj):
        if self.__class__.__dict__.has_key(key): # to force property access
            super(GenericConfiguration, self).__setattr__(key, obj)
            #PersistentDict.__setattr__(self, key, obj)
        else:
            super(GenericConfiguration, self).__setitem__(key, obj)
            #PersistentDict.__setitem__(self, key, obj)

    def __delattr__(self, key):
        try: # to force handling of properties
            super(GenericConfiguration, self).__delitem__(key)
            #PersistentDict.__delitem__(self, key)
        except KeyError:
            super(GenericConfiguration, self).__delattr__(key)
            #PersistentDict.__delattr__(self, key)

    def __str__(self):
        s = map(lambda it: "%s = %r" % (it[0], it[1]), self.items())
        s.sort()
        return "\n".join(s)

    def update(self, other):
        for k, v in other.items():
            setattr(self, k, v) # so that the properties are handled right

    # have to use getattr so that the property objects may also be returned.
    def get(self, name, default=None):
        try:
            val = getattr(self, name)
        except AttributeError:
            return default
        else:
            return val

    def DEFER(self, name):
        """Allows putting references in the config file that won't be evaluated
    until the time it is fetched."""
        return _getter(self, name)

    # report object constructor
    def get_report(self):
        if self._cache._report is None:
            rep = self._build_report(None)
            self._cache._report = rep
            return rep
        else:
            return self._cache._report

    def _build_report(self, name):
        import reports
        if name is None:
            name = self.get("reportname", None)
        params = self.reports.get(name, (None,))
        return reports.get_report( params )

    def set_report(self, reportname):
        if type(reportname) is str:
            rep = self._build_report(reportname)
            self._cache._report = rep
        else:
            self._cache._report = reportname # hopefully a report object already

    def del_report(self):
        self._cache._report = None
    report = property(get_report, set_report, del_report, "reporting object")

    def get_logfilename(self):
        return os.path.join(os.path.expandvars(self.logfiledir), self.logbasename)
    logfilename = property(get_logfilename, None, None, "full name of log file.")

    def get_logfile(self):
        import logfile
        if self._cache._logfile is None:

            logfilename = self.get_logfilename()
            try:
                lf = logfile.ManagedLog(logfilename, self.logfilesize)
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

# helper for DEFERing
class _getter(object):
    def __init__(self, cf, name):
        self._cf = cf
        self._name = name
    def __call__(self):
        return self._cf.get(self._name)


#get_configuration = get_config



def get_config():
    connection = Connection(FileStorage("/var/tmp/test.durus"))
    root = connection.get_root() # connection set as shown above.
    if not root.has_key("_pconfig"):
        cf = GenericConfiguration()
        root["_pconfig"] = cf
        root["_pconfig"]["default"] = SECTION()
        connection.commit()
    return root["_pconfig"]


def _test(argv):
    cf = get_config()
    print cf
    return cf

if __name__ == "__main__":
    cf = _test(sys.argv)

