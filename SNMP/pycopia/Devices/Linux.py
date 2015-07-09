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


