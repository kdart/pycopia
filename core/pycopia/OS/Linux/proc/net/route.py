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
Routing table via /proc/net/route.
Note that the RouteEntry returns values in host byte order, not the network
byte order that the kernel file emits.

"""
from socket import ntohl

FILE="/proc/net/route"

# Flag bits
# from /usr/include/linux/route.h
RTF_UP=0x0001       # route usable
RTF_GATEWAY=0x0002      # destination is a gateway
RTF_HOST=0x0004     # host entry (net otherwise)
RTF_REINSTATE=0x0008        # reinstate route after tmout
RTF_DYNAMIC=0x0010      # created dyn. (by redirect)
RTF_MODIFIED=0x0020     # modified dyn. (by redirect)
RTF_MTU=0x0040      # specific MTU for this route
RTF_WINDOW=0x0080       # per route window clamping
RTF_IRTT=0x0100     # Initial round trip time
RTF_REJECT=0x0200       # Reject route


def _hex(i):
    return "%8X" % (i,)

class RouteEntry(object):
    """Represents a routing table entry. """
    def __init__(self, Iface, Destination=None, Gateway=None,
                Flags=0, RefCnt=0, Use=0, Metric=0, Mask=None, 
                MTU=0, Window=0, IRTT=0):
        self.Iface = Iface
        self.Destination = Destination
        self.Gateway = Gateway
        self.Flags = Flags
        self.RefCnt = RefCnt
        self.Use = Use
        self.Metric = Metric
        self.Mask = Mask
        self.MTU = MTU
        self.Window = Window
        self.IRTT = IRTT
    
    def __str__(self):
        return "\t".join([self.Iface]+map(_hex, [self.Destination, self.Gateway])+map(str, [
                self.Flags, self.RefCnt, self.Use, self.Metric]) + [_hex(self.Mask)] + 
                map(str, [self.MTU, self.Window, self.IRTT]))

    # informational methods
    def is_up(self):
        return self.Flags & RTF_UP
    is_active = is_up # alias
    
    def is_gateway(self):
        return self.Flags & RTF_GATEWAY
    
    def is_host(self):
        return self.Flags & RTF_HOST

    def is_reject(self):
        return self.Flags & RTF_REJECT

class RouteFlags(int):
    def __new__(cls, v):
        return int.__new__(cls, int(v, 16))
    def __str__(self):
        return "%04X" %(self,)
    

HEADER="Iface   Destination Gateway     Flags   RefCnt  Use Metric  Mask        MTU Window  IRTT"
class RouteTable(object):
    """Represents the kernel FIB. Supports sequence operators."""
    def __init__(self):
        self._entries = []
    
    def __str__(self):
        return "\n".join([HEADER] + map(str, self._entries))
    
    def __getitem__(self, idx):
        return self._entries[idx]
    
    def __iter__(self):
        return iter(self._entries)
    
    def update(self, filt=None):
        """update([filter])
Update the RouteTable with current values. If a filter function is supplied
then it will be called with a RouteEntry and must return a true or false value.
If true, the RouterEntry will be included in the table. If false, it will not.
"""
        self._entries = []
        lines = open(FILE).readlines()
        for line in lines[1:]:
            [iface, dest, gateway, flags, refcnt, use, metric, mask, 
                mtu, window, irtt] = line.split()
            rt = RouteEntry(iface, 
                    Destination=ntohl(int(dest, 16)), 
                    Gateway=ntohl(int(gateway, 16)),
                    Flags=RouteFlags(flags), 
                    RefCnt=int(refcnt, 16), 
                    Use=int(use, 16), 
                    Metric=int(metric, 16), 
                    Mask=ntohl(int(mask, 16)), 
                    MTU=int(mtu, 16), 
                    Window=int(window, 16), 
                    IRTT=int(irtt, 16))
            if filt: 
                if filt(rt):
                    self._entries.append(rt)
            else:
                self._entries.append(rt)

def get_route():
    rt = RouteTable()
    rt.update()
    return rt

def get_active_route():
    def _active(re):
        return re.is_active()
    rt = RouteTable()
    rt.update(_active)
    return rt

if __name__ == "__main__":
    rt = get_route()
    # print only UP/active routes
    for r in rt:
        if r.is_active():
            print r


