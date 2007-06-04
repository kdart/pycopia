#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

"""

import sys
import keyword
from pycopia.SMI import Objects
from pycopia.SMI import Basetypes

def default_name_mangler(name):
    if name.endswith("Entry"):
        name = name[:-5]
    # make sure name doesn't match Python keyword, or there will be errors
    # later. Simply converting to uppercase should suffice.
    if keyword.iskeyword(name):
        name = name.capitalize()
        if __debug__:
            print >>sys.stderr, "warning: identifier matches keyword: converting to %r" % (name,)
    return name


class InterfaceEntry(object):
    def __init__(self, name, ifindex, adminstatus, mtu, address, speed, iftype):
        self.name = str(name)
        self.ifindex = int(ifindex)
        self.adminstatus = int(adminstatus)
        self.mtu = int(mtu)
        self.address = str(address)
        self.speed = long(speed)
        self.iftype = int(iftype)
    
    def __str__(self):
        return "%s (%s)" % (self.name, self.ifindex)


class InterfaceTable(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self._entries = {}
        self._byindex = {}
    
    def __str__(self):
        s = ["Interfaces for %s\nName (ifindex)" % (self.hostname,)]
        names = self._entries.keys()
        names.sort()
        for name in names:
            s.append(str(self._entries[name]))
        return "\n".join(s)
    
    def add_entry(self, If):
        name = str(If.ifDescr)
        ifindex = int(If.ifIndex)
        e = InterfaceEntry(name, ifindex, If.ifAdminStatus, If.ifMtu, 
                If.ifPhysAddress, If.ifSpeed, If.ifType)
        self._entries[name] = e
        self._byindex[ifindex] = e
    
    def __iter__(self):
        return self._entries.itervalues()

    def __getitem__(self, key):
        if type(key) is str:
            return self._entries[key]
        elif type(key) is int:
            return self._byindex[key]
        else:
            raise KeyError, "invalid key type"



class Manager(object):
    """
An instance of this object represents an SNMP management session, with
this instance acting as a manager role. This Manager object has a
one-to-one relation to a device agent.

This object maps MIB scalar objects to object attributes. You can get or
set these in the normal Python syntax.

Usage:
device = Manager( snmp_session )

    """
    def __init__(self, sess):
        if hasattr(sess, "get"):
            self.__dict__["session"] = sess
        else:
            raise TypeError, "Manager: must instantiate with SNMP session."
        self.__dict__["hostname"] = self.session.sessiondata.agent
        self.__dict__["scalars"] = {}
        self.__dict__["rows"] = {}
        self.__dict__["notifications"] = {}

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def add_mibs(self, miblist, mangler=default_name_mangler):
        for mib in miblist:
            self.add_mib(mib, mangler)

    def add_mib(self, mibmodule, mangler=default_name_mangler, subclassmodule=None):
        for objname in dir(mibmodule):
            name = mangler(objname)
            if subclassmodule and hasattr(subclassmodule, name):
                obj = getattr(subclassmodule, name)
            else:
                obj = getattr(mibmodule, objname)
            if type(obj) is type:
                if issubclass(obj, Objects.ScalarObject):
                    self.scalars[name] = obj
                elif issubclass(obj, Objects.RowObject):
                    self.rows[name] = obj
                elif issubclass(obj, Objects.NotificationObject):
                    self.notifications[name] = obj

    def __str__(self):
        return "<%s serving agent %s>" % (self.__class__.__name__, self.session.sessiondata.agent)

    # introspection interfaces
    def get_row_names(self):
        l = self.rows.keys()
        l.sort()
        return l
    get_table_names = get_row_names
    get_tables = get_row_names

    def get_scalar_names(self):
        """get_scalar_names()
        returns a list of scalar attributes for the managed device.
        """
        l = self.scalars.keys()
        l.sort()
        return l
    get_attributes = get_scalar_names 

    def get_notification_names(self):
        l = self.notifications.keys()
        l.sort()
        return l

    ### object retrieval methods
    # get_scalars is most efficient way of getting a set of scalars
    def get_scalars(self, *args):
        vbl = Basetypes.VarBindList()
        scalar_c = map(lambda on: self.scalars[on], args)
        map(lambda o: vbl.append(Basetypes.VarBind(o.OID+[0])), scalar_c)
        return_vbl = self.session.get_varbindlist(vbl)
        rv = map(lambda vb: vb.value, return_vbl)
        return tuple(rv)

    def getall(self, mangledname, indexoid=None):
        """getall(tablename, [indexoid=False])
        Gets all of the rows of a table (given by name). If an (optional) oid
        fragment is given as a second argument, this is used to restrict the
        objects retrieved to that index value. If the row has multiple indexes,
        you must supply a value in the order that the index is listed in the
        MIB.

        """
        t = Objects.ObjectTable(self.rows[mangledname])
        t.fetch(self.session)
        if indexoid: # return requested subset
            rt = Objects.ObjectTable(self.rows[mangledname])
            OIDtype = Objects.Basetypes.OID
            for oid, val in t.items():
                if OIDtype(oid) == indexoid:
                    rt[oid] = val
        else:
            rt = t
        return rt

    def get_iterator(self, name, indexoid=None, count=0):
        return Objects.RowIterator(self, self.rows[name], indexoid, count)

    def get(self, rowname, *indexargs):
        newobj = self.rows[rowname]()
        newobj.get(self.session, list(indexargs))
        newobj.set_session(self.session)
        return newobj

    def __getattr__(self, key):
        obj = self.scalars[key]()
        value = obj.get(self.session)
        return value

    def __setattr__(self, key, value):
        try:
            obj = self.scalars[key]()
            obj.set(self.session, value)
        except KeyError:
            if __debug__:
                print "Warning: setting local object in manager named", key
            self.__dict__[key] = value

    def create(self, rowname, *indexargs, **kwargs):
        rowobj = self.rows[rowname]()
        args = (self.session,)+indexargs
        row = apply(rowobj.createAndGo, args, kwargs)
        row.set_session(self.session)
        return row

    def destroy(self, rowname, *indexargs):
        rowobj = self.rows[rowname]()
        rowobj.get(self.session, indexargs)
        rowobj.destroy(self.session)

    def create_wait(self, rowname, *indexargs, **kwargs):
        rowobj = self.rows[rowname]()
        args = (self.session,) + indexargs
        row = apply(rowobj.createAndWait, args, kwargs)
        row.set_session(self.session)
        return row

    def _get_interfaces(self):
        t = self.getall('If')
        rt = InterfaceTable(self.hostname)
        for If in t.values():
            rt.add_entry(If)
        return rt
    InterfaceTable = property(_get_interfaces)
    
    def get_interface(self, index):
        return self.get("If", int(index))

