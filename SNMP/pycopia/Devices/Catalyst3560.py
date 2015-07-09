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
Manager constructor for Cisco Catalyst 3560 Ethernet switch.

"""

from pycopia.SNMP import Manager

MIBNAMES = [
    "SNMPv2_MIB",
    "SNMP_NOTIFICATION_MIB",
    "SNMP_PROXY_MIB",
    "SNMP_TARGET_MIB",
    "SNMP_USM_AES_MIB",
    "NET_SNMP_VACM_MIB",
    "BRIDGE_MIB",
    "CISCO_ACCESS_ENVMON_MIB",
    "CISCO_BRIDGE_EXT_MIB",
    "CISCO_BULK_FILE_MIB",
    "CISCO_CAR_MIB",
    "CISCO_CDP_MIB",
    "CISCO_CIRCUIT_INTERFACE_MIB",
    "CISCO_CLUSTER_MIB",
    "CISCO_CONFIG_COPY_MIB",
    "CISCO_CONFIG_MAN_MIB",
    "CISCO_DHCP_SNOOPING_MIB",
    "CISCO_ENTITY_VENDORTYPE_OID_MIB",
    "CISCO_ENVMON_MIB",
    "CISCO_FLASH_MIB",
    "CISCO_FTP_CLIENT_MIB",
    "CISCO_HSRP_EXT_MIB",
    "CISCO_HSRP_MIB",
    "CISCO_IF_EXTENSION_MIB",
    "CISCO_IGMP_FILTER_MIB",
    "CISCO_IMAGE_MIB",
    "CISCO_IP_STAT_MIB",
    "CISCO_L2L3_INTERFACE_CONFIG_MIB",
    "CISCO_LAG_MIB",
    "CISCO_MAC_NOTIFICATION_MIB",
    "CISCO_MEMORY_POOL_MIB",
    "CISCO_PAE_MIB",
    "CISCO_PAGP_MIB",
    "CISCO_PING_MIB",
    "CISCO_PORT_QOS_MIB",
    "CISCO_PORT_SECURITY_MIB",
    "CISCO_PORT_STORM_CONTROL_MIB",
    "CISCO_PRIVATE_VLAN_MIB",
    "CISCO_PROCESS_MIB",
    "CISCO_RTTMON_MIB",
    "CISCO_STACK_MIB",
    "CISCO_STACKMAKER_MIB",
    "CISCO_STP_EXTENSIONS_MIB",
    "CISCO_SYSLOG_MIB",
    "CISCO_TCP_MIB",
    "CISCO_UDLDP_MIB",
    "CISCO_VLAN_IFTABLE_RELATIONSHIP_MIB",
    "CISCO_VLAN_MEMBERSHIP_MIB",
    "CISCO_VTP_MIB",
    "CISCO_PRODUCTS_MIB",
    "ENTITY_MIB",
    "EtherLike_MIB",
    "HC_RMON_MIB",
    "IEEE8021_PAE_MIB",
    "IEEE8023_LAG_MIB",
    "IF_MIB",
    "NOTIFICATION_LOG_MIB",
    "OLD_CISCO_CHASSIS_MIB",
    "OLD_CISCO_CPU_MIB",
    "OLD_CISCO_FLASH_MIB",
    "OLD_CISCO_INTERFACES_MIB",
    "OLD_CISCO_IP_MIB",
    "OLD_CISCO_MEMORY_MIB",
    "OLD_CISCO_SYSTEM_MIB",
    "OLD_CISCO_TCP_MIB",
    "OLD_CISCO_TS_MIB",
    "RFC1213_MIB",
    "RMON_MIB",
    "RMON2_MIB",
    "SMON_MIB",
    "TCP_MIB",
    "UDP_MIB",
]


class C3560Manager(Manager.Manager):
    pass


def get_manager(device, community):
    return Manager.get_manager(device, community, C3560Manager, MIBNAMES)


