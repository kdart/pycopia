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
Interface for the Smartbits SAI method.

"""

import sys, os, string
from UserList import UserList
from UserDict import UserDict
from UserString import UserString

from pycopia import ipv4

from pycopia.smartbits.UserInt import UserInt
from pycopia.smartbits.UserLong import UserLong
from pycopia.smartbits.UserFloat import UserFloat
from pycopia.smartbits import SMBAddress

def IF(test, trueval, falseval):
    if test:
        return trueval
    else:
        return falseval

class SAIError(Exception):
    pass



# basic types of SAI objects follow. These are the objects that are
# referred to in the data (*.txt) files.
class Boolean(UserInt):
    def __str__(self):
        if self.data:
            return "yes"
        else:
            return "no"

yes = on = Boolean(1)
no = off = Boolean(0)
String = UserString
Integer = UserInt
Float = UserFloat

class MACAddress(UserLong):
    def __init__(self, data=0L, increment=0, bitoffset=0, length=6):
        self.length = length # octets
        self.increment = increment
        self.bitoffset = bitoffset
        if type(data) is type(""):
            self.data = self._handle_str(data)
        elif isinstance(data, MACAddress):
            self.data = data.data
            self.increment = data.increment
            self.bitoffset = data.bitoffset
            self.length = data.length
        else:
            self.data = long(data)
    def __str__(self):
        cv = []
        val = self.data
        for i in xrange(self.length):
            cv.insert(0, hex((val >> (i * 8)) & 0xff)[2:-1])
        return "%s%s%s" % (".".join(cv), IF(self.increment, 
                    IF(self.increment>1,"+%d"%self.increment ,"+"), ""), 
                        IF(self.bitoffset, "|%d" % self.bitoffset, ""))
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, hex(self.data))
    def set_increment(self, increment):
        self.increment = increment
    def _handle_str(self, data):
        rv = 0L
        octets = data.split(".")
        assert len(octets) == self.length
        count = self.length - 1
        octets = map(lambda oc: long(eval("0x%s" % oc)), octets)
        for octet in octets:
            rv += octet << (count * 8)
            count -= 1
        return rv
        
class IPAddress(ipv4.IPv4):
    def __init__(self, addr, increment=0, bitoffset=0):
        ipv4.IPv4.__init__(self, addr) # use slash notation feature for mask
        if isinstance(addr, IPAddress):
            self.__dict__["increment"] = addr.increment
            self.__dict__["bitoffset"] = addr.bitoffset
        else:
            self.__dict__["increment"] = increment
            self.__dict__["bitoffset"] = bitoffset
    def __str__(self):
        return "%s%s%s" % (ipv4.itodq(self._address), 
                IF(self.increment, IF(self.increment>1,"+%d" % self.increment, "+"), ""),
                IF(self.bitoffset, "|%s" % self.bitoffset, "") )
    def set_increment(self, increment):
        self.increment = increment

class HexInteger(UserInt):
    def __init__(self, value):
        if type(value) is type(""):
            self.data = eval("0x%s" % value)
        else:
            self.data = int(value)
    def __str__(self):
        return hex(self.data)[2:]

class Endpoint:
    def __init__(self, start, end=None):
        self.start = start
        self.end = end
    def __str__(self):
        if self.end is None:
            return str(self.start)
        else:
            return "%s:%s" % (self.start, self.end)
    def __repr__(self):
        return "Endpoint(%r, %r)" % (self.start, self.end)

class Flow:
    def __init__(self, endpoint1, endpoint2=None, name=""):
        if isinstance(endpoint1, self.__class__):
            self.endpoint1 = endpoint1.endpoint1
            self.endpoint2 = endpoint1.endpoint2
            self.name = endpoint1.name
        else:
            self.endpoint1 = endpoint1
            self.endpoint2 = endpoint2
            self.name = name
    def __str__(self):
        return "%s->%s" % (self.endpoint1, self.endpoint2)
    def __repr__(self):
        return "Flow(%r, %r)" % (self.endpoint1, self.endpoint2)
    def set_name(self, name):
        self.name = name

class MPLSLabel:
    """
MPLS Label (user-specified) in the form: 
    Label:Experimental:TTL
Disposition of fields: 
    Label User-specified 20-bit label. 
    Experimental User-specified 3-bit experimental value. 
    TTL User-specified 8-bis value.
