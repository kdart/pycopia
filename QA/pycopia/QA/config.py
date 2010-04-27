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

Provides runtime wrappers for persistent (database) objects with
extra methods for constructing active controllers.
"""


import sys, os, re
import logging

from sqlalchemy import and_

from pycopia import dictlib
from pycopia import aid

from pycopia.db import models
from pycopia.db import config

from pycopia.QA import controller

Config = models.Config


class RootContainer(config.Container):
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
        if key == "__dict__":
            return object.__getattribute__(self, key)
        try:
            # check the local cache first, overrides persistent storage
            return self.__dict__["_cache"].__getitem__(key)
        except KeyError:
            pass
        try:
            return super(RootContainer, self).__getattribute__(key)
        except AttributeError:
            node = self.__dict__["node"]
            session = self.__dict__["session"]
            try:
                item = config.get_item(session, node, key)
                if item.value is aid.NULL:
                    return config.Container(session, item)
                else:
                    return item.value
            except config.NoResultFound, err:
                raise AttributeError("RootContainer: No attribute or key '%s' found: %s" % (key, err))

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

    def copy(self):
        return self.__class__(self.session, self.node, self._cache.copy())

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
                v = eval(v, {}, vars(self))
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
                logging.warn("get_logfile: Could not open log file: %s: %s" % (ex, val))
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
                db = self.session
                try:
                    env = db.query(models.Environment).filter(models.Environment.name==name).one()
                except config.NoResultFound, err:
                    raise config.ConfigError("Bad environmentname %r: %s" % (name, err))
                env = EnvironmentRuntime(db, env, self.logfile)
                self._cache["_environment"] = env
            else:
                raise config.ConfigError, "Bad environmentname %r." % (name,)
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
        """Remove the UI object from the cache."""
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

# Runtime objects that bind sessions and database rows and provide helper
# methods and properties. Attributes table is made available using the
# mapping interface (getitem).

class EnvironmentRuntime(object):
    def __init__(self, session, environmentrow, logfile):
        self._session = session
        self._environment = environmentrow
        self._eqcache = {}
        self.logfile = logfile
        d = {}
        for prop in environmentrow.attributes:
            d[prop.type.name] = prop.value
        self._attributes = d

    def __getitem__(self, name):
        return self._attributes[name]

    def __str__(self):
        s = []
        for teq in self._environment.testequipment:
            s.append(str(teq))
        return "%s:\n  %s" % (self._environment.name, "\n  ".join(s))

    def _get_DUT(self):
        return EquipmentRuntime(
                self._environment.get_DUT(self._session), 
                "DUT",
                self.logfile)

    DUT = property(_get_DUT)

    environment = property(lambda s: s._environment)

    def get_role(self, rolename):
        try:
            return self._eqcache[rolename]
        except KeyError:
            pass
        eq = self._environment.get_equipment_with_role(self._session, rolename)
        eq = EquipmentRuntime(eq, rolename, self.logfile)
        self._eqcache[rolename] = eq
        return eq

    def get_supported_roles(self):
        return self._environment.get_supported_roles(self._session)

    supported_roles = property(get_supported_roles)

    def __getattr__(self, name):
        try:
            return self.get_role(name)
        except:
            ex, val, tb = sys.exc_info()
            raise AttributeError("%s: %s" % (ex, val))


class EquipmentRuntime(object):

    def __init__(self, equipmentrow, rolename, logfile):
        self.logfile = logfile
        self.name = equipmentrow.name
        self._equipment = equipmentrow
        self._controller = None
        self._init_controller = None
        d = {}
        d["hostname"] = equipmentrow.name
        d["role"] = rolename
        if equipmentrow.software:
            d["default_role"] = equipmentrow.software[0].category.name
        else:
            d["default_role"] = None
        for prop in equipmentrow.attributes: # These may override the attributes above.
            d[prop.type.name] = prop.value
        if equipmentrow.account: # Account info takes precedence
            d["login"] = equipmentrow.account.login
            d["password"] = equipmentrow.account.password
        self._attributes = d

    def get_url(self, scheme=None, port=None, path=None, with_account=False):
        attribs = self._attributes
        s = [scheme or attribs.get("serviceprotocol", "http")]
        s.append("://")
        if with_account:
            login = attribs.get("login")
            if login:
              pwd = attribs.get("password")
              if pwd:
                s.append("%s:%s" % (login, pwd))
              else:
                s.append(login)
              s.append("@")
        s.append(attribs["hostname"])
        port = attribs.get("serviceport", port)
        if port:
            s.append(":") ; s.append(str(port))
        s.append(path or attribs.get("servicepath", "/"))
        return "".join(s)

    URL = property(get_url)

    def __str__(self):
        return self._equipment.name

    def __getattr__(self, name):
        return getattr(self._equipment, name)

    def __getitem__(self, name):
        return self._attributes[name]

    def __del__(self):
        if self._controller is not None:
            try:
                self._controller.close()
            except:
                pass

    def get_controller(self):
        if self._init_controller is not None:
            self._init_controller = None
        if self._controller is None:
            self._controller = controller.get_controller(
                    self,
                    self["accessmethod"], 
                    self.logfile)
        return self._controller

    def get_initial_controller(self):
        if self._init_controller is None:
            self._init_controller = controller.get_controller(
                    self,
                    self["initialaccessmethod"], 
                    self.logfile)
        return self._init_controller

    controller = property(get_controller)

    initial_controller = property(get_initial_controller)



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
    rootnode = config.get_root(session)
    cache = dictlib.AttrDict()
    flags = dictlib.AttrDict()
    # copy flag values to cache so changes don't persist.
    flagsnode = session.query(Config).filter(and_(Config.parent_id==rootnode.id,
                Config.name=="flags")).one()
    for valnode in flagsnode.children:
        flags[valnode.name] = valnode.value
    cache.flags = flags
    cf = RootContainer(session, rootnode, cache)
    for f in files:
        if os.path.isfile(f):
            cf.mergefile(f)
    if type(initdict) is dict:
        cf.evalupdate(initdict)
    cf.update(kwargs)
    controller.initialize(cf)
    return cf


if __name__ == "__main__":
    from pycopia import autodebug
    if sys.flags.interactive:
        from pycopia import interactive
    cf = get_config()
    print cf
    print cf.flags
    print cf.flags.DEBUG
    #cf.reportname = "default"
    #print cf.get("reportname")
    #print cf.report
    #env = cf.environment
    #print "Environment:"
    #print env
    #print "Supported roles:"
    #print env.get_supported_roles()
    #print env.get_role("testcontroller")
    #print env._get_DUT()
    #dut = env.DUT
    #print dut["default_role"]


