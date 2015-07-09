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

