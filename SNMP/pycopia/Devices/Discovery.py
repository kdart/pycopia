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
Module to assist mapping networks using devices that support CDP and LLDP protocols.

"""


import ipv4
import SNMP.SNMP as SNMP
import SNMP.Manager as Manager
from SNMP.Basetypes import OctetString

from pycopia.mibs import SNMPv2_MIB
from pycopia.mibs import IF_MIB
from pycopia.mibs import IP_MIB
from pycopia.mibs import RFC1213_MIB # ipNetToMedia (ARP table)
from pycopia.mibs import CISCO_CDP_MIB as CDP_MIB
from pycopia.mibs import LLDP_MIB



# http://www.cisco.com/univercd/cc/td/doc/product/lan/trsrb/frames.htm
#Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
#                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone
class CDPCapabilityString(OctetString):
        # bit: (short desc., long description)
    _CAPS = {
        0x01: ("Router", "Performs level 3 routing for at least one network layer protocol."),
        0x02: ("Trans Bridge", "Performs level 2 transparent bridging."),
        0x04: ("Bridge (Source Route)", "Performs level 2 source-route bridging."),
        0x08: ("Switch", "Performs level 2 switching. "),
        0x10: ("Host", "Sends and receives packets for at least one network layer protocol. "),
        0x20: ("IGMP", "The bridge or switch does not forward IGMP Report packets on nonrouter ports."),
        0x40: ("repeater", "Provides level 1 functionality."),
        0x80: ("Phone", "Voice over IP."), # XXX not sure about this one
    }
    def description(self, long=False):
        val = self.__int__()
        s = []
        if long:
            si = 1 ; joiner = "\n"
        else:
            si = 0 ; joiner = " "
        for bits, desc in CDPCapabilityString._CAPS.items():
            if bits & val:
                s.append(desc[si])
        return joiner.join(s)
    
    def is_router(self):
        return 0x01 & self.__int__()

    def is_bridge(self):
        return 0x02 & self.__int__()

    def is_sourceroute(self):
        return 0x04 & self.__int__()

    def is_switch(self):
        return 0x08 & self.__int__()

    def is_host(self):
        return 0x10 & self.__int__()

    def is_igmp(self):
        return 0x20 & self.__int__()

    def is_repeater(self):
        return 0x40 & self.__int__()

    def is_phone(self):
        return 0x80 & self.__int__()

# "Patch"  cdpCacheCapabilities with modified syntaxobject
CDP_MIB.cdpCacheCapabilities.syntaxobject = CDPCapabilityString


class ARPEntry(object):
    def __init__(self, ip, mac, ifindex):
        self.ip = ip
        self.mac = mac
        self.ifindex = ifindex
    
    def __str__(self):
        return "%16.16s -> %s (%s)" % (self.ip, self.mac, self.ifindex)

class ARPTable(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self._entries = {}
    
    def __iter__(self):
        return self._entries.iteritems()

    def __getitem__(self, key):
        return self._entries[str(key)]

    def __getattr__(self, key):
        return getattr(self._entries, key)

    def __str__(self):
        s = ["ARP table for %s\nIP                  MAC               IfIndex" % (self.hostname,)]
        iplist = self._entries.keys()
        iplist.sort()
        for ip in iplist:
            ae = self._entries[ip]
            s.append(str(ae))
        return "\n".join(s)

    def add_entry(self, entry):
        ip = str(entry.ipNetToMediaNetAddress)
        mac = str(entry.ipNetToMediaPhysAddress)
        ifindex = int(entry.ipNetToMediaIfIndex)
        ae = ARPEntry(ip, mac, ifindex)
        self._entries[ip] = ae


class CDPEntry(object):
    def __init__(self, iface, entry):
        self.iface = iface
        self.deviceId = entry.cdpCacheDeviceId
        self.capabilities = entry.cdpCacheCapabilities 
        self.devicePort = entry.cdpCacheDevicePort
        self.platform = entry.cdpCachePlatform 

    def __str__(self):
        return "%s  ->\n    %s:%s (%s) %s"  % \
            (self.iface,
                self.deviceId, self.devicePort, self.capabilities.description(), self.platform)


class CDPTable(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self._entries = []
    
    def __iter__(self):
        return iter(self._entries)
    
    def __getitem__(self, i):
        return self._entries[i]

    def __str__(self):
        s = ["CDP Table for %s\nLocal Interface     ->\n    Device ID          Port ID    Capability    Platform" % (self.hostname,)]
        for entry in self._entries:
            s.append(str(entry))
        return "\n".join(s)

    def add_entry(self, iface, entry):
        self._entries.append(CDPEntry(iface, entry))


class LLDPEntry(object):
    def __init__(self):
        pass
    
class LLDPTable(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self._entries = []
    
    def __iter__(self):
        return iter(self._entries) # XXX
    
    def __str__(self):
        s = ["LLDP Table for %s\n " % (self.hostname,)]
        for entry in self._entries:
            s.append(str(entry))
        return "\n".join(s)
    
    def add_entry(self, entry):
        self._entries.append(entry) # XXX


class IPAddressTable(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self._entries = {}

    def __iter__(self):
        return self._entries.iteritems()
    
    def __getitem__(self, i):
        return self._entries[i]
    
    def get(self, i, default=None):
        return self._entries.get(i, default)
    
    def __str__(self):
        s = ["Address table for %s\n IfIndex IP Address" % (self.hostname,)]
        for i, ip in self._entries.items():
            s.append("%8d %s" % (i, ip.CIDR))
        return "\n".join(s)
    
    def add_entry(self, entry):
        ip = ipv4.IPv4(entry.ipAdEntAddr.address, entry.ipAdEntNetMask.address)
        self._entries[int(entry.ipAdEntIfIndex)] = ip


class DiscoverManager(Manager.Manager):
    """Manager that only supports discovery MIBS. Used to assist in mapping networks."""

    def _get_CDP_interfaces(self):
        return self.getall('cdpInterfaceEntry') # XXX
    cdpinterfaces = property(_get_CDP_interfaces)

    def _get_CDP(self):
        t =  self.getall('cdpCache')
        cdpt = CDPTable(self.hostname)
        for entry in t:
            ifindex = entry.indexoid[0]
            iface = self.get("If", ifindex).ifDescr
            cdpt.add_entry(iface, entry)
        return cdpt
    cdpcache = property(_get_CDP)
    CDPTable = cdpcache # alias

    def _get_arptable(self):
        t = self.getall("ipNetToMedia")
        at = ARPTable(self.hostname)
        for entry in t:
            at.add_entry(entry)
        return at
    ARPTable = property(_get_arptable)

    def _get_LLDP_ports(self):
        t =  self.getall("lldpPortConfig")
        return t # XXX
    LLDPPorts = property(_get_LLDP_ports)

    def _get_LLDP_table(self):
        t =  self.getall("lldpRem")
        lldp = LLDPTable(self.hostname)
        for e in t:
            lldp.add_entry(e)
        return lldp
    LLDPTable = property(_get_LLDP_table)

    def _get_iptable(self):
        t = self.getall("ipAddr")
        rt = IPAddressTable(self.hostname)
        for e in t:
            rt.add_entry(e)
        return rt
    IPAddressTable = property(_get_iptable)


def show_neighbors(dev):
    d = {}
    cache = dev._get_CDP()
    #print cache
    for entry in cache:
        port = str(entry.iface)
        l = d.get(port)
        e = (str(entry.deviceId), str(entry.devicePort), str(entry.platform))
        if l is not None:
            l.append(e)
        else:
            d[port] = [e]
    for pn, dl in d.items():
        print pn, "->"
        for dest in dl:
            print "        ", "%s:%s (%s)" % dest


def get_manager(host, community):
    box = SNMP.get_session(host, community)
    device = DiscoverManager(box)
    device.add_mibs([SNMPv2_MIB, IF_MIB, IP_MIB, RFC1213_MIB])
    device.add_mibs([CDP_MIB, LLDP_MIB])
    return device


def _test(argv):
    host = argv[1]
    community = argv[2]
    dev = get_manager(host, community)
    print dev.get_tables()
    #for cdpiface in dev.cdpinterfaces:
    #   print cdpiface
    #for entry in dev.cdpcache:
    #   print entry.cdpCacheDeviceId, 
    #   print "(", entry.cdpCacheCapabilities.description(), ")",
    #   print
    #show_neighbors(dev)
    print dev.InterfaceTable
    print dev.ARPTable
    print dev.IPAddressTable
    print dev.CDPTable
    print dev.LLDPTable
    return dev

if __name__ == "__main__":
    import sys
    dev = _test(sys.argv)

