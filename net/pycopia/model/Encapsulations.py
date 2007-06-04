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
Protocol Encapsulation objects.

"""

class Header(object):
    """
Virtual base class for all protocol headers.
    """
    def __init__(self):
        self.header = ""


# layer 2 encapsulations
class Encapsulation(Header):
    pass

class Ethernet(Encapsulation):
    pass

class Ethernet_II(Ethernet):
    pass

class Ethernet_8023(Ethernet):
    pass

class Ethernet_SNAP(Ethernet_8023):
    pass

class TokenRing_8025(Ethernet):
    pass

class PointToPointProtocol(Encapsulation):
    pass

class AsyncPPP(PointToPointProtocol):
    pass

class SyncPPP(PointToPointProtocol):
    pass

class HDLC(Encapsulation):
    pass

class Cisco_HDLC(Encapsulation):
    pass

class FrameRelayFrame(Encapsulation):
    pass


# Layer 3 transports
class IPv4(Header):
    pass

class IPv6(Header):
    pass

class IPX(Header):
    pass

class DDP(Header):
    pass


# layer 3 support
class AddressResolutionProtocol(Header):
    pass

class ReverseAddressResolutionProtocol(Header):
    pass

class InverseAddressResolutionProtocol(Header):
    pass

class InternetControlMessageProtocol(Header):
    pass

class BootProtocol(Header):
    pass

class DynamicHostConfigurationProtocol(Header):
    pass

# layer 4 transports
class TCP(Header):
    pass

class UDP(Header):
    pass

class SPX(Header):
    pass

class CLNP(Header):
    pass

# IPsec
class EncapsulatingSecurityPayload(Header):
    pass

class AuthenticationHeader(Header):
    pass


# routing protocols

# virtual base class for routing protocols
class RoutingProtocol(Header):
    pass

class BGP4(RoutingProtocol):
    pass

class OSPF(RoutingProtocol):
    pass

class RIP(RoutingProtocol):
    pass

class RIP2(RoutingProtocol):
    pass

class IGRP(RoutingProtocol):
    pass

class EIGRP(RoutingProtocol):
    pass

class IPX_RIP(RoutingProtocol):
    pass

class RTMP(RoutingProtocol):
    pass


