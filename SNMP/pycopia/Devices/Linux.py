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
Device manager for a Linux (or other Unix) machine running the net-snmp agent.


"""


import sys

from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB 
from pycopia.mibs import UCD_SNMP_MIB
from pycopia.mibs import HOST_RESOURCES_MIB


class LinuxManager(Manager.Manager):
    def get_processes(self):
        return self.getall("prEntry")


def get_manager(sessiondata):
    sess = SNMP.new_session(sessiondata)
    dev = LinuxManager(sess)
    dev.add_mibs([SNMPv2_MIB, HOST_RESOURCES_MIB])
    dev.add_mib(UCD_SNMP_MIB, subclassmodule=sys.modules[__name__])
    return dev