All fields are interpreted as hexadecimal. The label sub-field of the
first label will be overwritten by the value returned by the DUT, but
other labels (if any) will contain the user-specified value in the label
sub-field.
    """
    def __init__(self, label, experimental=0, ttl=64):
        if isinstance(label, self.__class__):
            self.label = label.label
            self.experimental = label.experimental
            self.ttl = label.ttl
        else:
            self.label = label & 0xfffff
            self.experimental = experimental & 0x3
            self.ttl = ttl & 0xff
    def __str__(self):
        return "%s:%s:%s" % (hex(self.label)[2:], hex(self.experimental)[2:], hex(self.ttl)[2:])
    def __repr__(self):
        return "%s(%x, %x, %x)" % (self.__class__.__name__, self.label, self.experimental, self.ttl)

class PayloadProt(UserInt):
    def __str__(self):
        if self:
            return "p%d" % (self.data)
        else:
            return ""

class VariantField(UserInt):
    # implemented as a bitmap
    _flags = {"none":0, "i": 0x1, "m": 0x2, "p":0x4, "I":0x8, "M":0x10, "P":0x20}
    def __init__(self, data=0):
        if type(data) is type(""):
            if data == "none":
                self.data = 0
            else:
                self.data = 0
                self.set(data)
        else:
            UserInt.__init__(self, data)
    def __str__(self):
        s = []
        if self.data:
            for name, bit in VariantField._flags.items():
                if self.data & bit:
                    s.append(name)
            return string.join(s, "")
        else:
            return "none"
    def set(self, flags):
        for flag in flags:
            self.data |= VariantField._flags[flag]
    def setall(self):
        for bit in VariantField._flags.values():
            self.data |= bit
    def reset(self, flags):
        for flag in flags:
            self.data &= ~VariantField._flags[flag]
    def clear(self):
        self.data = 0
    def get_attributes(self):
        return VariantField._flags.keys()


class TCPFlag(HexInteger):
    pass

class INETPort(UserInt):
    def __init__(self, data=9, increment=0):
        UserInt.__init__(self, data)
        if isinstance(data, INETPort):
            self.increment = data.increment
        else:
            self.increment = increment
    def __str__(self):
        return "%s%s" % (self.data, IF(self.increment, "+", ""))

class _ArrayList(UserList):
    def __init__(self, data=None):
        if type(data) is type(""): # allow initialization of list with single string.
            self.data = [data]
        else:
            UserList.__init__(self, data)
    def __str__(self):
        # it seems SAI interpreter cannot handle lines that are to long.
        # so this will break up the lines with a backslash continuation
        # feature.
        str_list = map(str, self.data)
        # approx 20 items per line
        lines = []
        for sect in range(int(len(str_list) / 20)+1):
            lines.append(string.join(str_list[sect*20:sect*20+20], " "))
        return string.join(lines, " \\\n")

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.data)

class FlowList(_ArrayList):
    pass

class Buckets(_ArrayList):
    pass

class FrameSizes(_ArrayList):
    pass

class GroupList(_ArrayList):
    pass

class Strings(_ArrayList):
    pass

class FrameRange:
    def __init__(self, minimum=64, maximum=1500, increment=10):
        if isinstance(minimum, FrameRange):
            self.minimum = minimum.minimum
            self.maximum = minimum.maximum
            self.increment = minimum.increment
        else:
            self.minimum = minimum
            self.maximum = maximum
            self.increment = increment
    def __str__(self):
        return "%d:%d:%d" % (self.minimum, self.maximum, self.increment)

class ReportFlags:
    """
