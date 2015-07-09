#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Pycopia Configuration and Information storage
---------------------------------------------

Provides runtime wrappers for persistent (database) objects with
extra methods for constructing active controllers.
"""


import sys, os, gc

from pycopia import logging
from sqlalchemy import and_

from pycopia import dictlib
from pycopia import aid
from pycopia import scheduler

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
        cache._userconfig = None

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
            except config.NoResultFound as err:
                raise AttributeError("RootContainer: No attribute or key '%s' found: %s" % (key, err))

    def __setattr__(self, key, obj):
        if key in self.__class__.__dict__: # to force property access
            type.__setattr__(self.__class__, key, obj)
        elif key in self.__dict__: # existing local attribute
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
            try:
                return self.get_userconfig().__getitem__(key)
            except KeyError:
                pass
        return super(RootContainer, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key in self._cache:
            self._cache[key] = value
        else:
            return super(RootContainer, self).__setitem__(key, value)

    def __delitem__(self, key):
        try:
            del self._cache[key]
        except KeyError:
            super(RootContainer, self).__delitem__(key)

    def get(self, key, default=None):
        try:
            rv = self.__getitem__(key)
        except KeyError:
            rv = default
        return rv

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
        if "," in name:
            params = []
            for n in name.split(","):
                rptparams = self.reports.get(n, None)
                if rptparams is None:
                    logging.warning("Reportname %r not found." % (n,))
                    continue
                params.append(rptparams)
        else:
            params = self.reports.get(name, None)
        if not params:
            raise reports.ReportFindError("Report %r not found." % (name,))
        if type(params) is list:
            params = map(self.expand_params, params)
        else:
            params = self.expand_params(params)
        return reports.get_report(params)

    def set_report(self, reportname):
        if type(reportname) is str:
            rep = self._build_report(reportname)
            self._cache._report = rep
        else:
            self._cache._report = reportname # hopefully a report object already

    def del_report(self):
        self._cache._report = None

    report = property(get_report, set_report, del_report, "report object")
    reportpath = property(lambda s: os.path.join(s.reportdir, s.reportbasename))

    def get_logfile(self):
        from pycopia import logfile
        if self._cache._logfile is None:
            logfilename = self.get_logfilename()
            try:
                lf = logfile.ManagedLog(logfilename, self.get("logfilesize", 1000000))
                if self.flags.VERBOSE:
                    logging.info("Logging to: {}".format(logfilename))
            except:
                logging.exception_warning("get_logfile: Could not open log file")
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
        Will set the owner to the currently running user. If already owned then
        a ConfigError will be raised.
        """
        if self._cache.get("_environment") is None:
            name = self.get("environmentname", "default")
            if name:
                db = self.session
                try:
                    env = db.query(models.Environment).filter(models.Environment.name==name).one()
                except config.NoResultFound as err:
                    raise config.ConfigError("Bad environmentname %r: %s" % (name, err))
                username = self.get("username") # username should be set by test runner
                if username:
                    if env.is_owned():
                        if env.owner.username != username:
                            raise config.ConfigError("Environment is currently owned by: %s" % (env.owner,))
                    env.set_owner_by_username(db, username)
                env = EnvironmentRuntime(db, env, self.logfile)
                self._cache["_environment"] = env
            else:
                raise config.ConfigError, "Bad environmentname %r." % (name,)
        return self._cache["_environment"]

    def _del_environment(self):
        envruntime = self._cache.get("_environment")
        if envruntime is not None:
            self._cache["_environment"] = None
            envruntime._environment.clear_owner(self.session)
            del envruntime._environment

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
            params = self.expand_params(params)
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

    def get_account(self, identifier):
        """Get account credentials by identifier."""
        db = self.session
        try:
            acct = db.query(models.LoginAccount).filter(models.LoginAccount.identifier==identifier).one()
        except config.NoResultFound as err:
            raise config.ConfigError("Bad account identifier %r: %s" % (identifier, err))
        return acct.login, acct.password

    def get_equipment(self, name):
        """Get any equipment runtime from the configuration by name."""
        db = self.session
        try:
            eqrow = db.query(models.Equipment).filter(models.Equipment.name.contains(name)).one()
        except config.NoResultFound as err:
            raise config.ConfigError("Bad equipment name %r: %s" % (name, err))
        return EquipmentRuntime(eqrow, "unspecified", self.get_logfile(), db)

    # user-specific configuration variables.
    # user configuration is explicit, contained in this "userconfig" attribute,
    # which maps to a configuration container that has the same name as the
    # current user, and configuration items owned by that user.
    def get_userconfig(self):
        if self._cache.get("_userconfig") is None:
            uc = self._build_userconfig()
            self._cache["_userconfig"] = uc
            return uc
        else:
            return self._cache["_userconfig"]

    def del_userconfig(self):
        self._cache["_userconfig"] = None

    userconfig = property(get_userconfig, None, del_userconfig,
                        "User specific configuration area.")

    def _build_userconfig(self):
        try:
            #username = self.__getitem__("username")
            username = self._cache["username"]
        except KeyError:
            username = os.environ["USER"]
        try:
            cont = self.get_container(username)
        except config.NoResultFound:
            self.add_container(username)
            cont = self.get_container(username)
        cont.register_user(username)
        return cont



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

    def get(self, name, default=None):
        return self._attributes.get(name, default)

    def __str__(self):
        s = []
        for teq in self._environment.testequipment:
            s.append(str(teq))
        return "%s:\n  %s" % (self._environment.name, "\n  ".join(s))

    def _get_DUT(self):
        try:
            return self._eqcache["DUT"]
        except KeyError:
            pass
        eq = EquipmentRuntime(
                self._environment.get_DUT(self._session),
                "DUT",
                self.logfile,
                self._session)
        self._eqcache["DUT"] = eq
        return eq

    DUT = property(_get_DUT)

    environment = property(lambda s: s._environment)

    owner = property(lambda s: s._environment.owner)

    def get_role(self, rolename):
        try:
            return self._eqcache[rolename]
        except KeyError:
            pass
        eq = self._environment.get_equipment_with_role(self._session, rolename)
        eq = EquipmentRuntime(eq, rolename, self.logfile, self._session)
        self._eqcache[rolename] = eq
        return eq

    def get_all_with_role(self, rolename):
        eqlist = self._environment.get_all_equipment_with_role(self._session, rolename)
        first = self._eqcache.get(rolename)
        if first:
            rlist = [first]
            rlist.extend([EquipmentRuntime(eq, rolename, self.logfile, self._session) for eq in eqlist if eq.name != first.name])
            return rlist
        else:
            rlist = [EquipmentRuntime(eq, rolename, self.logfile, self._session) for eq in eqlist]
            if rlist:
                self._eqcache[rolename] = rlist[0]
                return rlist
            else:
                raise config.ConfigError("No equipment with role {} available in environment.".format(rolename))

    def get_supported_roles(self):
        return self._environment.get_supported_roles(self._session)

    supported_roles = property(get_supported_roles)

    def clear(self):
        if self._eqcache:
            eqc = self._eqcache
            self._eqcache = {}
            while eqc:
                name, obj = eqc.popitem()
                try:
                    obj.clear()
                except:
                    logging.exception_error("environment clear: {!r}".format(obj))
        gc.collect()
        for obj in gc.garbage:
            try:
                obj.close()
            except:
                logging.exception_warning("environment garbage collect: {!r}".format(obj))
        del gc.garbage[:]
        scheduler.sleep(2) # some devices need time to fully clear or disconnect

    def __getattr__(self, name):
        try:
            return self.get_role(name)
        except:
            ex, val, tb = sys.exc_info()
            raise AttributeError("%s: %s" % (ex, val))

    # Allow persistent storage of environment state in the state attribute.
    def get_state(self):
        return self._environment.get_attribute(self._session, "state")

    def set_state(self, newstate):
        return self._environment.set_attribute(self._session, "state", str(newstate))

    def del_state(self):
        return self._environment.del_attribute(self._session, "state")

    state = property(get_state, set_state, del_state)


