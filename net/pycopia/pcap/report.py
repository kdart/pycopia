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

import struct
import getopt

import pcap
import dpkt



def get_macs(fname):
    pc = pcap.pcap(fname)
    for ts, pkt in pc:
        pkt = dpkt.ethernet.Ethernet(pkt)
        yield ts, struct.unpack("!Q", "\0\0"+pkt.src)[0], struct.unpack("!Q", "\0\0"+pkt.dst)[0]


def get_unique_macs(namelist, dstset=None, srcset=None):
    dstset = set() if dstset is None else dstset
    srcset = set() if srcset is None else srcset
    for fname in namelist:
        for ts, src, dst in get_macs(fname):
            srcset.add(MACaddress(src))
            if dst != 0xffffffffffffL:
                dstset.add(MACaddress(dst))
    return dstset, srcset


class MACaddress(long):

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


CISCO_CF_TEMPLATE = "mac-address-table static {mac} vlan {vlan} interface {interface}"


def pcap_report(argv):
    """pcapinfo [-h?] [-m] [-c] <pcap file>...

    Report information about pcap files.
    Where:
        -h (?)  -- Print this help.
        -m      -- Report the set of unique MAC addresses contained in the
                   files.
        -c         Print Cisco style MAC addesses. Otherwise, hex strings.
        -C <fname> Write Cisco config file for static mac entries.
        -v <id>    Supply VLAN ID for destination MAC when writing Cisco config.
        -i <intf>  Supply Cisco destination interface when writing Cisco config.
    """
    writecisco = False
    reportmacs = False
    ciscostyle = False
    fname = None
    vlan = None
    intf = None
    try:
        optlist, args = getopt.getopt(argv[1:], "h?mcC:v:i:")
    except getopt.GetoptError:
            print smtpcli.__doc__
            return
    for opt, val in optlist:
        if opt in ("-?", "-h"):
            print pcap_report.__doc__
            return
        elif opt == "-C":
            fname = val
            writecisco = True
        elif opt == "-m":
            reportmacs = True
        elif opt == "-v":
            vlan = int(val)
        elif opt == "-i":
            intf = val
        elif opt == "-c":
            ciscostyle = True

    if not args:
        print pcap_report.__doc__
        return

    if reportmacs:
        dst, src = get_unique_macs(args)
        if writecisco:
            if vlan is None or intf is None:
                print "You need to supply vlan and interface options."
                return
            with open(fname, "w") as fo:
                while dst:
                    mac = dst.pop()
                    fo.write(CISCO_CF_TEMPLATE.format(mac=mac.to_cisco(), vlan=vlan, interface=intf))
                    fo.write("\n")
                fo.write("end\n")
        else:
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

