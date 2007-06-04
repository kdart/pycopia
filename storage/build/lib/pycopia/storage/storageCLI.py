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
CLI interface to the Pycopia storage.

"""

import sys, os

from pycopia import CLI

from pycopia import netobjects
from pycopia.storage import Storage


class StorageCLI(CLI.BaseCommands):

    def initialize(self):
        self._we_locked = False

    def edit(self, argv):
        """edit
    Allows editing database starting from root storage."""
        # first, check if it is being edited already.
        root = self._obj.get_root()
        if root.get("_LOCK") and not self._we_locked:
            self._print("Database is locked. Please try again later.")
            return
        cmd = self.clone(RootContainerEditor)
        cmd._setup(root, "root")
        raise CLI.NewCommand, cmd

    def lock(self, argv):
        """lock
    Set a flag in the database to indicate it is locked. Other users will not
    be able to make changes."""
        root = self._obj.get_root()
        if root.get("_LOCK"):
            self._print("Already locked.")
            return
        root["_LOCK"] = True
        self._we_locked = True
        self._obj.commit()

    def unlock(self, argv):
        """unlock
    Resets a flag in the database to indicate that it is unlocked. Other users
    will be able to make changes."""
        root = self._obj.get_root()
        root["_LOCK"] = False
        self._obj.commit()

    def commit(self, argv):
        """commit
    Commits a pending transation."""
        self._obj.commit()

    def abort(self, argv):
        """abort
    Aborts a pending transation."""
        self._obj.abort()

    def pack(self, argv):
        """pack
    Packs the database into a more compact form. Since new entries are only
    appended in Durus, this must be done periodically."""
        root = self._obj.get_root()
        root["_LOCK"] = False
        self._obj.commit()
        self._obj.pack()


class ContainerEditor(CLI.BaseCommands):
    def _setup(self, cf, name):
        self._obj = cf
        self._environ["PS1"] = "{%s}> " % (name, )
        self._reset_scopes()

    def _reset_scopes(self):
        global _EDITORS
        names = self._obj.keys()
        self.add_completion_scope("show", names)
        self.add_completion_scope("info", names)
        self.add_completion_scope("cd", names)
        self.add_completion_scope("ls", names)
        self.add_completion_scope("set", names)
        self.add_completion_scope("get", names)
        self.add_completion_scope("delete", names)
        self.add_completion_scope("edit", names)
        self.add_completion_scope("add", [ n.__name__ for n in _EDITORS.keys()])

    def ls(self, argv):
        """ls [<obj>...]
    List contents of current container, or given containers."""
        if len(argv) < 2:
            self._list_container(self._obj)
        else:
            for arg in argv[1:]:
                try:
                    obj = self._obj[arg]
                except (KeyError, IndexError):
                    self._print("No such object: %s" % (arg,))
                else:
                    if hasattr(obj, "iteritems"):
                        self._list_container(obj)
                    else:
                        self._print(obj)
    dir = ls # alias

    def _list_container(self, obj):
        names = obj.keys()
        names.sort()
        for name in names:
            self._print("%22.22s: %r" % (name, obj[name]))

    def commit(self, argv):
        """commit
    Commit changes to the database now."""
        global _stores
        for _storageuser in _stores.values():
            _storageuser.commit()

    def up(self, argv):
        """up
    Move up in the object space."""
        raise CLI.CommandQuit

    def show(self, argv):
        """show <object>
    Show an object."""
        if len(argv) > 1:
            for arg in argv[1:]:
                obj = getattr(self._obj, arg)
                self._print(repr(obj))
        else:
            self._print(repr(self._obj))

    def info(self, argv):
        """info <object>...
    Show detailed information about an object."""
        for arg in argv[1:]:
            obj = self._obj.get(arg)
            self._print("Type: %s" % (type(obj),))
            if hasattr(obj, "__doc__") and obj.__doc__ is not None:
                self._print("Docstring:")
                self._print(obj.__doc__)
            self._print("Attributes:")
            self._print_list(filter(lambda s: not s.startswith("__"), dir(obj)), 2)

    def cd(self, argv):
        """cd <object>
    Change the current context to the given container object."""
        name = argv[1]
        if name == "..":
            raise CLI.CommandQuit
        obj = self._obj.get(name)
        if obj is not None:
            cmd = get_editor(self, obj, name)
            if cmd:
                raise CLI.NewCommand, cmd
            else:
                self._print("%r is not a container or editable object (it is a %s)." % (name, type(obj)))
        else:
            self._print("No such container.")

    def edit(self, argv):
        """edit  <object>
    Interactively edit an object's attributes."""
        name = argv[1]
        obj = self._obj.get(name)
        if obj is not None:
            cmd = get_editor(self, obj, name)
            if cmd:
                raise CLI.NewCommand, cmd
            else:
                self._print("Cannot edit this object. Use 'set' to edit a simple attribute.")
        else:
            self._print("No such object.")
            return

    def add(self, argv):
        """add <objectname> <objname>...
    Adds the specified type of object to the database."""
        objname = argv[1]
        name = argv[2]
        obj = _get_object_by_name(objname)
        inst  = obj(*tuple(argv[3:])) # remaining args go to constructor
        self._obj[name] = inst
        self._reset_scopes()
    
    def add_container(self, argv):
        """add_container <name>
    Adds a new container in the current location."""
        global _stores
        name = argv[1]
        new = netobjects.PersistentAttrDict()
        self._obj[name] = new
        for _storageuser in _stores.values():
            _storageuser.commit()
        self._reset_scopes()
    mkdir = add_container

    def delete(self, argv):
        """delete <name>
    Delete the named object."""
        name = argv[1]
        try:
            self._obj.delete(name)
        except KeyError:
            delattr(self._obj, name)
        self._reset_scopes()

    def rename(self, argv):
        """rename <oldname> <newname>
    Rename the object."""
        old = argv[1]
        new = argv[2]
        self._obj.rename(old, new)
        self._reset_scopes()

    def set(self, argv):
        """set <name> <value>
    Sets the <name> to a new value.  """
        name = argv[1]
        value = eval(argv[2]) # may not be exactly what you wanted...
        setattr(self._obj, name, value)
        self._reset_scopes()

    def get(self, argv):
        """get <name>
    Gets and prints the item."""
        name = argv[1]
        v = getattr(self._obj, name)
        self._print(v)

    def mergefile(self, argv):
        """mergefile <filename>
    Merges then named file into the local storage cache. Values contained in the file are not persistent."""
        self._obj.mergefile(argv[1])

    def update(self, argv):
        """update [--name=value]...
    Updates the storage with its update method."""
        optlist, longoptdict, args = self.getopt(argv, "?")
        self._obj.update(longoptdict)

    def eval(self, argv):
        """eval <path>
    Evaluate a path the same way a program would. Display the resulting object."""
        obj = eval("self._obj.%s" % (argv[1],))
        self._print(repr(obj))


