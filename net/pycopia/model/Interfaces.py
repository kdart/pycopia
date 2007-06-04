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
Interface types

"""


### Interfaces - define interface types
# virtual base classes
class Interface(object):
    def __init__(self, node, netlink, index=-1):
        self.node = node
        self.network = netlink
#       self.ifEntry = SMI.OID("1.3.6.1.2.1.2.2.1")
#       self.ifEntry.ifIndex = index
        self.ifIndex = index
    
class PhyInterface(Interface):
    pass

class VirtInterface(Interface):
    pass


# Physical (singular) interfaces
class SyncronousSerial(PhyInterface):
    pass

class HighSpeedSerialInterface(PhyInterface):
    pass

class Ethernet(PhyInterface):
    pass

class FastEthernet(PhyInterface):
    pass

class GigabitEthernet(PhyInterface):
    pass

class TokenRing(PhyInterface):
    pass