Manage ReportAFGRTS parameter object.
    """
    _flags = {"A":0, "F":1, "G":2, "R":3, "T":4, "S":5} # index numbers
    def __init__(self, data=None):
        self.clear()
        if type(data) is type(""):
            self.data = string.split(data, ":")
            assert len(self.data) == 6
    def __str__(self):
        return string.join(self.data, ":")
    def set(self, flags):
        for flag in flags:
            self.data[ReportFlags._flags[flag]] = "1"
    def reset(self, flags):
        for flag in flags:
            self.data[ReportFlags._flags[flag]] = "0"
    def clear(self):
        self.data = ["1","1","1","0","0","0"]

class SnapSCType:
    def __init__(self, starttime=2000, count=10):
        if type(starttime) is type(""):
            ss, cs = tuple(string.split(starttime, ":"))
            self.starttime = int(ss)
            self.count = int(cs)
        elif isinstance(starttime, SnapSCType):
            self.starttime = starttime.starttime
            self.count = starttime.count
        else:
            self.starttime = starttime
            self.count = count
    def __str__(self):
        return "%d:%d" % (self.starttime, self.count)

class thruputRSBType:
    def __init__(self, range=0, step=0, binary=1):
        if type(range) is type(""):
            self.range, self.step, self.binary = tuple(map(int, string.split(range, ":")))
        elif isinstance(range, thruputRSBType):
            self.range = range.range
            self.step = range.step
            self.binary = range.binary
        else:
            self.range = range
            self.step = step
            self.binary = binary
    def __str__(self):
        return "%d:%d:%d" % (self.range, self.step, self.binary)
    def __repr__(self):
        return "%s(%d, %d, %d)" % (self.__class__.__name__, self.range, self.step, self.binary)

class thruputSMMRType:
    def __init__(self, start=1, min=0, max=100, resolution=1):
        if type(start) is type(""):
            self.start, self.min, self.max, self.resolution = tuple(map(int, string.split(start, ":")))
        elif isinstance(start, thruputSMMRType):
            self.start = start.start
            self.min = start.min
            self.max = start.max
            self.resolution = start.resolution
        else:
            self.start = start
            self.min = min
            self.max = max
            self.resolution = resolution
    def __str__(self):
        return "%d:%d:%d:%d" % (self.start, self.min, self.max, self.resolution)

class stepwisePLFTType:
    def __init__(self, ports=1, learning=1, flows=1, transmit=1):
        if type(ports) is type(""):
            self.ports, self.learning, self.flows, self.transmit = tuple(map(int, string.split(start, ":")))
        elif isinstance(ports, stepwisePLFTType):
            self.ports = ports.ports
            self.learning = ports.learning
            self.flows = ports.flows
            self.transmit = ports.transmit
        else:
            self.ports = ports
            self.learning = learning
            self.flows = flows
            self.transmit = transmit
    def __str__(self):
        return "%d:%d:%d:%d" % (self.ports, self.learning, self.flows, self.transmit)


### end of SAI types

### Utility objects

# A ParameterTable holds SAI table data. It is used internally by the
# section objects. Lines starting with a '#' are comments. Each
# non-comment line must contain four tab-delimited fields. Each field is
# evaluated by the Python interpreter to convert them to python objects.
# Those objects must exists in the namespace where this is run, or errors
# will occur when reading in the file. 
# Field 1: name of attribute. This name becomes the first paramter given
#          to most O.append() methods. It selects the proper row data. 
# Field 2: description. A quoted string that describes the attribute.
#          useful for online help.
# Field 3: default value. If a value other than None is given here it will
#          be used in the generated SAI file if it is not overridden by
#          explicitly setting it.
# Field 4: An object that defines the permissible values for this
#          attribute. It may be a tuple containing a set of permissible
#          values.

class ParameterTable:
    def __init__(self, fname):
        self.data = [] # to preserve order
        self.table = {}
        # the data files should be kept in the same directory as this
        # module. They will be automatically found then.
        FILE = os.path.join(os.path.dirname(__file__), fname)
        fp = open(FILE, "r")
        for line in fp.readlines():
            if len(line) < 2 or line[0] == "#":
                continue
            name, desc, defval, types = tuple(string.split(line.strip(), "\t"))
            tr = TableRow(name, eval(desc), eval(defval), eval(types))
            self.data.append(tr)
            self.table[name] = tr
        fp.close()
    def get(self, key, default=None):
        return self.table.get(key, default)
    def __getitem__(self, key):
        return self.table[key]
    def keys(self):
        return map(lambda o: o.name, self.data)
    def items(self):
        return self.table.items()


# represents a row of data in the data files. The four fields are
# represented here.
class TableRow:
    def __init__(self, name, description, default, types):
        self.name = name
        self.description = description
        self.default = default
        self.types = types
    def __str__(self):
        return "%s\t%s\t%s\t%s" % (self.name, self.description, self.default, self.types)
    def __repr__(self):
        return "%r\t%r\t%r\t%r" % (self.name, self.description, self.default, self.types)


# global function to verify parameter values
def _check_value(types, val):
    typeoftypes = type(types)
    if typeoftypes is type(()): # recursively check objects in a tuple
                                # if any pass, check is good (not efficient)
        cv = map(lambda ty, v=val: _check_value(ty, v), types)
        if yes in cv:
            return yes
        else:
            return no
#       if val in types:
#           return yes
#       else:
#           return no
    if typeoftypes is type(''):
        if val == types:
            return yes
        else:
            return no
    if typeoftypes is type(TableEntry): # class type
        try:
            testval = types(val)
        except:
            return no
        else:
            return yes
    # XXX check other values
    return yes

# A TableEntry represents a particular kind of paramter line in the SAI
# file. it allows setting the column values by name (named arguments), and
# verifies that the supplied values make sense for that type as defined in
# the data files. Printing the object emits the SAI parameter line.
class TableEntry:
    def __init__(self, paramtype, table, **kwargs):
        self.paramtype = paramtype
        self.table = table
        self.values = {}
        self.set(**kwargs)

    # if a value has been supplied for a parameter, use that. If not, and
    # there is a default value defined in that paramter table, use that.
    # if the value is None, do not emit it. 
    def __str__(self):
        s = [self.paramtype]
        for key in self.table.keys():
            val = self.values.get(key, None)
            if val is None:
                val = self.table[key].default
            if val is not None:
                s.append(str(val))
        return string.join(s, " ")

    
    def set(self, **kwargs):
        for key, val in kwargs.items():
            te = self.table.get(key)
            if te is None:
                raise SAIError, "Invalid paramter name given: "+ key
            if _check_value(te.types, val):
                if type(te.types) is type(TableEntry): # class type, cast to class object
                    self.values[key] = te.types(val)
                else:
                    self.values[key] = val
            else:
                raise SAIError, "invalid value for %s (should be %r)" % (key, te.types)


    def get_value(self, name):
        rv = self.values.get(name, None)
        if rv is None:
            te = self.table.get(name)
            if te is None:
                raise ValueError, "no entry by the name %s." % (name)
            return te.default
        else:
            return rv



class PortEntry(TableEntry):
    pass

class EndPointEntry(TableEntry):
    pass

class IPFlowEntry(TableEntry):
    pass

class IPFlowEntry(TableEntry):
    pass

class TCPFlowEntry(TableEntry):
    pass

class UDPFlowEntry(TableEntry):
    pass

class VIPFlowEntry(TableEntry):
    pass

class VUDPFlowEntry(TableEntry):
    pass

class VTCPFlowEntry(TableEntry):
    pass

class LIPFlowEntry(TableEntry):
    pass

class LUDPFlowEntry(TableEntry):
    pass

class GroupEntry(TableEntry):
    pass

#   headings = """
#   #   %wireRate Step Speed Duplex AutoNg BurstSize    AddressResolution
#   #   H:S:P W    St Sp    D    AutoNg B    A    IPaddress    Gateway    Netmask    Name
#"""

