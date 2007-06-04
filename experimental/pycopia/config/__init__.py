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
This package is a collection of configuration objects. 

The 'get_config' factory function returns a GenericConfiguration object
populated with items from several sources.

"""
import sys, os, re

from basicconfig import ConfigHolder, SECTION


class GenericConfiguration(dict):
    def __init__(self, init={}):
        dict.__init__(self, init)
        # "hidden" dictionary for caching objects. "special" attributes are cached here.
        dict.__setattr__(self, "_cache", ConfigHolder() )
        self["default"] = SECTION("default")
        self._cache._report = None
        self._cache._logfile = None
    
    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __getitem__(self, key):
        # environment variables prefixed with "PYNMS_" override config settings.
        env = os.environ.get("PYNMS_%s" % key, None)
        if env is None:
             # You can specify the key by "path" name, dot delimited.
            if key.find(".") > 0:
                parts = key.split(".", 1)
                top = dict.__getitem__(self, parts[0])
                return top.__getitem__(parts[1])
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                try:
                    return self["default"][key]
                except KeyError:
                    raise KeyError, "no item '%s' in configuration or default section." % (key,)
        else:
            return env

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __getattribute__(self, key):
        try:
            return dict.__getattribute__(self, key)
        except AttributeError:
            try:
                return self.__getitem__(key)
            except KeyError:
                raise AttributeError, "no attribute or key '%s' found." % (key,)

    def __setattr__(self, key, obj):
        if self.__class__.__dict__.has_key(key): # to force property access
            dict.__setattr__(self, key, obj)
        else:
            dict.__setitem__(self, key, obj)

    def __delattr__(self, key):
        try: # to force handling of properties
            dict.__delitem__(self, key)
        except KeyError:
            dict.__delattr__(self, key)

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

    def write(self, fo):
        fo.write(repr(self))

    def mergefile(self, filename):
        if os.path.isfile(filename):
            gb = {} # temporary global namespace for config files.
            gb["SECTION"] = SECTION
            gb["sys"] = sys
            gb["os"] = os
            execfile(filename, gb, self)

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
        name = name or self.get("reportname", None)
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


def get_config(extrafiles=None, initdict=None, **kwargs):
    """get_config([extrafiles=], [initdict=], [**kwargs])
Returns a Configuration instance containing configuration parameters obtained
from the pynms.conf and user's ~/.pynmsrc files. Extra files to read can be passed
in as a list. An extra dictionary may be merged in with the 'initdict' parameter.
And finally, extra options may be added with keyword parameters when calling
this.  """
    SOURCES = []
    SOURCES.append(os.path.join(os.environ["PYNMS_HOME"], "etc", "pynms.conf"))
    SOURCES.append(os.path.join(os.environ["HOME"], ".pynmsrc"))
    if type(extrafiles) is str:
        extrafiles = [extrafiles]
    if extrafiles:
        FILES = SOURCES + extrafiles
    else:
        FILES = SOURCES
    cf = GenericConfiguration()
    #cf.reports = SECTION("reports")
    flags = SECTION("flags")
    flags.DEBUG = False
    flags.VERBOSE = False
    flags.NONOTE = False
    cf.flags = flags
    for f in FILES:
        if os.path.isfile(f):
            cf.mergefile(f)
    if type(initdict) is dict:
        cf.update(initdict)
    cf.update(kwargs)
    return cf

get_configuration = get_config


if __name__ == "__main__":
    os.environ["PYNMS_TEST"] = "get me"
    cf = get_config(initdict={"extra":"stuff"}, kwarg=3)
    print cf

