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
IPv4 module. Defines an IPv4 class (Internet Protocol address).
By Keith Dart, 1999

Exports helper functions:

itodq(int) - return dotted quad string given an integer.
dqtoi(string) - return and integer given a string in IP dotted-quad notation.
iprange(startip, number) - return a list of sequential hosts in a network, as strings.
ipnetrange(startnet, number) - return a list of sequential networks, as strings.
netrange(startnet, number, [increment]) - return a list of networks, as IPv4 objects.


The IPv4 class stores the IP address and mask. It also makes available the
network, host, and broadcast addresses via computed attributes.
See the IPv4 documentation for more details.


"""

from sys import maxint
# for the address translation functions
from pycopia import socket

class IPv4(object):
    """
    Store an IP addresss. Computes the network, host, and broadcast address on
    demand.

    Usage:
    ipaddress = IPv4(address, [mask])

    Supply an address as an integer,  dotted-quad string, list of 4
    integer octets, or another IPv4 object. A netmask may optionally be
    supplied. It defaults to a classful mask appropriate for its class.
    the netmask may be supplied as integer, dotted quad, or slash (e.g.
    /24) notation. The mask may optionally be part of the IP address, in
    slash notation. if an IPv4 object is initialized with another IPv4
    object, the address and mask are taken from it. In the case that a
    mask is obtained from the address parameter, the mask parameter will
    be ignored.

    For example:
    ip = IPv4("10.1.1.2")
    ip = IPv4("10.1.1.2", "255.255.255.0")
    ip = IPv4("10.1.1.2/24") # note that if a mask value was supplied,
                             # it would be ignored.

    Raises ValueError if the string representation is malformed, or is not an
    integer.

    Class attributes that you may set or read are:
        address   = 32 bit integer IP address
        mask      = 32 bit integer mask
        maskbits  = number of bits in the mask

    additional attributes that are read-only (UNDEFINED for /32 IPV4 objects!):
        network             = network number, host part is zero.
        host (or hostpart)  = host number, network part is zero.
        broadcast           = directed broadcast address, host part is all ones.
        firsthost           = What would be the first address in the subnet.
        lasthost            = What would be the last address in the subnet.

    Methods:
        copy() - Return a copy of this IPv4 address.
        nextnet() - Increments the IP address into the next network range.
        previousnet() - Decrements the IP address into the previous network range.
        nexthost() - Increments this IP address object's host number.
        previoushost() - Decrements this IP address object's host number.
        set_to_first() - Set the IP address to the first address in the subnet.
        set_to_last() - Set the IP address to the last address in the subnet.
        getStrings() - return a 3-tuple of address, mask and broadcast as dotted
                       quad strings.

    Operators:
        An IPv4 object can be used in a "natural" way with some python
        operators.  It behaves as a sequence object when sequence
        operators are applied to it.
        For example:
        ip = ipv4.IPv4("192.168.1.0", "255.255.255.248")
        ip[2] returns 2nd host in subnet.
        ip[-1] returns broadcast address.
        ip[0] returns network.
        ip[1:-1] returns list of IPv4 objects from first to last host.
        len(ip) returns number of hosts in network range, including net
                and broadcast.
        if ip3 in ip:     # test for inclusion in subnet
            print "In range"

        You may also perform some arithmetic operators;
        ip2 = ip + 2 # assigns ip2 to new IPv4 object two hosts greater than ip.
        ip2 > ip # returns true (can compare addresses)
        int(ip) # return IPv4 object address as integer
        hex(ip) # return IPv4 object address as hexadecimal string


    """
    __slots__ = ["_address", "_mask"]
    def __init__(self, address, mask=None):
        # determine input type and convert if necessary
        self._address = 0x0L; self._mask = None
        self.__handleAddress(address)
        # handle the optional mask parameter. Default to class mask.
        if self._mask is None:
            if mask is None:
                if self._address & 0x80000000L == 0:
                    self._mask = 0xff000000L
                elif self._address & 0x40000000L == 0:
                    self._mask = 0xffff0000L
                else:
                    self._mask = 0xffffff00L
            else:
                 self.__handleMask(mask)

    def __repr__(self):
        return "%s('%u.%u.%u.%u/%u')" % (self.__class__.__name__, (self._address >> 24) & 0x000000ff,
                            ((self._address & 0x00ff0000) >> 16),
                            ((self._address & 0x0000ff00) >> 8),
                            (self._address & 0x000000ff),
                            self.__mask2bits())

    def __str__(self):
        return "%u.%u.%u.%u" % ((self._address >> 24) & 0x000000ff,
                            ((self._address & 0x00ff0000) >> 16),
                            ((self._address & 0x0000ff00) >> 8),
                            (self._address & 0x000000ff))

    def __getstate__(self):
        return (self._address, self._mask)

    def __setstate__(self, state):
        self._address, self._mask = state

    def __iter__(self):
        return _NetIterator(self)

    def getStrings(self):
        """getStrings()
