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
Port of smartlib's Samples/C/CBasic/1stTest.c 

"""

import sys
from smartbits import *

hub1 = 0
slot1 = 0
port1 = 0
hub2 = 0
slot2 = 1
port2 = 0
numPackets = 100000

if len(sys.argv) > 1:
    ipaddr = sys.argv[1]
else:
    ipaddr = raw_input("Enter IP address of SmartBits chassis ==> ")
rv = ETSocketLink(ipaddr, 16385)
if rv < 0:
    print "Error linking to chassis: %d " % rv
    sys.exit(rv)

print "successfully linked"

# reset cards
HTResetPort(RESET_FULL, hub1, slot1, port1)
HTResetPort(RESET_FULL, hub2, slot2, port2)

# clear counters
HTClearPort(hub1, slot1, port1)
HTClearPort(hub2, slot2, port2)

# set transmission parameters, single burst of numPackets packets
HTTransmitMode(SINGLE_BURST_MODE,hub1,slot1,port1)
HTBurstCount(numPackets,hub1,slot1,port1)

# start transmitting from the first card
HTRun(HTRUN,hub1,slot1,port1)

# you could need a delay here before reading counter data
raw_input("Press ENTER key to get counts.")

# get the transmit counts from card1 then the receive counts from card2
cs = HTCountStructure()
HTGetCounters(cs, hub1, slot1, port1)
txPackets = cs.TmtPkt
HTGetCounters(cs, hub2, slot2, port2)
rxPackets = cs.RcvPkt
if txPackets == rxPackets:
   print "Test Passed! %d packets transmitted and %d packets received." % (txPackets, rxPackets)
else:
   print "Test Failed! %d packets transmitted and %d packets received." % (txPackets, rxPackets)

ETUnLink()



