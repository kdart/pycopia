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
Demo SNMP API.
Supply a host and community on the command line.

"""

import sys
from pycopia.SNMP import SNMP

# common code - get an SNMP session object.
host = sys.argv[1] ; community = sys.argv[2]

box = SNMP.get_session(host, community)

# bug here... must import Python mibs so that OIDMAP gets created.
from pycopia.mibs import SNMPv2_MIB
from pycopia.mibs import IF_MIB

print "Direct OID list method:"
print box.get([1, 3, 6, 1, 2, 1, 1, 5, 0]) # get OID from some other source
print

print "MIB node and raw SNMP method:"
try:
    from pycopia.SMI import SMI
except ImportError, err:
    print err
    print "you need libsmi and the libsmi wrappers installed for this demo."
else:
    oid1 = SMI.get_node('IF-MIB::ifName').OID + [1] # InterfaceIndex
    oid2 = SMI.get_node('SNMPv2-MIB::sysName').OID + [0]
    # same SNMP methods
    for varbind in box.get(oid1, oid2):
        print varbind.value
    print

print "Abstract API method:"
# get SMI instance
ifname = IF_MIB.ifName(indexoid=[1]) # ColumnObject needs indexoid
sysname = SNMPv2_MIB.sysName()

# Get the SMI using the SNMP session. useful for getting the same MIB variable
# from many devices/sessions (iterate over a list of sessions).
print ifname.get(box)
print sysname.get(box)
print

# can combine into one-liner, of course.
print "Abstract API one-liner:"
print IF_MIB.ifName(indexoid=[1]).get(box)
print SNMPv2_MIB.sysName().get(box)
print


print "Direct table:"
from pycopia.SMI import Objects
ift = Objects.get_table(box, IF_MIB.ifEntry) # dictionary
print "Interface entries:"
for iface in ift.values():
    print iface.ifDescr
print "Entire row data for last interface:"
print iface
del ift, iface
print

###################
print "Manager interface:"
from pycopia.SNMP import Manager

# Define a class that represents a managed device.
# You can add device-special methods here. See the Devices package for more examples.
class DeviceManager(Manager.Manager):
    pass

device = DeviceManager(box)
# add all the MIB modules the device supports...
device.add_mibs([SNMPv2_MIB, IF_MIB])

print "Available tables:"
print device.get_tables()
print

print "Interface entries:"
FMT = "%32.32s %20.20s %20.20s"
print FMT % ("Desc", "Out Pkts", "In Pkts")
for iface in device.getall('If'):
    print FMT % (iface.ifDescr, iface.ifOutUcastPkts, iface.ifInUcastPkts)