class EquipmentModelRuntime(object):
    def __init__(self, equipmentmodel):
        d = {}
        d["name"] = equipmentmodel.name
        d["manufacturer"] = equipmentmodel.manufacturer.name
        for prop in equipmentmodel.attributes:
            d[prop.type.name] = prop.value
        self._attributes = d

    def __str__(self):
        return "{} {}".format(self._attributes["manufacturer"], self._attributes["name"])

    def __getitem__(self, name):
        return self._attributes[name]

    def get(self, name, default=None):
        return self._attributes.get(name, default)

    @property
    def name(self):
        return self._attributes["name"]



class EquipmentRuntime(object):

    def __init__(self, equipmentrow, rolename, logfile, session):
        self.logfile = logfile
        self.name = equipmentrow.name
        self._equipment = equipmentrow
        self._session = session
        self._controller = None
        self._init_controller = None
        d = {}
        d["hostname"] = equipmentrow.name
        d["modelname"] = equipmentrow.model.name
        d["manufacturer"] = equipmentrow.model.manufacturer.name
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
        self._equipmentmodel = EquipmentModelRuntime(equipmentrow.model)

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

    def get(self, name, default=None):
        return self._attributes.get(name, default)

    def get_primary_interface(self):
        return self._equipment.interfaces[self._attributes.get("admin_interface", "eth0")]

    primary_interface = property(get_primary_interface)

    def get_controller(self):
        if self._init_controller is not None:
            self._init_controller = None
        if self._controller is None:
            self._controller = controller.get_controller(
                    self,
                    self["accessmethod"],
                    self.logfile)
        return self._controller

    controller = property(get_controller)

    def get_initial_controller(self):
        if self._init_controller is None:
            self._init_controller = controller.get_controller(
                    self,
                    self["initialaccessmethod"],
                    self.logfile)
        return self._init_controller

    initial_controller = property(get_initial_controller)

    def clear(self):
        if self._controller is not None:
            try:
                self._controller.close()
            except:
                logging.exception_warning("controller close: {!r}".format(self._controller))
            self._controller = None
        if self._init_controller is not None:
            try:
                self._init_controller.close()
            except:
                logging.exception_warning("initial controller close: {!r}".format(self._init_controller))
            self._init_controller = None

    def get_software(self):
        return SoftwareRuntime(self._equipment.software[0])

    software = property(get_software)

    # Easy persistent state of equipment. State is kept in the state attribute.
    def get_state(self):
        return self._equipment.get_attribute(self._session, "state")

    def set_state(self, newstate):
        return self._equipment.set_attribute(self._session, "state", str(newstate))

    state = property(get_state, set_state)

    model = property(lambda s: s._equipmentmodel)


class SoftwareRuntime(object):

    def __init__(self, software):
        self.name = software.name
        d = {}
        d["category"] = software.category.name
        d["manufacturer"] = software.manufacturer.name
        for prop in software.attributes: # These may override the attributes above.
            d[prop.type.name] = prop.value
        self._attributes = d

    def __getitem__(self, name):
        return self._attributes[name]


def get_config(_extrafiles=None, initdict=None, session=None, **kwargs):
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
    session = session or models.get_session()
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
    from pycopia import passwd
    if sys.flags.interactive:
        from pycopia import interactive
    cf = get_config()
    print cf
    print cf.flags
    print cf.flags.DEBUG
#    print cf.environment.DUT.state
    #cf.reportname = "default"
    #print cf.get("reportname")
    #print cf.report
    cf.username = passwd.getpwself().name
    cf.environmentname = "default"
    #env = cf._get_environment()
    env = cf.environment
    print "Environment:"
    print env
    print "Supported roles:"
    print env.get_supported_roles()
#    print env.get_role("testcontroller")
    #print env._get_DUT()
    #dut = env.DUT
    #print dut["default_role"]
    print (cf.environment._environment.owner)
    del cf.environment


