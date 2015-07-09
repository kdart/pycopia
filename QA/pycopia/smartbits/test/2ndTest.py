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

try:
    if len(sys.argv) > 1:
        linkToSmartBits(sys.argv[1])
    else:
        linkToSmartBits()
except SmartlibError, err:
    print_error_desc(err)
    sys.exit(1)

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



