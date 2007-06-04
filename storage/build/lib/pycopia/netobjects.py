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
Persistent network objects. Uses the Durus persistence library.

"""

import sys

try:
    from durus.persistent import Persistent
    from durus.persistent_list import PersistentList
    from durus.persistent_dict import PersistentDict
    # Pycopia extensions
    from pycopia.durusplus.persistent_data import PersistentData, MANDATORY, CONTAINER 
    from pycopia.durusplus.persistent_attrdict import PersistentAttrDict
except ImportError:
    print >>sys.stderr, "Warning: Durus persistence package is not installed. Objects will not persist."
    Persistent = object
    PersistentData = object
    PersistentList = list
    PersistentDict = dict
    from pycopia.dictlib import AttrDict
    PersistentAttrDict = AttrDict
    MANDATORY = "Mandatory"

from pycopia import ipv4
from pycopia.aid import IF


class OwnershipError(Exception):
    """Used for invalid object bindings"""
    pass

# This defines the ownership interface for all Pycopia ownable persistent objects.
# A User may own many objects, but any object has only one owner. 
class OwnedPersistent(Persistent):
    """base class for persistent objects that may be owned by a User."""
    def __init__(self):
        super(OwnedPersistent, self).__init__()
        self._owner = None

    def get_owner(self):
        return self._owner
    is_owned_by = get_owner

    def set_owner(self, newowner):
        assert isinstance(newowner, User), "owner must be a User object"
        if newowner._p_oid is None:
            raise OwnershipError, "cannot give objects to uncommited users."
        if self._owner is not None:
            if self._owner is newowner:
                return # already owner
            else:
                raise OwnershipError, "Object is already owned by %r" % (self._owner,)
        self._owner = newowner

    def disown(self):
        if self._owner is not None:
            self._owner = None

    def is_owned(self):
        return self._owner is not None

# function to bind users and objects
def giveto(obj, user):
    """Gives an ownable object to a User. """
    assert isinstance(user, User), "user must be a User object"
    assert hasattr(obj, "set_owner"), "object just have set_owner method"
    obj.set_owner(user)
    user.give(obj)

# function to unbind user from object
def takeback(obj, user=None):
    """Takes an ownable object from a User. The user parameter is optional, the
    objects current user will be used as the default."""
    user = user or obj.get_owner()
    assert isinstance(user, User), "user must be a User object"
    assert hasattr(obj, "disown"), "object just have disown method"
    if user:
        obj.disown()
        user.take(obj)


#### network model objects ###
class NetworkDevice(OwnedPersistent):
    """NetworkDevice([name])