Returns a 3-tuple of address, mask, and broadcast address as dotted-quad string.
        """
        return itodq(self._address), itodq(self._mask), itodq(self.broadcast)
    address_mask_broadcast = property(getStrings)

    def cidr(self):
        """cidr() Returns string in CIDR notation."""
        return "%s/%u" % (itodq(self._address), self.__mask2bits())

    CIDR = property(cidr)

    address = property(lambda s: s._address,
            lambda s, v: s.__handleAddress(v),
            None, "whole address")
    mask = property(lambda s: s._mask,
            lambda s, v: s.__handleMask(v),
            None, "address mask")
    maskbits = property(lambda s: s.__mask2bits(),
            lambda s, v: s.__handleMask(s.__bits2mask(v)),
            None, "CIDR mask bits")

    network = property(lambda s: IPv4(s._address & s._mask, s._mask),
            None, None, "network part")

    def _get_broadcast(self):
        if self._mask == 0xffffffff:
            return 0xffffffff
        else:
            return self._address | (~self._mask & 0xffffffffL)
    broadcast = property(_get_broadcast)

    def _get_hostpart(self):
        # check for host specific address
        if self._mask == 0xffffffffL:
            return self._address
        else:
            return self._address & (~self._mask & 0xffffffffL)

    def _set_hostpart(self, value):
        self._address = ((self._address & self._mask) | 
                (long(value) & (~self._mask & 0xffffffffL)))

    host = property(_get_hostpart, _set_hostpart, None, "host part")
    hostpart = host

    firsthost = property(lambda s: IPv4((s._address & s._mask) + 1, s._mask),
                 None, None, "first host in range")

    lasthost = property(lambda s: IPv4(
            (s._address & s._mask) + ((~s._mask & 0xffffffffL) - 1), s._mask),
            None, None, "last host in range")

    # The IPv4 object can be initialized a variety of ways.
    def __handleAddress(self, address):
        # determine input type and convert if necessary
        if type(address) is str:
            # first, check for optional slash notation, and handle it.
            aml = address.split("/")
            if len(aml) > 1:
                self._address = nametoi(aml[0])
                self._mask = self.__bits2mask(long(aml[1]))
            else:
                self._address = nametoi(aml[0])
        elif type(address) in (long, int):
            self._address = long(address)
        elif type(address) is list: # a list of integers as dotted quad (oid)
            assert len(address) >= 4
            self._address = (address[0]<<24) | (address[1]<<16) | (address[2]<<8) | address[3]
        elif isinstance(address, IPv4):
            self._address = address._address
            self._mask = address._mask
        else:
            raise ValueError

    def __handleMask(self, mask):
        if type(mask) is str:
            if mask[0] == '/':
                bits = int(mask[1:])
                self._mask = self.__bits2mask(bits)
            else:
                self._mask = dqtoi(mask)
        elif type(mask) in (long, int):
            self._mask = long(mask)
        else:
            raise ValueError, "Invalid mask value: %r" % (mask,)

    def __bits2mask(self, bits):
        if bits <= 32 and bits >= 0:
            return (0xffffffffL << (32 - bits)) & 0xffffffffL
        else:
            raise ValueError, "mask bits must be in range 0 to 32"

    def __mask2bits(self):
        # Try to work around the fact the in Python, right shifts are always
        # sign-extended 8-( Also, cannot assume 32 bit integers.
        val = self._mask
        bits = 0
        for byte in range(4):
            testval = (val >> (byte * 8)) & 0xff
            while (testval != 0):
                if ((testval & 1) == 1):
                    bits += 1
                testval >>= 1
        return bits

    def __add__(self, increment):
        return IPv4(self._address + increment, self._mask)

    def __sub__(self, decrement):
        return IPv4(self._address - decrement, self._mask)

    def __int__(self):
        return long(self._address)

    def __long__(self):
        return long(self._address)

    def __hex__(self):
        return hex(self._address)

    def __hash__(self):
        return int(self._address % maxint)

    def __cmp__(self, other):
        return cmp(self._address, other._address)

    def __eq__(self, other):
        return self._address == other._address

    def __ne__(self, other):
        return self._address != other._address

    def __lt__(self, other):
        return self._address < other._address

    def __gt__(self, other):
        return self._address > other._address

    def __ge__(self, other):
        return self._address >= other._address

    def __le__(self, other):
        return self._address <= other._address

    # contains if networks are equal.
    def __contains__(self, other):
        other = self.__class__(other)
        if self._mask != other._mask:
            return 0
        return (self._address & self._mask) == (other._address & other._mask)

    # By defining these sequence operators, an IPv4 object can appear as a
    # "virtual" sequence of IPv4 objects.
    # e.g.: ip[4] will return the 4th host in network range. ip[-2] will
    # return the last. Note that ip[0] returns the network, and ip[-1]
    # returns the broadcast address.
    def __getitem__(self, index):
        if index >= 0:
            if index <= (~self._mask & 0xffffffffL):
                return IPv4(
                  (self._address & self._mask) + index, self._mask)
            else:
                raise IndexError, "Host out of range"
        else:
            if -index < (~self._mask & 0xffffffffL) + 1:
                return IPv4( (self._address & self._mask) + 
                       ((~self._mask & 0xffffffffL) + index + 1), 
                       self._mask)
            else:
                raise IndexError, "Host out of range"

    def __setitem__(self, index, value):
        raise IndexError, "cannot set a sequence index"

    # len(ip) is number of hosts in range, including net and broadcast.
    def __len__(self):
        return (~self._mask & 0xffffffffL) + 1

    def __getslice__(self, start, end):
        length = (~self._mask & 0xffffffffL) + 1
        selfnet = self._address & self._mask
        if end < 0:
            end = length + end
        if start < 0:
            start = length + start
        start = min(start, length)
        end = min(end, length)
        sublist = []
        for i in xrange(start, end):
            sublist.append(IPv4(selfnet + i, self._mask))
        return sublist

    def copy(self):
        return IPv4(self._address, self._mask)

    def __isub__(self, other):
        self._address -= long(other)
        # if host becomes broadcast address, bump it to next network
        if self.host == (~self._mask & 0xffffffffL):
            self._address -= 2
        return self

    def __iadd__(self, other):
        self._address += long(other)
        # if host becomes broadcast address, bump it to next network
        if self.host == (~self._mask & 0xffffffffL):
            self._address += 2
        return self

    def nexthost(self, increment=1):
        """
