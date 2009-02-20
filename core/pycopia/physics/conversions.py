#!/usr/bin/python2.4
# -*- coding: us-ascii -*-
# vim:ts=2:sw=2:softtabstop=0:tw=74:smarttab:expandtab


"""General conversion functions.

Convert units from one to another. Generally you can use a
PhysicalQuantity object to do linear conversions. But that doesn't handle
logarithmic units yet.

All voltages are RMS values.
"""

import math

def dBVToVolts(dbv):
  return 10.0**(dbv / 20.0)

def VoltsTodBV(v):
  return 20.0 * math.log10(v / 1.0)

def VoltsTodBu(v):
  return 20.0 * math.log10(v / 0.77459667)

def dBuToVolts(dbu):
  return 0.77459667 * 10.0**(dbu / 20.0)

def dBmToWatts(dbm):
  return 0.001 * 10.0**(dbm / 10.0)

def WattsTodBm(w):
  return 10.0 * math.log10(w / 0.001)


