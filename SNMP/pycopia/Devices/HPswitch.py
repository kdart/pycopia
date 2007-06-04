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
SNMP device manager for the following HP etherswitch models.

  HP J4812A, HP J4813A, HP J4819A, HP J4848A, HP J4849A,
  HP J4850A, HP J4861A, HP J4865A, HP J4887A, HP J4888A,
  HP J4903A, HP J490XA, HP J8130A

"""


import sys
from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB

MIBNAMES = [
 "BRIDGE_MIB",
 "CISCO_CDP_MIB",
 "CISCO_SMI",
 "CISCO_TC",
 "CISCO_VTP_MIB",
 "CONFIG_MIB",
 "ENTITY_MIB",
 "EtherLike_MIB",
 "HC_RMON_MIB",
 "HP_ICF_BASIC",
 "HP_ICF_BRIDGE",
 "HP_ICF_CHASSIS",
 "HP_ICF_DOWNLOAD",
 "HP_ICF_FAULT_FINDER_MIB",
 "HP_ICF_GENERIC_RPTR",
 "HP_ICF_IP_ROUTING",
 "HP_ICF_LINKTEST",
 "HP_ICF_OID",
 "HP_ICF_OSPF",
 "HP_ICF_RIP",
 "HP_ICF_SECURITY",
 "HP_ICF_XRRP",
 "HP_SN_OSPF_GROUP_MIB",
 "HP_SNTPclientConfiguration_MIB",
 "HP_SwitchStack_MIB",
 "HP_VLAN",
 "IANA_RTPROTO_MIB",
 "IANAifType_MIB",
 "IEEE8021_PAE_MIB",
 "IEEE8023_LAG_MIB",
 "IF_MIB",
 "IP_FORWARD_MIB",
 "MAU_MIB",
 "NETSWITCH_MIB",
 "OSPF_MIB",
 "OSPF_TRAP_MIB",
 "P_BRIDGE_MIB",
 "Q_BRIDGE_MIB",
 "RADIUS_ACC_CLIENT_MIB",
 "RADIUS_AUTH_CLIENT_MIB",
 "RFC1213_MIB",
 "RIPv2_MIB",
 "RMON_MIB",
 "RMON2_MIB",
 "SEMI_MIB",
 "SMON_MIB",
 "SNMP_MPD_MIB",
 "SNMP_NOTIFICATION_MIB",
 "SNMP_TARGET_MIB",
 "SNMP_USER_BASED_SM_MIB",
 "SNMP_VIEW_BASED_ACM_MIB",
 "SNMPv2_MIB",
 "SNMPv2_SMI",
 "STATISTICS_MIB",
]

MIBS = map(lambda n: __import__("mibs.%s" % n, globals(), locals(), ["*"]), MIBNAMES)

# main manager object
class HPSwitchManager(Manager.Manager):
    pass

# factory function
def get_session(sessiondata):
    sess = SNMP.new_session(sessiondata)
    dev = HPSwitchManager(sess)
    dev.add_mibs(MIBS)
    return dev


def get_manager(device, community):
    sd = SNMP.sessionData(device, version=1)
    sd.add_community(community, SNMP.RW)
    sess = SNMP.new_session(sd)
    dev = HPSwitchManager(sess)
    dev.add_mibs(MIBS)
    return dev