Increments this IP address object's host number. It will overflow into the
next network range. It will not become a broadcast or network address.

        """
        self._address = self._address + increment
        # if host becomes broadcast address, bump it to next network
        if self.host == (~self._mask & 0xffffffff):
            self._address += 2
        return self

    def previoushost(self, decrement=1):
        """
Decrements this IP address object's host number. It will underflow into the
next network range. It will not become a broadcast or network address.

        """
        self._address = self._address - decrement
        # if host becomes broadcast address, bump it to next network
        if self.host == (~self._mask & 0xffffffff):
            self._address -= 2
        return self

    def set_to_first(self):
        """
Set the address to the first host in the network.
        """
        self._address = (self._address & self._mask) + 1
        return self

    def set_to_last(self):
        """
Set the address to the last host in the network.
        """
        self._address = ((self._address & self._mask) + 
                             ((~self._mask & 0xffffffffL) - 1))
        return self

    def nextnet(self, increment=1):
        """
Increments the IP address into the next network range, keeping the host
part constant. Default increment is 1, but optional increment parameter
may be used.

        """
        self._address = self._address + ((~self._mask & 0xffffffffL) + 1) * increment
        return self

    def previousnet(self, decrement=1):
        """
Decrements the IP address into the next network range, keeping the host
part constant. Default decrement is 1, but optional decrement parameter
may be used.

        """
        self._address = self._address - ((~self._mask & 0xffffffffL) + 1) * decrement
        return self

    def gethost(self):
        """gethost()
    Resolve this IP address to a canonical name using gethostbyaddr."""
        try:
            hostname, aliases, others = socket.gethostbyaddr(str(self))
        except:
            return ""
        return hostname
    hostname = property(gethost, None, None, "associated host name")

##### end IPv4 object #########

class _NetIterator(object):
    def __init__(self, net):
        mask = self.mask = net._mask
        self.start = (net._address & mask)
        self.end = (net._address & mask) + (~mask & 0xffffffffL) - 1

    def __iter__(self):
        return self

    def next(self):
        if self.start == self.end:
            raise StopIteration
        self.start += 1
        return IPv4(self.start, self.mask)

### Useful helper functions. May also be useful outside this module. ###

def nametoi(name):
    """Resolve a name and return the IP address as an integer."""
    return dqtoi(socket.gethostbyname(name))

def dqtoi(dq):
    """dqtoi(dotted-quad-string)
