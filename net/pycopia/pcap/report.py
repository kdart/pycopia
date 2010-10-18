#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Report on pcap files.

"""

import getopt
import struct

# scapy is a bit weird. You have to import this stuff just for their side
# effects. Otherwise, this script won't work.
from scapy import config
from scapy import packet
from scapy import layers
from scapy.layers import l2

from scapy.utils import PcapReader


def get_macs(fname):
    """Yield src and dst MAC addresses."""
    rdr = PcapReader(fname)
    try:
        for pkt in rdr:
            l2 = pkt.firstlayer()
            yield l2.src, l2.dst
    finally:
        rdr.close()


def get_unique_macs(namelist, dstset=None, srcset=None):
    dstset = set() if dstset is None else dstset
    srcset = set() if srcset is None else srcset
    for fname in namelist:
        for src, dst in get_macs(fname):
            srcset.add(MACaddress(src))
            if dst != 'ff:ff:ff:ff:ff:ff':
                dstset.add(MACaddress(dst))
    return dstset, srcset


class MACaddress(long):
    def __new__(cls, macstr):
        return long.__new__(cls, long(macstr.replace(":", ""), 16))

    def to_cisco(self):
        return to_cisco(self)

    def to_hex(self):
        return to_hex(self)

    def __hex__(self):
        return to_hex(self)

    def __str__(self):
        return to_hex(self)


def to_cisco(l):
    s = []
    s.append("{0:04x}".format(l & 0xffff))
    l >>= 16
    s.append("{0:04x}".format(l & 0xffff))
    l >>= 16
    s.append("{0:04x}".format(l & 0xffff))
    s.reverse()
    return ".".join(s)


def to_hex(l):
    s = []
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.append("{0:02x}".format(l & 0xff))
    l >>= 8
    s.reverse()
    return ":".join(s)



def pcap_report(argv):
    """pcapinfo [-h?] [-m] [-c] <pcap file>...
    
    Report information about pcap files.
    Where:
        -h (?)  -- Print this help.
        -m      -- Report the set of unique MAC addresses contained in the
                   files.
        -c         Print Cisco style MAC addesses. Otherwise, hex strings.
    """
    reportmacs = False
    ciscostyle = False
    try:
        optlist, args = getopt.getopt(argv[1:], "h?mc")
    except getopt.GetoptError:
            print smtpcli.__doc__
            return
    for opt, val in optlist:
        if opt in ("-?", "-h"):
            print pcap_report.__doc__
            return
        elif opt == "-m":
            reportmacs = True
        elif opt == "-c":
            ciscostyle = True

    if reportmacs:
        dst, src = get_unique_macs(args)
        for h, s in (("Destination Macs:", dst), ("Source macs:", src)):
            print h
            while s:
                mac = s.pop()
                if ciscostyle:
                    print "  ", mac.to_cisco()
                else:
                    print "  ", mac.to_hex()



if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    pcap_report(sys.argv)

