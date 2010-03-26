#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010  Keith Dart <keith@kdart.com>
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
Device manager for a Linux (or other Unix) machine running the net-snmp agent.

"""


from pycopia.SNMP import Manager



MIBNAMES = [
    "NET_SNMP_TC",
    "NET_SNMP_EXAMPLES_MIB",
    "NET_SNMP_MIB",
    "NET_SNMP_EXTEND_MIB",
    "NET_SNMP_AGENT_MIB",
    "HOST_RESOURCES_MIB",
    "IF_MIB",
]


class LinuxManager(Manager.Manager):
    def get_processes(self):
        return self.getall("prEntry")


def get_manager(device, community):
    return Manager.get_manager(device, community, LinuxManager, MIBNAMES)