class RootContainerEditor(ContainerEditor):

    def _setup(self, cf, name):
        global _stores
        self._obj = cf
        self._environ["PS1"] = "{%s}> " % (name, )
        self._reset_scopes()
        _stores[str(id(self))] = cf._connection

    def finalize(self):
        global _stores
        del _stores[str(id(self))]
        if bool(self._obj.changed):
            if self._ui.yes_no("Changes have been made. Commit?"):
                self._obj.commit()
            else:
                self._obj.abort()

    def commit(self, argv):
        """commit
    Commits a pending transation."""
        self._obj.commit()

    def abort(self, argv):
        """abort
    Aborts a pending transation."""
        self._obj.abort()

    def pack(self, argv):
        """pack
    Aborts and packs a pending transation."""
        self._obj.pack()

    def set(self, argv):
        """set <name> <value>
    Sets the <name> to a new value.  """
        name = argv[1]
        value = eval(argv[2])
        self._obj.set(name, value)
        self._reset_scopes()

    def get(self, argv):
        """get <name>
    Gets and prints the item."""
        name = argv[1]
        v = self._obj.get(name)
        self._print(v)


class ObjectEditor(CLI.GenericCLI):
    def _setup(self, obj, name):
        self._obj = obj
        self._environ["PS1"] = "%%I%s%%N (%s)> " % (name, obj.__class__.__name__)
        self._reset_scopes()

    def _get_object(self, name):
        global _stores
        for _storageuser in _stores.values():
            try:
                d = _storageuser.get_root()
                path = name.split(".")
                for part in path[:-1]:
                    d = d[part]
                return d[path[-1]]
            except KeyError:
                continue
        self._print("Did not find object: ", name)
        return None

    def cd(self, argv):
        """cd <object>
    Change context to the named container object."""
        name = argv[1]
        if name == "..":
            raise CLI.CommandQuit
        try:
            obj = getattr(self._obj, name)
        except AttributeError:
            self._print("Object not found.")
            return
        if isinstance(obj, Storage.Container) or isinstance(obj, netobjects.PersistentAttrDict):
            cmd = self.clone(ContainerEditor)
            cmd._setup(obj, name)
            raise CLI.NewCommand, cmd
        else:
            self._print("Not a container object.")

    def up(self, argv):
        """up
    Move up in the object space."""
        raise CLI.CommandQuit

    def commit(self, argv):
        """commit
    Commit changes to the database now."""
        global _stores
        for _storageuser in _stores.values():
            _storageuser.commit()

    def abort(self, argv):
        """abort
    Abort changes to the database."""
        global _stores
        for _storageuser in _stores.values():
            _storageuser.abort()
        # just so user knows something really happened
        raise CLI.CommandQuit

    def giveto(self, argv):
        """giveto <user>
    Gives ownership of this object to the given user."""
        user = self._get_object(argv[1])
        if user:
            netobjects.giveto(self._obj, user)

    def disown(self, argv):
        """disown
    Set the object free!"""
        netobjects.takeback(self._obj)

    def owner(self, argv):
        """owner
    Show the current owner of this object."""
        self._print(self._obj.get_owner())

    def edit(self, argv):
        """edit  <object>
    Interactively edit an object."""
        name = argv[1]
        obj = getattr(self._obj, name)
        if obj:
            cmd = get_editor(self, obj, name)
            if cmd:
                raise CLI.NewCommand, cmd
            else:
                self._print("Cannot edit this object. Use 'set' to edit a simple attribute.")
        else:
            self._print("No such object.")
            return