#### Main API 
# The document sections. Most of them can inherit from the generic Section
# class. those sections that have a list of Entry lines of arbitrary
# length are objects of this type. Some sections are special, they contain
# only keyword/value pairs (such as the testdefaults section). Those types
# of sections have the keyword mapped to a section attribute.

class Section(UserList):
    """
Abstract base class for most SAI sections.
    """
    def __init__(self):
        UserList.__init__(self)
        self.tables = {}
        # _table_names entries relate a paramter line name to a table and
        # its Entry object name. The tables are defined in external text
        # files. 
        for param, tabledata in self.__class__._table_names.items():
            tablename, rowclass = tabledata
            self.tables[param] = (ParameterTable(tablename), rowclass)
    def __str__(self):
        s = map(lambda d: "\t%s\n" % (d), self.data)
        return self.__class__._header + "".join(s) + "\n"
    def add(self, entry_type, **kwargs):
        try:
            table, entryclass = self.tables[entry_type]
            self.data.append(entryclass(entry_type, table, **kwargs))
        except IndexError:
            raise SAIError, "invalid parameter type. should be one of %r." % (self.__class__._table_names.keys(),)
    append = add
    def get_attributes(self):
        rv = []
        for td in self.tables.values():
            rv.extend(td[0].keys())
        return rv


