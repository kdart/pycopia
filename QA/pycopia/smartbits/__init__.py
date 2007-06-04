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

class SMBAddress(object):
    def __init__(self, hub_or_addr, slot=0, port=0):
        if isinstance( hub_or_addr, self.__class__):
            self.hub = hub_or_addr.hub
            self.slot = hub_or_addr.slot
            self.port = hub_or_addr.port
        else:
            self.hub = hub_or_addr
            self.slot = slot
            self.port = port

    def __str__(self):
        return "%d:%d:%d" % (self.hub, self.slot, self.port)

    def __repr__(self):
        return "%s(%d, %d, %d)" % (self.__class__.__name__, self.hub, self.slot, self.port)


