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
SNMP device manager for the following Dell etherswitch models.

Dell PowerConnect 6224
Dell PowerConnect 6248

"""
import sys

from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB

MIBNAMES = [
 "BRIDGE_MIB",
 "CONFIG_MIB",
 "ENTITY_MIB",
 "EtherLike_MIB",
 "IANA_RTPROTO_MIB",
 "IANAifType_MIB",
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
 "SNMP_NOTIFICATION_MIB",
 "SNMP_TARGET_MIB",
 "SNMP_USER_BASED_SM_MIB",
 "SNMP_VIEW_BASED_ACM_MIB",
 "SNMPv2_MIB",
 "SNMPv2_SMI",
]

MIBS = [__import__("pycopia.mibs.%s" % n, globals(), locals(), ["*"]) for n in MIBNAMES]

# main manager object
class DellSwitchManager(Manager.Manager):
    pass

# factory function
def get_session(sessiondata):
    sess = SNMP.new_session(sessiondata)
    dev = DellSwitchManager(sess)
    dev.add_mibs(MIBS)
    return dev


def get_manager(device, community):
    sd = SNMP.sessionData(device, version=1)
    sd.add_community(community, SNMP.RW)
    sess = SNMP.new_session(sd)
    dev = DellSwitchManager(sess)
    dev.add_mibs(MIBS)
    return dev