class testdefaultsSection:
    """
TestDefaultsSection([parameters])
creates a 'testdefaults' SAI section. It will only emit an option line if
you set a value different from the default. You can set the attribute by
setting the instances attribute. 

ts = TestDefaultsSection()
ts.sizewcrc = yes
print ts

or

ts = TestDefaultsSection(sizewcrc = yes)
sai.append(ts)
print sai

    """
    _header = "testdefaults\n"
    def __init__(self, **kwargs):
        self.__dict__["table"] = ParameterTable("table_testdefaults.txt")
        self.__dict__["values"] = kwargs
    def __str__(self):
        s = []
        # only emit testdefaults if some parameter is different from the default
        for key, value in self.values.items():
            if self.table[key].default != value:
                s.append("\t%s %s\n" % (key, value))
        if s:
            return testdefaultsSection._header + string.join(s) + "\n"
        else:
            return "\n"
    def __setattr__(self, name, val):
        te = self.table.get(name, None)
        if te is None:
            raise AttributeError, "invalid testdefaults attribute"
        self.values[name] = val
    def get_attributes(self):
        return self.table.keys()


class portsSection(Section):
    _header = "ports\n"
    _table_names = {
        "eth": ("table_ports_eth.txt", PortEntry),
        "pos": ("table_ports_pos.txt", PortEntry),
    }

class resolve_endpointsSection(Section):
    _header = "resolve_endpoints\n"
    _table_names = {"node": ("table_resolve_endpoints.txt", EndPointEntry)}



class defineflowsSection(Section):
    _header = "defineflows\n"
    _table_names = {
        # ethernet or POS
        "IP": ("table_flows_IP.txt", IPFlowEntry),
        "TCP": ("table_flows_TCP.txt", TCPFlowEntry),
        "UDP": ("table_flows_UDP.txt", UDPFlowEntry),
        "SIP": ("table_flows_IP.txt", IPFlowEntry), # this was in an example, but not the docs!
        # VLAN tagged
        "VIP": ("table_flows_VIP.txt", VIPFlowEntry),
        "VUDP": ("table_flows_VUDP.txt", VUDPFlowEntry),
        "VTCP": ("table_flows_VTCP.txt", VTCPFlowEntry),
        # MPLS labeled
        "LIP": ("table_flows_LIP.txt", LIPFlowEntry),
        "LUDP": ("table_flows_LUDP.txt", LUDPFlowEntry),
    }

class definegroupsSection(Section):
    _header = "definegroups\n"
    _table_names = {"group": ("table_definegroups.txt", GroupEntry)}


class flowtestSection:
    _serial = 1
    def __init__(self, **kwargs):
        self.__dict__["table"] = ParameterTable("table_flowtest.txt")
        self.__dict__["values"] = {}
        self.__dict__["serial"] = flowtestSection._serial
        self.set(**kwargs)
        flowtestSection._serial += 1
    def __str__(self):
        s = ["flowtest %d\n" % (self.serial)]
        valuenames = self.values.keys()
        for key in valuenames:
            s.append("\t%s %s\n" % (key, self.values[key]))
        for key, te in self.table.items():
            if te.default is not None and key not in valuenames:
                s.append("\t%s %s\n" % (key, te.default))
        return string.join(s) + "\n"
    def __setattr__(self, key, val):
        te = self.table.get(key, None)
        if te is None:
            raise AttributeError, "invalid parameter name"
        if _check_value(te.types, val):
            if type(te.types) is type(flowtestSection): # class type, cast to class object
                self.values[key] = te.types(val)
            else:
                self.values[key] = val
        else:
            raise SAIError, "invalid value for %s (should be %r)" % (key, te.types)

    def __getattr__(self, key):
        rv = self.values.get(key, None)
        if rv is None:
            rv = self.table.get(key, None)
            if rv is None:
                raise AttributeError, "AttributeError: no attribute '%s'" % (key)
            return rv.default
        return rv
    def set(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def get_attributes(self):
        return self.table.keys()

    def get_type(self, name):
        return self.table[name].types


### The top level container object. 
class SAI:
    """
SAI()
The top-level SAI document. Instantiate this, then add section objects to it 
with the append() method. 
Use any method to "stringify" this object to produce the document. 
    """
    def __init__(self, application="smartflow 1.30"):
        self.data = []
        self.application = application
    def __str__(self):
        s = ["sai %s\n\n" % (self.application)]
        s.extend(map(str, self.data))
        return string.join(s, "")
    def append(self, sect):
        self.data.append(sect)
    add = append
    def insert(self, index, val):
        self.data.insert(index, val)


