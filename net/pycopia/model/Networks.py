#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Network technologies.

"""

class Network(object):
    """
The Network class is a pure virtual class from which all other network
types inherit. It may define attributes and methods common to all types of
networks.
    """
    pass


# General network classifications
class LocalAreaNetwork(Network):
    pass

class WideAreaNetwork(Network):
    pass

class MetropolitanAreaNetwork(Network):
    pass

class StorageAreaNetwork(Network):
    pass


# network access types
class MultiAccess(Network):
    pass

class BroadcastMultiAccess(MultiAccess):
    pass

class NonBroadcastMultiAccess(MultiAccess):
    pass

class PointToPoint(Network):
    pass

class PointToMultiPoint(Network):
    pass

# Specific technologies
class Ethernet(LocalAreaNetwork, BroadcastMultiAccess):
    pass

class FastEthernet(LocalAreaNetwork, BroadcastMultiAccess):
    pass

class GigabitEthernet(LocalAreaNetwork, BroadcastMultiAccess):
    pass

class TokenRing(LocalAreaNetwork, BroadcastMultiAccess):
    pass

class FDDI(LocalAreaNetwork, BroadcastMultiAccess):
    pass


# frame relay aggregate network properties depend on its configuration
# Basic PVC
class FrameRelay(WideAreaNetwork, PointToPoint):
    pass

# full mesh
class FrameRelayNBMA(WideAreaNetwork, NonBroadcastMultiAccess):
    pass

# partial mesh
class FrameRelayPTMP(WideAreaNetwork, PointToMultiPoint):
    pass