Return an integer value given an IP address as dotted-quad string. You can also
supply the address as a a host name. """
    s = buffer(socket.inet_aton(dq))
    return (ord(s[0]) << 24) + (ord(s[1]) << 16) + (ord(s[2]) << 8) + (ord(s[3]))

def itodq(addr):
    """itodq(int_address) (integer to dotted-quad)
Return a dotted-quad string given an integer. """
    intval = long(addr) # might get an IPv4 object
    s = "%c%c%c%c" % (((intval >> 24) & 0x000000ff), ((intval & 0x00ff0000) >> 16),
        ((intval & 0x0000ff00) >> 8), (intval & 0x000000ff))
    return socket.inet_ntoa(s)

def iprange(startip, number, increment=1):
    """
iprange: return a list of consequtive IP address strings.
Usage:
    iprange(startip, number)
Where:
    startip is an IP address to start from.
    number is the number of IP addresses in the returned list.
    """
    # make a copy first
    start = IPv4(startip)
    ips = []
    for i in xrange(number):
        ips.append(str(start))
        start.nexthost(increment)
    return ips


def ipnetrange(startnet, number, increment=1):
    """
ipnetrange: return a list of consecutive networks, starting from initial
network and mask, keeping the mask constant.
Usage:
    ipnetrange(startnet, number, [increment])
Where:
    startnet is an IP address where the range will start.
    number is the number of IP networks in the range
    optional increment will skip that number of nets.

    """
    start = IPv4(startnet)
    ips = []
    baseaddress = start.address
    for i in xrange(number):
        start.address = baseaddress + (~start.mask+1) * (i*increment)
        ips.append(str(start))
    return ips

def netrange(startnet, number, increment=1):
    """
netrange: return a list of consecutive networks, starting from initial
network and mask, keeping the mask constant.
Usage:
    netrange(startnet, number, [increment])
Where:
    startnet is an IP address where the range will start.
    number is the number of IP networks in the range.
    An optional increment will set the stride (count by <increment> nets).

    """
    ips = []
    counter = IPv4(startnet)
    for i in xrange(number):
        ips.append(counter.copy())
        counter.nextnet(increment)
    return ips


def resolve(host, mask=None):
    """resolve(hostname, [mask]
Resolve a hostname to an IPv4 object. An optional mask value may me supplied."""
    try:
        hostname, aliases, addresses = socket.gethostbyname_ex(str(host))
    except socket.gaierror, why:
        raise ValueError, "Unable to resolve host: %s" % (why[1])
    if addresses:
        return IPv4(addresses[0], mask)
    else:
        raise ValueError, "No addresses found."

def sortnets(l):
    l = list(l)
    def _netcmp(a, b):
        return cmp(b.maskbits, a.maskbits)
    l.sort(_netcmp)
    return l

def findnet(ip, ipnets):
    ip = IPv4(ip)
    for ipnet in sortnets(ipnets):
        ip.mask = ipnet.mask
        if ip in ipnet:
            return ipnet
    return None

# objects for IP address management

# arbitary (non-VLSM) range of IP addresses in same network. For VLSM ranges
# just use an IPv4 object.
class IPRange(object):
    def __init__(self, start, end):
        start = IPv4(start)
        end = IPv4(end)
        self._len = long(start) - long(end)
        if self._len < 0:
            self._len *= -1
            self._start = start
            self._end = end
        else:
            self._start = end
            self._end = start
        self._index = 0
        assert self._start._mask == self._end._mask, "start and end are not in the same network"
        self._mask = self._start._mask

    def __repr__(self):
        return "%s.%s(%r, %r)" % (self.__class__.__module__, self.__class__.__name__, self._start, self._end)
    def __str__(self):
        return "(%s, %s)" % (self._start.cidr(), self._end.cidr())

    def __contains__(self, other):
        other = IPv4(other)
        if self._start._mask != other._mask:
            return False
        return self._start._address <= other._address and self._end._address >= other._address

    def next(self):
        if self._index <= self._len:
            rv = self._start+self._index
            self._index += 1
            return rv
        else:
            raise StopIteration

    def __iter__(self):
        self._index = 0
        return self

    def __getitem__(self, idx):
        if idx < 0:
            idx = self._len + idx + 1
        if idx < 0 or idx > self._len:
            raise IndexError, "IPRange index out of range"
        else:
            return self._start + idx

class IPAddressSet(object):
    pass