This object is a persistent store object that represents a networked device as
a collection of interfaces. It has a name that is used for string conversion.
    """
    # the following (class-level attributes) become the default values for
    # various methods. Set an instance attribute of the same name to override
    # these values.
    user = None # default user to log in as
    password = None # default password for default user
    prompt = "# " # default CLI prompt for interactive sessions
    accessmethod = "ssh" # default. Possible are: ssh, console, serial, telnet, snmp
    initialaccessmethod = "console" # how to access for initial (before accessmethod is available) access
    console_server = (None, None) # host and TCP port used to connect to device serial console
    power_controller = (None, None) # APC host and outlet number used to control power
    monitor_port = (None, None) # may contain tuple of (device, interface) of an etherswitch to monitor
    domain = None # default DNS domain of the device
    nameservers = []       # default DNS server list to be configured
    ntpserver = None       # default NTP server to configure
    sysObjectID = None # The SNMP object identifier for a (sub)class of device.
    snmpRoCommunity = "public"     # default RO SNMP community to use
    snmpRwCommunity = "private"    # default RW SNMP community to use
    admin_interface = "eth0" # interface on administrative network. This interface is "invisible" to device methods.
    data_interfaces = ["eth0"] # the "business" interfaces that are in use.

    def __init__(self, name):
        super(NetworkDevice, self).__init__()
        self.name = self.hostname = str(name)
        self.INTERFACEMAP = PersistentDict()
        self._interfaces = PersistentDict()
        self.data_interfaces = PersistentList()
        self.admin_interface = None
        self.initialize() # subclass interface

    # a non-persistent dictionary to cache transient attributes from a device
    def _get_cache(self):
        try:
            return self.__dict__["_cache_"]
        except KeyError:
            from pycopia import dictlib
            c = dictlib.AttrDict()
            self.__dict__["_cache_"] = c
            return c
    _cache = property(_get_cache)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name # don't change this or you will break a lot of things 

    def initialize(self):
        pass

    def interface_alias(self, name, alias=None):
        """sets (or removes) an alias name for an interface."""
        if alias is not None:
            self.INTERFACEMAP[str(alias)] = str(name)
        else:
            del self.INTERFACEMAP[str(name)]

    def set_hostname(self, name):
        """Sets the hostname (and alias "name" attribute)."""
        self.name = self.hostname = str(name)

    def add_interface(self, devname, ipaddress=None, mask=None, hostname=None, 
                physaddress=None, ifindex=None, iftype=0):
        devname = self.INTERFACEMAP.get(devname, devname)
        if self._interfaces.has_key(devname):
            return
        if ipaddress is not None:
            ipaddress=ipv4.IPv4(ipaddress, mask)
        if not hostname:
            if ipaddress is not None:
                try:
                    hostname = ipaddress.hostname
                except:
                    hostname = self._get_ifname(devname)
                else:
                    if not hostname:
                        hostname = self._get_ifname(devname)
            else:
                hostname = self._get_ifname(devname)
        intf = Interface(devname, ipaddress, hostname, iftype, physaddress, ifindex)
        self._interfaces[devname] = intf
        intf.owner = self
        self._p_note_change()
        return intf

    def _get_ifname(self, devname):
        return "%s_%s" % (self.hostname.split(".")[0], devname)

    def update_interface(self, devname, address=None, mask=None, hostname=None, iftype=0):
        devname = self.INTERFACEMAP.get(devname, devname)
        return self._interfaces[devname].update(address, mask, hostname, iftype)

    def get_interface(self, devname):
        """Return an Interface object from the index. The index value may be an integer or a name.  """
        devname = self.INTERFACEMAP.get(devname, devname)
        return self._interfaces[devname]

    def set_interface(self, intf):
        if isinstance(intf, Interface):
            self._interfaces[intf.device] = intf
        else:
            raise ValueError, "interfaces: value must be Interface object."

    def del_interface(self, devname):
        """Delete an interface given the name, or index as an integer."""
        devname = self.INTERFACEMAP.get(devname, devname)
        intf = self._interfaces[devname]
        del self._interfaces[devname]
        intf.owner = None

    def get_interfaces(self):
        return self._interfaces.copy()

    def del_interfaces(self):
        self._interfaces.clear()

    interfaces = property(get_interfaces, None, del_interfaces, "device interfaces")

    # return a list of IPv4 addresses used by the data interfaces of this device.
    def _get_ipv4(self):
        rv = []
        for name in self.data_interfaces:
            intf = self._interfaces[name]
            rv.append(intf.address)
        return rv
    addresses = property(_get_ipv4)

    def get_address(self, ifname):
        return self._interfaces[ifname].address

    def reset(self):
        self._interfaces.clear()
        self.set_hostname("")
        self.disown()

    def connect(self, ifname, network):
        """Connect this device to a network object (the supplied parameter)."""
        assert isinstance(network, Network), "network parameter must be a Network object."
        ifname = self.INTERFACEMAP.get(ifname, ifname)
        try:
            intf = self._interfaces[ifname]
        except KeyError:
            intf = self.add_interface(ifname)
        intf.connect(network)

    def disconnect(self, ifname):
        """disconnect the named interface from its network."""
        ifname = self.INTERFACEMAP.get(ifname, ifname)
        intf = self._interfaces[ifname]
        intf.disconnect()

    def connections(self, network=None):
        """Return a list of interfaces connected to the given network object,
        or all connections if no network provided."""
        rv = []
        for intf in self._interfaces.values():
            if network is None and intf.network is not None:
                rv.append(intf)
            elif intf.network is network:
                rv.append(intf)
        return rv

class Host(NetworkDevice):
    pass

class Router(NetworkDevice):
    pass

class EtherSwitch(NetworkDevice):
    pass

class SwitchRouter(Router, EtherSwitch):
    pass

class Interface(Persistent):
    def __init__(self, devname, address=None, name="", 
                iftype=0, physaddress=None, ifindex=None):
        super(Interface, self).__init__()
        self.address = address
        self.devname = devname # a device name (e.g. "eth0")
        self.hostname = name # a "friendly" name (e.g. "Ethernet 1") or DNS name
        self.iftype = iftype # type of interface
        self.network = None # network object this interface is attached to
        self.owner = None # the owner (device) this interface belongs to
        self.physaddress = physaddress
        self.ifindex = ifindex
        self._subinterfaces = PersistentDict()

    def __str__(self):
        return "%s (%s): ipaddress=%s, physaddress=%s" % \
                (self.devname, self.hostname, self.address, self.physaddress)

    def __cmp__(self, other):
        return cmp(self.devname, other.devname)

    def connect(self, network):
        """connect(netobject)
