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

import sys
import SNMP.SNMP as SNMP

import pdb

#sd = SNMP.sessionData("172.20.165.20") # regression
#sd = SNMP.sessionData("172.20.149.40") # dev14
#sd = SNMP.sessionData("192.168.146.97") # sum4_1
sd = SNMP.sessionData("rosita")
sd.add_community("public", SNMP.RO)
sd.add_community("private", SNMP.RW)
session = SNMP.new_session(sd)

import mibs.SNMPv2_MIB
#import mibs.UDP_MIB
#import mibs.TCP_MIB
#import mibs.BRIDGE_MIB
#import mibs.RMON_MIB
#import mibs.RMON2_MIB
#import mibs.EtherLike_MIB
#import mibs.EXTREME_BASE_MIB
#import mibs.EXTREME_VLAN_MIB
#import mibs.EXTREME_PORT_MIB
#import mibs.EXTREME_SYSTEM_MIB
#import mibs.IP_FORWARD_MIB
#import mibs.IP_MIB

sysname = mibs.SNMPv2_MIB.sysName()

#pdb.runcall(sn.get, session)
print sysname.get(session)
t = be.getRawTable(session)
print t

vpns = VPNEntry.getRawTable(session)
print vpns

routers = VPNRouter.getRawTable(session)
print routers



#box = SNMP.Manager.Manager(session)

#print "System Name       :", box.sysName
#print "System Uptime     :", box.sysUpTime
#print "UDP In Datagrams  :", box.udpInDatagrams
#print "UDP Out Datagrams :", box.udpOutDatagrams


#to = box.udp
#print to.attributes
#print to.rowstatus
#print to.indexes
#print to

#print box.get_attributes()
#scalars = box.get_scalars()
#for attrib in scalars:
#   print "%35s : %s" % (attrib, getattr(box, attrib))

#blades = box.getall(Objects.Blade)

