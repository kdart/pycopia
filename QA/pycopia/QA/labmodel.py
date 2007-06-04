#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
This module defines the objects in the test environment object model.
These represent objects in the lab, customer products, users, etc.
These are persistent in the persistent storage.

"""

import sys

from pycopia.aid import Enum

from pycopia.netobjects import Persistent, OwnedPersistent, PersistentList, PersistentDict, \
        PersistentAttrDict, NetworkDevice, Network, User, Interface, IPAssignments, \
        PersistentData, MANDATORY, CONTAINER, giveto, takeback


# abstract base classes
class _Device(NetworkDevice):
    "Tested Base Device."
    # user account
    user = "root"
    password = "root"
    accessmethod = "ssh" # any value supported by get_configurator constructor.
    initialaccessmethod = "console" # how to access for initial (before accessmethod is available) config
    snmpRwCommunity = "dartest" # RW SNMP community
    # possible device configuration states
    UNKNOWN = Enum(0, "UNKNOWN")
    UNCONFIGURED = Enum(1, "UNCONFIGURED") # in initial config prompt
    INITIALCONFIG = Enum(2, "INITIALCONFIG" ) # has been initially configured, but no additional configuration
    PARTIALCONFIG = Enum(3, "PARTIALCONFIG" ) # a config test was started, but not completed
    CONFIGURED = Enum(4, "CONFIGURED" ) # has a working configuration, but is not being used
    INUSE = Enum(5, "INUSE" ) # working configuration, and currently in use (data flow)
    CONFIG_STATES = [UNKNOWN, UNCONFIGURED, INITIALCONFIG, PARTIALCONFIG, CONFIGURED, INUSE]
    _configstate = UNKNOWN
    # Modes that the console may be found in
    LOGIN_MODE = Enum(0, "LOGIN_MODE") # normal login prompt
    CONFIG_MODE = Enum(1, "CONFIG_MODE") # initial config mode
    LOGGEDIN_MODE = Enum(2, "LOGGEDIN_MODE") # already logged in
    LOGGEDIN_ROOT_MODE = Enum(3, "LOGGEDIN_ROOT_MODE") # already logged in as root user

    def get_hosturl(self, scheme=None):
        scheme = scheme or self.accessmethod
        return "%s://%s:%s@%s/" % (scheme, self.user, self.password, self.name)

    def get_remote(self):
        """Returns a remote control object to interact with this device."""
        from pycopia.remote import Client
        return Client.get_remote(self.name.split(".")[0])

    def scp(self, rfile, dest, logfile=None):
        """Use the scp program to copy a file to or from this device."""
        from pycopia import sshlib
        return sshlib.scp(self.name, rfile, dest, user=self.user, password=self.password, logfile=logfile)

    def get_controller(self, logfile=None):
        raise NotImplementedError, "overide in subclass"

    def get_initial_controller(self, logfile=None):
        raise NotImplementedError, "overide in subclass"



class LinuxBox(NetworkDevice):
    "Linux based machine"
    user = "root"
    password = "root"
    accessmethod = "ssh"

    def scp(self, rfile, dest, logfile=None):
        """Use the scp program to copy a file to or from this device."""
        from pycopia import sshlib
        sshlib.scp(self.name, rfile, dest, user=self.user, password=self.password, logfile=logfile)

    def get_remote(self):
        """Returns a remote control object to interact with this device."""
        from pycopia.remote import Client
        return Client.get_remote(self.name.split(".")[0])

    def rcopy(self, src, dst):
        from pycopia.remote import Client
        agent = Client.get_remote(self.name.split(".")[0])
        Client.remote_copy(agent, src, dst)

    def rmove(self, src, dst):
        from pycopia.remote import Client
        agent = Client.get_remote(self.name.split(".")[0])
        Client.remote_copy(agent, src, dst)
        agent.unlink(src)


class _MSWindows(NetworkDevice):
    user = "Administrator"
    password = "admin123"
    accessmethod = "ssh" # depends on cygwin being installed

    def scp(self, rfile, dest, logfile=None):
        """Use the scp program to copy a file to or from this device."""
        from pycopia import sshlib
        sshlib.scp(self.name, rfile, dest, user=self.user, password=self.password, logfile=logfile)

    def get_remote(self):
        """Returns a remote control object to interact with this device."""
        from pycopia.remote import Client
        return Client.get_remote(self.name.split(".")[0])


class WindowsNT(_MSWindows):
    "Windows NT"
    pass

class WindowsXPPro(_MSWindows):
    "Windows XP Pro"
    pass

class WindowsXPHome(_MSWindows):
    "Windows XP Home"
    pass



class TestBed(PersistentData):
    """Collection of devices, in different roles, that comprise a test setup.
    This is called a "testbed". Its contained devices are allocated as a unit."""
    def __init__(self, name):
        super(TestBed, self).__init__()
        self.name = name
        self._items = PersistentDict()
        self.user = None # set by test runner at test run time


    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def set_owner(self, newowner):
        super(TestBed, self).set_owner(newowner)
        try:
            for device in self._items.values():
                giveto(device, newowner)
        except:
            self.disown()
            raise

    def disown(self):
        owner = self.get_owner()
        super(TestBed, self).disown()
        for device in self._items.values():
            try:
                takeback(device, owner)
            except:
                pass


class TestBedRuntime(object):
    def __init__(self, config, tb, logfile):
        self.config = config
        self.testbed = tb
        self.logfile = logfile

    def __getitem__(self, name):
        self.testbed[name]

    DUT = property(lambda s: s._items["DUT"])


def IPGetter(user, network):
    """Generator that returns available IP addresses for user and network combo."""
    assignments = user.possessions.ip_assignments
    while 1:
        for assignment in assignments:
            try:
                ip = assignment.get_next(network)
            except ValueError: # out of addressess
                return
            yield ip


def get_devices():
    """Return available device types in a list.  """
    return [ c for c in vars(sys.modules[__name__]).values() \
                if type(c) is type(object) \
                and c.__doc__ is not None \
                and issubclass(c, NetworkDevice) \
                and not c.__name__.startswith("_")]



if __name__ == "__main__":
    PLATFORMS = get_devices()
    print map(lambda o: o.__name__, PLATFORMS)

