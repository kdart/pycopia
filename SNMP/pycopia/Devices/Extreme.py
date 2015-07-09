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


def get_manager(device, community):
    return Manager.get_manager(device, community, ExtremeManager, MIBS)

