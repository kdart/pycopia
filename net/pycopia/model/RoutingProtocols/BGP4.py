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

import sys, os
import struct

# Networks modules
import common
from NetworkUtils import Bitfield

class Route:
    pass

class IPPrefix:
    def __init__(self, prefix=0, length=0):
        self.struct_pack = 'Bs'
        self.prefix = prefix
        self.length = length

class Attribute(common.Header):
    def __init__(self, flags=0, type=0, length=0, value=""):
        self.struct_pack = 'BBss'
        self.flags = Bitfield(flags)
        self.type = type
        self.length = length
        self.value = value


class Message(common.Header):
    def __init__(self, marker=0, length=0, type=1):
        self.struct_pack = '16BHB'
        self.marker = marker
        self.length = length
        self.type = type

class OpenMessage(Message):
    def __init__(self, version=4, myAS=0, hold_time=3600, identifier=0, optional=""):
        self.struct_pack = 'BHHIBs'
        self.version = version
        self.AS = myAS
        self.hold_time = hold_time
        self.identifier = identifier
        self.opt_len = len(optional)
        self.optional = optional

class UpdateMessage(Message):
    def __init__(self, withdrawn=None, path_attributes=None, reachability=None):
        self.struct_pack = 'HsHss'
        self.withdrawn = withdrawn
        self.path_attributes = path_attributes
        self.reachability = reachability
    

class NotificationMessage(Message):
    def __init__(self, code=0, subcode=0, data=""):
        self.struct_pack = 'BBs'
        self.code = code
        self.subcode = subcode
        self.data = data


class KeepaliveMessage(Message):
    pass



# Routing base

class RIB:
    """
Abstract base class for RIBs.
    """
    pass

class Adj_RIB_In(RIB):
    """
Candidate routes recieved from peers. One per peer.
    """
    pass

class Loc_RIB(RIB):
    """
Local RIB is the actual routing RIB. There is only one.
    """
    pass

class Adj_RIB_Out(RIB):
    """
Candidate routes for transission to peers. One per peer.
    """
    pass