# editor for PersistentData objects
class DataEditor(ObjectEditor):
    def ls(self, argv):
        """ls (or dir)
    Display a list of the wrapped objects attributes and their types."""
        s = []
        for aname, (typ, default) in self._obj._ATTRS.items():
            s.append("%20.20s (%16.16s) : %r" % (aname, typ.__name__, getattr(self._obj, aname)))
        self._print("\n".join(s))
    dir = ls

    def create(self, klass):
        kwargs = {}
        for aname, (typ, default) in klass._ATTRS.items():
            if default is netobjects.MANDATORY:
                self._get_input(aname, typ, None, kwargs)
            else:
                self._get_input(aname, typ, default, kwargs)
        inst = klass(**kwargs)
        return inst

    def _get_input(self, aname, typ, default, kwargs):
        if typ is bool:
            val = self._ui.yes_no(aname, default)
            kwargs[aname] = val
        elif typ in (unicode, str):
            val = self._ui.get_value(aname, default)
            kwargs[aname] = typ(val)
        elif typ in (long, int):
            val = self._ui.get_value(aname, default)
            kwargs[aname] = typ(val)
        elif issubclass(typ, netobjects.PersistentData):
            val = self.create(typ)
            kwargs[aname] = val


class UserEditor(ObjectEditor):
    def who(self, argv):
        """who
    Show who this user is."""
        self._print(self._obj)

    def give(self, argv):
        """give <object>
    Give this user an object."""
        obj = self._get_object(argv[1])
        if obj:
            netobjects.giveto(obj, self._obj)

    def take(self, argv):
        """take <object>
    Take the object given by its name from this user."""
        obj = self._get_object(argv[1])
        if obj:
            netobjects.takeback(obj, self._obj)

    def has(self, argv):
        """has <object>
    Tell whether or not this user has the given object."""
        obj = self._get_object(argv[1])
        if obj:
            if self._obj.has(obj):
                self._print("Yes, %s is in possession of %r." % (self._obj.name, obj))
            else:
                self._print("No, %s does not own '%s'." % (self._obj.name, obj.name))

    def inventory(self, argv):
        """inventory
    Show the entire set of possessions for this user."""
        inv = self._obj.inventory()
        if inv:
            self._print("%s has the following items:" % (self._obj.name,))
            for name in map(repr, inv):
                self._print("  %s" % (name,))
        else:
            self._print("%s has no possessions." % (self._obj.name,))

    def preferences(self, argv):
        """preferences ("get"|"set"|"edit") <name> [<object>]
    Get or set this users preferences, or preference objects. Without arguments displays all preferences."""
        prefs = self._obj.get_prefs()
        if len(argv) > 1:
            op = argv[1]
            if op == "edit":
                cmd = self.clone(ContainerEditor)
                cmd._setup(prefs, self._obj.name)
                raise CLI.NewCommand, cmd
            elif op == "set":
                name = argv[2]
                obj = eval(" ".join(argv[3:]))
                prefs[name] = obj
            elif op == "get":
                name = argv[2]
                self._print(prefs[name])
        else:
            self._print("Preferences:")
            for name, val in prefs.items():
                self._print("%22.22s: %r" % (name, val))