Connect this interface object to a network object (the supplied parameter)."""
        network.add_interface(self)

    def disconnect(self):
        if self.network:
            self.network.del_interface(self)
            self.address = None
            self.hostname = self.name = ""

    def add_subinterface(self, devname, address=None, mask=None, hostname=None, ifindex=None):
        intf = Interface(devname, address, mask, hostname, self.iftype, ifindex)
        self._subinterfaces[devname] = intf
        return intf

    def set_subinterface(self, subint):
        if isinstance(subint, Interface):
            self._subinterfaces[subint.device] = subint
            return subint
        else:
            raise ValueError, "subinterface must be another Interface object."

    def get_subinterface(self, subint):
        return self._subinterfaces[subint]

    def update(self, address=None, mask=None, hostname=None, iftype=None):
        if address is not None:
            self.address = ipv4.IPv4(address, mask)
            if not hostname:
                self.hostname = self.name = self.address.gethost()
        if hostname:
            self.hostname = self.name = str(hostname)
        if iftype:
            self.iftype = iftype

    # mapping interface for subinterface objects
    def __getitem__(self, subint):
        return self._subinterfaces[subint]

    def __len__(self):
        return len(self._subinterfaces)

    def __iter__(self):
        return iter(self._subinterfaces)


class Network(OwnedPersistent):
    _netnode_template = """|  +---------------------------------------------+
|--| %-20.20s (%-20.20s) |
|  +---------------------------------------------+""" # don't touch this 
    def __init__(self, subnet=None, subnetname=None):
        super(Network, self).__init__()
        self.name = None
        self.mask = None
        self._subnets = PersistentList()
        self.nodes = PersistentDict() # actually, Interface objects
        self._gatways = PersistentList()
        if subnet:
            self.add_subnet(subnet, subnetname)

    def __str__(self):
        s = ["-"*70]
        sbl = []
        sn = []
        for subnet, name in self._subnets:
            sbl.append("%20s" % (subnet,))
            sn.append("%20s" % (name,))
        s.append(" | ".join(sbl))
        s.append(" | ".join(sn))
        s.append("-"*70)
        for node in self.nodes.values():
            s.append(self._netnode_template % (node.owner.name, node.owner.__class__.__name__))
        return "\n".join(s)

    def __repr__(self):
        try:
            addr, name = self._subnets[0]
            return "%s(%r, %r)" % (self.__class__.__name__, addr, name)
        except IndexError:
            return "%s()" % (self.__class__.__name__)

    def __getitem__(self, idx):
        return self._subnets[idx]

    def __iter__(self):
        return iter(self._subnets)

    def add_interface(self, interface):
        self.nodes[interface.hostname] = interface
        interface.network = self

    def del_interface(self, interface):
        del self.nodes[interface.hostname]
        interface.network = None

    def get_interfaces(self):
        return self.nodes.copy()

    def get_node(self, hostname):
        intf = self.nodes[str(hostname)]
        return intf.owner

    def add_node(self, netdev):
        for intf in netdev.interfaces.values():
            for subnet, name in self._subnets:
                if intf.address in subnet:
                    self.nodes[intf.name] = intf
                    intf.network = self
                    return

    def add_subnet(self, addr, name=None):
        sn = ipv4.IPv4(addr)
        sn.host = 0
        name = name or sn.cidr() 
        if not self._subnets: # first subnet sets the name and mask
            self.name = name
            self.mask = sn.mask 
        self._subnets.append((sn, name))
        self._p_note_change()
        return sn
    
    def remove_subnet(self, name):
        for i, (sn, netname) in enumerate(self._subnets[:]):
            if netname == name:
                del self._subnets[i]

    def get_subnets(self):
        return list(self._subnets)
    subnets = property(get_subnets)

    def __contains__(self, address):
        if isinstance(address, str):
            address = ipv4.IPv4(address)
        for subnet, name in self._subnets:
            if address in subnet:
                return True
        return False


# Stores a particular command invocation. 
class Program(Persistent):
    """Program(name, [options], **kwargs)
