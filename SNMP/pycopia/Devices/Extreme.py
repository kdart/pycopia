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
Device manager for Extreme etherswitch Device.

"""

import keyword

from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager


MIBNAMES = [
"SNMPv2_MIB", 
"RFC_1213", 
"IP_FORWARD_MIB", 
"BRIDGE_MIB", 
"ENTITY_MIB", 
"EtherLike_MIB", 
"RMON_MIB", 
"RMON2_MIB", 
"MAU_MIB", 
"RIPv2_MIB", 
"RADIUS_ACC_CLIENT_MIB", 
"RADIUS_ACC_SERVER_MIB", 
"RADIUS_AUTH_CLIENT_MIB", 
"RADIUS_AUTH_SERVER_MIB", 
"EXTREME_BASE_MIB", 
"EXTREME_DLCS_MIB", 
"EXTREME_EDP_MIB", 
"EXTREME_ESRP_MIB", 
"EXTREME_FILETRANSFER_MIB", 
"EXTREME_PBQOS_MIB", 
"EXTREME_PORT_MIB", 
"EXTREME_QOS_MIB", 
"EXTREME_RTSTATS_MIB", 
"EXTREME_SLB_MIB", 
"EXTREME_SYSTEM_MIB", 
"EXTREME_TRAP_MIB", 
"EXTREME_TRAPPOLL_MIB", 
"EXTREME_VC_MIB", 
"EXTREME_VLAN_MIB", 
]

MIBS = map(lambda n: __import__("mibs.%s" % n, globals(), locals(), ["*"]), MIBNAMES)

#import mibs.SNMPv2_MIB
#import mibs.RMON_MIB


class ExtremeManager(Manager.Manager):
    pass


def get_manager(sessiondata):
    sess = SNMP.new_session(sessiondata)
    dev = ExtremeManager(sess)
    dev.add_mibs(MIBS)
    return dev