class DeviceEditor(ObjectEditor):
    def _reset_scopes(self):
        ifaces = self._obj.interfaces.keys()
        self.add_completion_scope("show", ["interface","connection"])
        self.add_completion_scope("interface", ifaces)
        self.add_completion_scope("connection", ifaces)

    def interact(self, argv):
        """interact
    Connect to the device via its Operations Server and interact with it."""
        return NotImplemented

    def connect(self, argv):
        """connect <interfacename> <networkobject>
    Connects the interface with the given name to the named network object. The
    network object must exist, but the interface need not. It will be created
    if it does not exist.  """
        ifname = argv[1]
        net = self._get_object(argv[2])
        if net:
            self._obj.connect(ifname, net)

    def disconnect(self, argv):
        """disconnect <interfacename>
    Set the named interface to disconnected state."""
        ifname = argv[1]
        self._obj.disconnect(ifname)

    def interface(self, argv):
        """interface <name>
    Edit the named interface."""
        intf = self._obj.get_interface(argv[1])
        cmd = get_editor(self, intf, argv[1])
        if cmd:
            raise CLI.NewCommand, cmd

    def show(self, argv):
        """show <object>
    Display information about the device attributes."""
        objname = argv[1]
        if objname.startswith("int"):
            if len(argv) > 2:
                ifname = argv[2]
                self._print(self._obj.get_interface(ifname))
            else:
                iflist = self._obj.get_interfaces()
                ifnames = iflist.keys()
                ifnames.sort()
                for ifname in ifnames:
                    self._print(str(self._obj.get_interface(ifname)))
        elif objname.startswith("conn"):
            if len(argv) > 2:
                net = self._get_object(argv[2])
                if net:
                    iflist = self._obj.connections(net)
                else:
                    self._print("Network not found.")
                    return
            else:
                iflist = self._obj.connections()
            iflist.sort()
            for intf in iflist:
                if intf.network:
                    self._print("%30.30s => %s" % (intf.devname, intf.network.name))
                else:
                    self._print("%30.30s => not connected" % (intf.devname, ))