Represents a saved state of a commandline utility and all of its options. The
optional 'options' argument is a dictionary of option-value pairs that will be
added to the long options list (minus the preceding dashes)."""
    def __init__(self, name, options=None, **kwargs):
        self.name = name
        self._opts = {}
        self._longopts = kwargs
        if type(options) is dict: # dictionary of option-name: value pairs
            self._longopts.update(options)

    def add_opt(self, name, value=None):
        self._opts[name] = value
        self._p_note_change()

    def del_opt(self, name):
        del self._opts[name]
        self._p_note_change()

    def add_longopt(self, name, value=None):
        self._longopts[name] = value
        self._p_note_change()

    def del_longopt(self, name):
        del self._longopts[name]
        self._p_note_change()

    def _opt_helper(self, nvt):
        name, val = nvt
        if val is None:
            return "-%s" % name
        else:
            return "-%s %s" % (name, val)

    def _longopt_helper(self, nvt):
        name, val = nvt
        if val is None:
            return "--%s" % name
        else:
            return "--%s=%r" % (name, val)

    def __str__(self):
        opts = " ".join(map(self._opt_helper, self._opts.items()) + \
                    map(self._longopt_helper, self._longopts.items()))
        return "%s %s" % (self.name, opts)


class UserPossessions(PersistentDict):
    def get_all(self, typefilt):
        rv = []
        for obj in self.values():
            if isinstance(obj, typefilt):
                rv.append(obj)
        return rv

    # return all Devices in this users possession
    def get_all_devices(self):
        return self.get_all(NetworkDevice)
    devices = property(get_all_devices)

    # return all networks in this users possession
    def get_all_networks(self):
        return self.get_all(Network)
    networks = property(get_all_networks)

    # get all IP assignments in this users possession
    def get_all_ip(self):
        return self.get_all(IPAssignments)
    ip_assignments = property(get_all_ip)


class User(Persistent):
    def __init__(self, loginname, longname=None):
        super(User, self).__init__()
        self.name = str(loginname)
        self.longname = longname
        self.possessions = UserPossessions()
        self._prefs = PersistentAttrDict()
        self.initialize()

    def initialize(self):
        pass

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.longname)

    # object ownership - give and take things to/from the user
    def give(self, obj):
        if obj._p_oid is None:
            raise ValueError, "cannot give uncommited object to user"
        self.possessions[obj._p_oid] = obj
        self._p_note_change()

    def take(self, obj):
        ido = obj._p_oid
        if self.possessions.has_key(ido):
            del self.possessions[ido]
            self._p_note_change()

    def has(self, obj):
        return self.possessions.has_key(obj._p_oid)

    def inventory(self):
        return self.possessions.values()

    # user preferences for various things
    def get_prefs(self):
        return self._prefs
    prefs = property(get_prefs)

    def set_pref(self, name, obj):
        self._prefs[name] = obj

    def get_pref(self, name):
        d = self._prefs
        path = name.split(".")
        for part in path[:-1]:
            d = d[part]
        return d[path[-1]]


# manages ranges of IP address 
class IPAssignments(OwnedPersistent):
    def __init__(self, name, *args):
        super(IPAssignments, self).__init__()
        self.name = name
        self._store = PersistentDict()
        for arg in args:
            self.add(arg)

    def __contains__(self, address):
        if isinstance(address, str):
            address = ipv4.IPv4(address)
        for ip in self._store.iterkeys():
            if address == ip:
                return True
        return False

    def __str__(self):
        s = []
        for address, disp in self._store.items():
            s.append("%s is %s\n" % (address.cidr(), IF(disp, "used.", "free.")))
        s.sort()
        return "".join(s)

    def __repr__(self):
        return "%s(%r, ...)" % (self.__class__.__name__, self.name)

    def __iter__(self):
        return self._store.iteritems()

    def get(self, ip):
        if isinstance(ip, str):
            ip = ipv4.IPv4(ip)
        return ip, self._store.get(ip)

    def add(self, arg):
        if isinstance(arg, str):
            arg = ipv4.IPv4(arg)
        if isinstance(arg, ipv4.IPRange):
            for ip in arg:
                self._store[ip] = False
        elif isinstance(arg, ipv4.IPv4):
            for ip in arg[1:-1]:
                self._store[ip] = False
        else:
            raise ValueError, "must be IP address or Range."

    # IPv4 used as a VLSM range here
    def add_net(self, ipnet):
        if isinstance(ipnet, str):
            ipnet = ipv4.IPv4(ipnet)
        if isinstance(ipnet, ipv4.IPv4):
            for ip in ipnet[1:-1]:
                self._store[ip] = False
        else:
            raise ValueError, "must add IPv4 network"
    add_network = add_net
    
    def add_range(self, addr1, addr2):
        rng = ipv4.IPRange(addr1, addr2)
        for ip in rng:
            self._store[ip] = False

    def remove(self, arg):
        if isinstance(arg, str):
            arg = ipv4.IPv4(arg)
        if isinstance(arg, ipv4.IPRange):
            for ip in arg:
                try:
                    del self._store[ip]
                except KeyError:
                    pass
        elif isinstance(arg, ipv4.IPv4):
            for ip in arg[1:-1]:
                try:
                    del self._store[ip]
                except KeyError:
                    pass
        else:
            raise ValueError, "must be IP address or Range."

    # removes the given range of IP. Useful for making "holes"
    def remove_range(self, addr1, addr2):
        rng = ipv4.IPRange(addr1, addr2)
        for ip in rng:
            try:
                del self._store[ip]
            except KeyError:
                pass

    def remove_net(self, ipnet):
        if isinstance(ipnet, str):
            ipnet = ipv4.IPv4(ipnet)
        if isinstance(ipnet, ipv4.IPv4):
            for ip in ipnet[1:-1]:
                try:
                    del self._store[ip]
                except KeyError:
                    pass
        else:
            raise ValueError, "must add IPv4 network"

    def allocate(self, address):
        if isinstance(address, str):
            address = ipv4.IPv4(address)
        self._store[address] = True

    def deallocate(self, address):
        if isinstance(address, str):
            address = ipv4.IPv4(address)
        try:
            self._store[address] = False
        except KeyError:
            pass

    def reset(self):
        """deallocate all addressess"""
        for addr in self._store.iterkeys():
            self._store[addr] = False

    def clear(self):
        """remove all addresses."""
        self._store.clear()

    # find next available IP address. Raise ValueError if exhausted.
    # If Network is supplied, only pick an IP in that network.
    def get_next(self, network=None):
        for addr, allocated in self._store.items():
            if allocated:
                continue
            if network is not None:
                if addr in network:
                    self._store[addr] = True
                    return addr
                else:
                    continue
            else:
                self._store[addr] = True
                return addr
        raise ValueError, "No more addresses availiable in the assignment"



# XXX experimental
class Resource(OwnedPersistent):
    """Resource(object)
A container object that manages a resource. The resource may be any object.  """
    def __init__(self, name, obj):
        super(Resource, self).__init__()
        self.name = name
        self._obj = obj


def get_devices():
    """Return available device types in a list.  """
    return [ c for c in vars(sys.modules[__name__]).values() \
                if type(c) is type(object) \
                and issubclass(c, NetworkDevice) \
                and not c.__name__.startswith("_")]


