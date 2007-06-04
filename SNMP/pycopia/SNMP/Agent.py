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
Implements an SNMP agent role.

"""

class Agent(object):
    """
An instance of this class will act as an SNMP agent. This is a generic base
class that should be subclassed by a module in the Devices package to implement
a specific Agent.

    """
    def add_mibs(self, XXX):
        raise NotImplementedError

    def add_mib(self, XXX):
        raise NotImplementedError

    def open(self, socket=161):
        pass
    
    def send_trap(self, XXX):
        pass
    
    def register_managed_object(self, oid, callback):
        pass

    