class InterfaceEditor(ObjectEditor):
    def address(self, argv):
        """address <ipaddress> [<netmask>]
    Set the IP address for this interface."""
        if len(argv) > 2:
            mask = argv[2]
        else:
            mask = None
        address = argv[1]
        self._obj.update(address, mask)

    def name(self, argv):
        """name <newname>
    Name this interface with a new, user selected name."""
        newname = argv[1]
        self._obj.update(hostname=newname)


class NetworkEditor(ObjectEditor):
    def add_node(self, argv):
        """add_node <device>
    Adds the specified device to this network."""
        obj = self._get_object(argv[1])
        if obj and isinstance(obj, netobjects.NetworkDevice):
            self._obj.add_node(obj)

    def subnet(self, argv):
        """subnet ("add"|"remove") [<IPnetwork>] [<name>]
    Adds or removes the specified IP network to this physical network. You can
    supply an optional name when adding. Use this name when removing. Without
    arguments displays all subnets."""
        if len(argv) > 1:
            op = argv[1].lower()
            if op.startswith("a"):
                if len(argv) >= 4:
                    name = argv[3]
                else:
                    name = None
                self._obj.add_subnet(argv[2], name)
            elif op.startswith("r") or op.startswith("d"): # remove or delete
                self._obj.remove_subnet(argv[2])
            else:
                self._print(subnet.__doc__)
        else:
            for sn, name in self._obj:
                self._print("Subnet: %s (%s)" % (name, sn))

# this edits IP address allocation objects
class AddressEditor(ObjectEditor):

    def add(self, argv):
        """add <address> [<address>]
    Add an address or address range to this set."""
        addr1 = argv[1]
        if len(argv) > 2:
            addr2 = argv[2]
            self._obj.add_range(addr1, addr2)
        else:
            self._obj.add_net(addr1)

    def remove(self, argv):
        """remove <address> [<address>]
    Removes the given addressess from the set."""
        addr1 = argv[1]
        if len(argv) > 2:
            addr2 = argv[2]
            self._obj.remove_range(addr1, addr2)
        else:
            self._obj.remove_net(addr1)

    def allocate(self, argv):
        """allocate <address>
    Allocate (mark in use) the given address. The address must be in the set."""
        addr1 = argv[1]
        self._obj.allocate(addr1)
    use = allocate

    def deallocate(self, argv):
        """deallocate <address>
    Deallote (mark as free) the given address. The address must be in the set."""
        addr1 = argv[1]
        self._obj.deallocate(addr1)
    free = deallocate

    def next(self, argv):
        """next [<network>]
    Allocate the next available address. Limit the search to the network, if given."""
        if len(argv) > 1:
            net = self._get_object(argv[1])
            assert isinstance(net, netobjects.Network), "network must be a Network object."
        else:
            net = None
        ip = self._obj.get_next(net)
        self._print("Allocated %s for use." % (ip,))

    def show(self, argv):
        """show [<ip>]
    Show the current allocation from this set."""
        def _ipprint(ip, disp):
            if disp:
                self._print("%-17.17s %s" % (ip.cidr(), self._ui.format("%Rused%N")))
            else:
                self._print("%-17.17s %s" % (ip.cidr(), self._ui.format("%Gfree%N")))

        if len(argv) > 1:
            ip, disp = self._obj.get(argv[1])
            _ipprint(ip, disp)
        else:
            iplist = list(self._obj)
            iplist.sort()
            for ip, disp in iplist:
                _ipprint(ip, disp)

    def reset(self, argv):
        """reset
    Clears all allocations!"""
        if self._ui.yes_no("Are you sure?", False):
            self._obj.reset()

    def clear(self, argv):
        """clear
    Removes all addresses from collection!"""
        if self._ui.yes_no("Are you sure?", False):
            self._obj.clear()

# mapping of objects to editor objects.
_EDITORS = {}

def register_editor(klass, editobj):
    """Register an editor object for a particular type of object."""
    global _EDITORS
    assert type(klass) is type, "object must be class"
    assert type(editobj) is type and issubclass(editobj, CLI.BaseCommands), "editobject must be BaseCommands type object."
    _EDITORS[klass] = editobj

def get_editor_object(obj):
    "Returns a pre-registered editor class given an object instance."""
    global _EDITORS
    if isinstance(obj, object):
        return _EDITORS.get(obj.__class__)
    else:
        raise TypeError, "Can't get editor: object not a class instance"

def get_editor(cli, obj, name):
    editobj = get_editor_object(obj)
    if editobj is None: # not registered, try generic defaults
        if isinstance(obj, dict):
            cmd = cli.clone(CLI.DictCLI)
        elif hasattr(obj, "__dict__"):
            if isinstance(obj, netobjects.PersistentData):
                cmd = CLI.get_generic_clone(obj, cli, DataEditor)
            else:
                cmd = CLI.get_generic_clone(obj, cli, ObjectEditor)
        else:
            raise TypeError, "no editor available for %r." % (obj,)
    else:
        cmd = cli.clone(editobj)
    cmd._setup(obj, name)
    return cmd

def _get_object_by_name(objname):
    objlist = _EDITORS.keys()
    for obj in objlist:
        if objname == obj.__name__:
            return obj

def _register_my_modules():
    register_editor(Storage.Container, ContainerEditor)
    register_editor(netobjects.PersistentAttrDict, ContainerEditor)
    register_editor(netobjects.PersistentDict, CLI.DictCLI)
    register_editor(netobjects.NetworkDevice, DeviceEditor)
    register_editor(netobjects.Router, DeviceEditor)
    register_editor(netobjects.Host, DeviceEditor)
    register_editor(netobjects.EtherSwitch, DeviceEditor)
    register_editor(netobjects.SwitchRouter, DeviceEditor)
    register_editor(netobjects.Interface, InterfaceEditor)
    register_editor(netobjects.Network, NetworkEditor)
    register_editor(netobjects.User, UserEditor)
    register_editor(netobjects.IPAssignments, AddressEditor)

_register_my_modules()

# global singleton _storageusers object for Command instances to use, if needed
_stores = {}

def get_object(name):
    global _stores
    rv = None
    for _storageuser in _stores.values():
        r = _storageuser.get_root()
        try:
            rv = r.get(str(name))
        except (KeyError, AttributeError):
            continue
        else:
            if rv is None:
                continue
            else:
                return rv
    return rv

def get_storage_editor(parent, cf):
    cmd = parent.clone(RootContainerEditor)
    cmd._setup(cf, "root")
    return cmd

def commitall():
    global _stores
    for _storage in _stores.values():
        _storage.commit()

# main program
def storagecli(argv):
    """storagecli [-?rg] [<scriptfile>...]

Provides an interactive session to the configuration server. This allows you to
interactively view and change the persistent database.

Options:
   -?        = This help text.
   -g        = used paged output (like 'more').

"""
    from pycopia import getopt

    paged = False

    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "?g")
    except getopt.GetoptError:
            print storagecli.__doc__
            return
    for opt, val in optlist:
        if opt == "-?":
            print storagecli.__doc__
            return
        elif opt == "-g":
            paged = True

    if paged:
        from pycopia import tty
        io = tty.PagedIO()
    else:
        io = CLI.ConsoleIO()

    ui = CLI.UserInterface(io)

    cf = Storage.get_config(initdict=longopts)

    cf.reportfile = __name__.replace(".", "_")
    cf.logbasename = "%s.log" % (__name__.replace(".", "_"),)
    cf.arguments = argv
    cmd = RootContainerEditor(ui)
    cmd._setup(cf, "root")

    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_storagecli"))
    if args:
        for arg in args:
            try:
                parser.parse(arg)
            except KeyboardInterrupt:
                break
    else:
        parser.interact()


