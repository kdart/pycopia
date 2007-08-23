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
SNMP basic types, and well-known textual conventions.

"""

from struct import pack
from array import array

from pycopia import ipv4
from pycopia.aid import unsigned, unsigned64, IF, Enum

from pycopia.SMI import OIDMAP

class Range(object):
    def __init__(self, minValue=-2147483647, maxValue=2147483647):
        self.minValue = minValue
        self.maxValue = maxValue
    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, self.minValue, self.maxValue)
    def verify(self, value):
        return self.minValue <= value <= self.maxValue

class Ranges(list):
    def __init__(self, *args):
        super(Ranges, self).__init__(list(args))
    def __repr__(self):
        return "%s.%s(%s)" % (self.__class__.__module__, self.__class__.__name__, ", ".join(map(repr, self)))
    def verify(self, value):
        if True in map(lambda r: r.verify(value), self):
            return True
        return False
    def get_max(self):
        return reduce(lambda a, r: max(a, r.maxValue), self, self[0].maxValue)

    def get_min(self):
        return reduce(lambda a, r: min(a, r.minValue), self, self[0].minValue)

    max = property(get_max, None, None, "maximum value in ranges")
    min = property(get_min, None, None, "minimum value in ranges")


# This object is the interface to the pysmi module. 
class OID(list):
    def __init__(self, oid):
        if type(oid) is str:
            # filter out empty members (leading dot causes this)
            map(self.append, map(int, filter(len, oid.split('.'))))
        elif isinstance(oid, list):
            self.extend( oid )
        else:
            raise ValueError, "OID must be initialized with OID string, or list. "

    def __str__(self):
        return ".".join(map(lambda x: '%lu' % x, self))
        
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, super(OID, self).__repr__())
    
    def __cmp__(self, other):
        if not other:
            return -1
        # self can only be greater than other if prefixes match.
        cv = cmp(len(self), len(other))
        if cv < 0: # then self is shorter than other, defined as less
            return -1
        elif cv == 0: # then self is same size as other
            if self == other:
                return 0
            else:
                return -1
        else: # then self is longer than other
            if self[:len(other)] == other:
                return 1
            else:
                return -1

    # subtracting one oid from another removes any common prefix
    # (considered to be the difference).
    def __sub__(self, other):
        i = 0
        for s, o in map(None, self, list(other)):
            if s != o:
                break
            i += 1
        return self.__class__(self[i:])

    def __getslice__(self, i, j):
        cl = self.__class__
        return cl(list.__getslice__(self, i,j))

    def __add__(self, other):
        cl = self.__class__
        return cl(list.__add__(self, other))

# Abstract base classes for SNMP objects
class ObjectSyntax(object):
    def _ber_(self):
        raise NotImplementedError, "define _ber_in object class."
    def _oid_(self):
        raise NotImplementedError, "define _ber_in object class."
    def __repr__(self):
        return "%s.%s()" % (self.__class__.__module__, self.__class__.__name__)
    def __str__(self):
        return self.__class__.__name__

class SimpleSyntax(ObjectSyntax):
    pass

class ApplicationSyntax(ObjectSyntax):
    pass

class _ImplicitUnsigned(ApplicationSyntax):
    ranges = Ranges(Range(0, 4294967295L))

    def verify(self):
        return self.ranges.verify(self)

    def verify_ex(self):
        if not self.ranges.verify(self):
            raise ValueError, "value %s out of range for type %s" % (self, self.__class__.__name__)

    def _ber_(self):
        if self == 0:
            return self._ber_tag+"\x00"
        raw = pack("!Q", self)
        raw = raw.lstrip('\0')
        if (not raw) or (ord(raw[0]) & 0x80):
            result = '\0' + raw
        else:
            result = raw
        return self._ber_tag + encode_length(len(result)) +  result
    def _oid_(self):
        return ObjectIdentifier([self])
    def oid_decode(self, oid):
        return self.__class__(int(oid.pop(0)))


# concrete classes
class SequenceOf(list):
    _ber_tag = '\x30' # tagged sequence
    def _ber_(self):
        encodings = []
        for arg in self:
            if arg is None:
                encodings.append('\x05\0') # Null
            else:
                encodings.append(ber(arg))
        res = "".join(encodings)
        return self._ber_tag + encode_length(len(res)) + res

TAGGED_SEQUENCE = SequenceOf

class Boolean(int):
    "BOOLEAN"
    _ber_tag = '\x01'
    def __new__(cls, val):
        return int.__new__(cls, bool(val))
    def _ber_(self):
        if self: # pre-computed constant
            return '\x01\x01\xff'
        else:
            return '\x01\x01\x00'
    def __str__(self):
        if self:
            return "True"
        else:
            return "False"
    def __repr__(self):
        return "%s.%s(%s)" % (self.__class__.__module__, self.__class__.__name__, IF(self, "True", "False"))
    def __hash__(self):
        return int.__hash__(self)
    def _oid_(self):
        return ObjectIdentifier([self])


### built-in ASN.1 types
class Integer32(int, SimpleSyntax):
    "INTEGER (-2147483648..2147483647)"
    _ber_tag = '\x02'
    ranges = Ranges(Range(-2147483648, 2147483647))
    def __new__(cls, val=0):
        return int.__new__(cls, val)
    def verify(self):
        return self.ranges.verify(self)
    def verify_ex(self):
        if not self.ranges.verify(self):
            raise ValueError, "value %s out of range for type %s" % (self, self.__class__.__name__)

    def _ber_(self):
        if self == 0:
            return self._ber_tag+"\x01\x00"
        arg = self
        i = 0
        raw = pack("!l", arg)
        while (arg & 0xff800000) in (0, 0xff800000):
            arg <<= 8
            i += 1
        result = raw[i:]
        return self._ber_tag + encode_length(len(result)) + result
        #return self._ber_tag + encode_length(len(raw)) + raw
    def _oid_(self):
        return ObjectIdentifier([self])
    def oid_decode(self, oid):
        return self.__class__(int(oid.pop(0)))
    def __add__(self, other):
        return self.__class__(int.__add__(self, other))
    def __sub__(self, other):
        return self.__class__(int.__sub__(self, other))
    def __mul__(self, other):
        return self.__class__(int.__mul__(self, other))
    def __div__(self, other):
        return self.__class__(int.__div__(self, other))
    def __int__(self):
        return self

INTEGER = Integer32

class Enumeration(INTEGER):
    enumerations = [] # list of possible values for a subclass
    def __str__(self):
        try:
            i = self.enumerations.index(self)
        except ValueError:
            name = "BADVALUE"
        else:
            name = str(self.enumerations[i])
        return "%s(%s)" % (name, int.__str__(self))
    def __repr__(self):
        return "%s.%s(%d)" % (self.__class__.__module__, self.__class__.__name__, self)
    def verify(self):
        return self in self.enumerations
    def verify_ex(self):
        if not self in self.enumerations:
            raise ValueError, "value %s out of range for type %s" % (self, self.__class__.__name__)


class OctetString(array, SimpleSyntax):
    "OCTET STRING (SIZE (0..65535))"
    _ber_tag = '\x04'
    ranges = Ranges(Range(0, 65535))
    def __new__(cls, v="", implied=False):
        return array.__new__(cls, 'c', "".join(v))
    def __init__(self, v="", implied=False):
        self.implied = bool(implied)
    def __getstate__(self):
        return (self.tostring(), self.implied)
    def __setstate__(self, st):
        self.fromstring(st[0])
        self.implied = st[1]
    def __iadd__(self, obj):
        self.fromstring(str(obj))
    def __str__(self):
        return self.tostring()
    def __int__(self): # some MIBs encode numbers as octet strings :-o
        val = 0
        l = len(self)
        for i, octet in enumerate(self):
            val += ord(octet)<<((l-i-1)*8)
        return val
    def verify(self):
        return self.ranges.verify(len(self))
    def verify_ex(self):
        if not self.ranges.verify(len(self)):
            raise OverflowError, "size (%s) out of range for type %s" % (len(self), self.__class__.__name__)
    def __repr__(self):
        return "%s.%s(%r)" % (self.__class__.__module__, self.__class__.__name__, "".join(self))
    def _ber_(self):
        return self._ber_tag + encode_length(len(self)) + self.tostring()
    def _oid_(self):
        if self.implied:
            l = []
        else:
            l = [len(self)]
        return ObjectIdentifier(l+map(ord, self))

    def oid_decode(self, oid):
        if not self.implied:
            length = oid.pop(0)
            rv = "".join(map(chr, oid[:length+1]))
            del oid[:length+1]
            return OctetString(rv)
        else:
            rv = "".join(map(chr, oid))
            del oid[:]
            return OctetString(rv)

OCTET_STRING = OctetString

class BITS(OctetString):
    """A collection of named bits."""
    enumerations = []

    def _extend(self, tooctet):
        for i in range(tooctet - len(self)+1):
            self.append("\0")

    def set(self, bit):
        if bit in self.enumerations:
            octet, obit = divmod(bit, 8)
            if octet >= len(self):
                self._extend(octet)
            self[octet] = chr(ord(self[octet]) | (128 >> obit))
        else:
            raise ValueError, "invalid bit for this syntax: %s" % (bit,)

    def clear(self, bit):
        octet, obit = divmod(bit, 8)
        if octet >= len(self):
            self._extend(octet)
        self[octet] = chr(ord(self[octet]) & ~(128 >> obit))

    def test(self, bit):
        octet, obit = divmod(bit, 8)
        if octet >= len(self):
            self._extend(octet)
        return bool(ord(self[octet]) & (128 >> obit))

    def __str__(self):
        s = []
        for enum in self.enumerations:
            if self.test(enum):
                s.append(str(enum))
        return "BITS(%s)" % (",".join(s),)

Bits = BITS

def bits_factory(basename, enums):
    bitclass = newclass("%sBITS" % (basename,), BITS, enumerations=enums)
    return bitclass()

class ObjectIdentifier(OID, SimpleSyntax):
    "OBJECT IDENTIFIER"
    _ber_tag = '\x06'
    def __init__(self, init=[], implied=False):
        self.implied = bool(implied)
        super(ObjectIdentifier, self).__init__(init)
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, list.__repr__(self))
    def _ber_(self):
        index = 0
        # skip leading empty oid
        while not self[index]:
            index += 1
        # build the first two
        if len(self) > index+1:
            result = self[index] * 40
            result += self[index+1]
            result = chr(result)
        else:
            result = ""
        index += 2
        for subid in self[index:]:
            # 7 bits long subid
            if subid >= 0 and subid < 128:
                result += '%c' % subid
            # 14 bits long subid
            elif subid >= 128 and subid < 16384:
                result += '%c%c' % (0x80 | (subid >> 7), subid & 0x7f)
            # 21 bits long subid
            elif subid >= 16384 and subid < 2097152:
                result += '%c%c%c' % (0x80 | ((subid >> 14) & 0x7f), \
                    0x80 | ((subid >> 7) & 0x7f), subid & 0x7f)
            # 28 bits long subid
            elif subid >= 2097152 and subid < 268435456:
                result += '%c%c%c%c' % (0x80 | ((subid>>21) & 0x7f), \
                    0x80 | ((subid >> 14) & 0x7f), 0x80 | ((subid >> 7) & 0x7f), \
                    subid & 0x7f)
            # 31 bits long subid
            elif subid >= 268435456L and subid < 2147483648L:
                result += '%c%c%c%c%c' % (0x80 | ((subid>>28) & 0x0f), \
                    0x80 | ((subid>>21) & 0x7f), 0x80 | ((subid >> 14) & 0x7f), \
                    0x80 | ((subid >> 7) & 0x7f), subid & 0x7f)
            # 32 bits long subid
            elif subid >= -2147483648L and subid < 0:
                result += '%c%c%c%c%c' % (0x80 | ((subid>>28) & 0x0f), \
                    0x80 | ((subid>>21) & 0x7f), 0x80 | ((subid >> 14) & 0x7f), \
                    0x80 | ((subid >> 7) & 0x7f), subid & 0x7f)
            else:
                raise BadOID, "problem with subid: %s" % (subid,)
        return self._ber_tag + encode_length(len(result)) + result

    def _oid_(self):
        if self.implied:
            l = []
        else:
            l = [len(self)]
        return ObjectIdentifier(l+self)

    def oid_decode(self, oid):
        if not self.implied:
            length = oid.pop(0)
            rv = oid[:length+1]
            del oid[:length+1]
            return ObjectIdentifier(rv)
        else:
            rv = oid[:]
            del oid[:]
            return ObjectIdentifier(rv)

    def get_object(self):
        """Returns the object class this OID refers to, or None if it is not imported."""
        oidmap = OIDMAP
        for i in range(len(self)+1, 4, -1):
            obj = oidmap.get(str(self[:i]), None)
            if obj:
                return obj
        return None

OBJECT_IDENTIFIER = ObjectIdentifier


### SNMP ApplicationSyntax types
class IpAddress(ipv4.IPv4, ApplicationSyntax):
    "IMPLICIT OCTET STRING (SIZE (4))"
    _ber_tag = '\x40'
    ranges = Ranges(Range(4, 4))
    def _ber_(self):
        result = pack("!l", self._address)
        return self._ber_tag + "\x04" + result
    def _oid_(self):
        return ObjectIdentifier( [(self._address >> 24) & 0x000000ff, 
                    ((self._address & 0x00ff0000) >> 16), 
                    ((self._address & 0x0000ff00) >> 8), 
                    (self._address & 0x000000ff)]  )
    def oid_decode(self, oid):
        assert len(oid) >= 4
        self._address = (oid[0]<<24) | (oid[1]<<16) | (oid[2]<<8) | oid[3]
        self._mask = 0xffffffff # XXX ?
        del oid[0:4]

def combine_ipaddress(addr_part, mask_part):
    """
combine_ipaddress(addr_part, mask_part) Helper function that takes two SNMP
IpAddress objects, the first containing the address, and the second that
contains a mask value in the "address" attribute (as returned by an SNMP get in
some tables).  """
    return IpAddress(addr_part.address, mask_part.address)

class Counter32(unsigned, _ImplicitUnsigned):
    "IMPLICIT INTEGER (0..4294967295)"
    _ber_tag = '\x41'
Counter = Counter32 # SNMPv1 name

class Gauge32(unsigned, _ImplicitUnsigned):
    "IMPLICIT INTEGER (0..4294967295)"
    _ber_tag = '\x42'

def get_gauge(val):
    """Return a Gauge32 constrained to the defined range."""
    if Gauge32.ranges.verify(val):
        return Gauge32(val)
    if val > Gauge32.ranges.max:
        return Gauge32(Gauge32.ranges.max)
    if val < Gauge32.ranges.min:
        return Gauge32(Gauge32.ranges.min)

Gauge = Gauge32 # SNMPv1 name

class Unsigned32(unsigned, _ImplicitUnsigned):
    "IMPLICIT INTEGER (0..4294967295)"
    _ber_tag = '\x42'

class TimeTicks(unsigned, _ImplicitUnsigned):
    "IMPLICIT INTEGER (0..4294967295)"
    _ber_tag = '\x43'

class Opaque(OctetString):
    "IMPLICIT OCTET STRING"
    _ber_tag = '\x44'
    def decode(self):
        from pycopia.SNMP import BER_decode
        tlv = BER_decode.get_tlv(self.tostring())
        return tlv.decode()

class Counter64(unsigned64, _ImplicitUnsigned):
    "IMPLICIT INTEGER (0..18446744073709551615)"
    _ber_tag = '\x46'
    ranges = Ranges(Range(0, 18446744073709551615L))

# values indicating errors
class _VarBindException(object):
    def __nonzero__(self):
        return 0
    def __repr__(self):
        return "%s()" % self.__class__.__name__
    def __str__(self):
        return self.__class__.__name__
    def __int__(self):
        return ord(self._ber_tag)
    def __long__(self):
        return long(ord(self._ber_tag))
    def _ber_(self):
        return self._ber_tag # XXX

class noSuchObject(_VarBindException):
    _ber_tag = '\x80'

class noSuchInstance(_VarBindException):
    _ber_tag = '\x81'

class endOfMibView(_VarBindException):
    _ber_tag = '\x82'


### SNMPv2-TC types. Hard coded here for added functionality.

class DisplayString(OctetString):
    format = "255a"
    ranges = Ranges(Range(0,255))

class PhysAddress(OctetString):
    format = "1x:"
    def __str__(self):
        return ":".join(map (lambda x: "%02x" % x, map(ord, self)))

class MacAddress(OctetString):
    format = "1x:"
    ranges = Ranges(Range(6, 6))
    def __str__(self):
        return ":".join(map (lambda x: "%02x" % x, map(ord, self)))

class TruthValue(Enumeration):
    enumerations = [Enum(1,"true"), Enum(2,"false")]

class TestAndIncr(Integer32):
    ranges = Ranges(Range(0, 2147483647))

class AutonomousType(ObjectIdentifier):
    """The identity of an item"""

class InstancePointer(ObjectIdentifier):
    pass

class VariablePointer(ObjectIdentifier):
    pass

class RowPointer(ObjectIdentifier):
    pass

class RowStatus(Enumeration):
    enumerations = [Enum(2,'notInService'), Enum(5,'createAndWait'), Enum(1,'active'), Enum(4,'createAndGo'), Enum(6,'destroy'), Enum(3,'notReady') ]
    def isActive(self):
        return self == 1
    def isNotInService(self):
        return self == 2
    def isNotReady(self):
        return self == 3

class TimeStamp(TimeTicks):
    pass

class TimeInterval(Integer32):
    ranges = Ranges(Range(minValue=0, maxValue=2147483647))

class DateAndTime(OctetString):
    format='2d-1d-1d,1d:1d:1d.1d,1a1d:1d'
    ranges = Ranges(Range(8,8), Range(11,11))
    #def __init__(self, string="\0\0\0\0\0\0\0\0"):
    def __str__(self):
        year = (ord(self[0]) << 8) + ord(self[1])
        if len(self) == 11:
            rv = "%4d-%d-%d,%d:%d:%d.%d,%s%d:%d" % (year, ord(self[2]), ord(self[3]), \
                    ord(self[4]), ord(self[5]), ord(self[6]), ord(self[7]), self[8], ord(self[9]), \
                    ord(self[10]))
        elif len(self) == 8:
            rv = "%4d-%d-%d,%d:%d:%d.%d" % (year, ord(self[2]), ord(self[3]), ord(self[4]), \
                ord(self[5]), ord(self[6]), ord(self[7]))
        else:
            rv = "DateAndTime: Incorrect value: %r" % self
        return rv

class StorageType(Enumeration):
    enumerations = [Enum(1, "other"), Enum(2, "volatile"),Enum(3, "nonVolatile"),Enum(4, "permanent"),Enum(5, "readOnly"),]

class TDomain(ObjectIdentifier):
    pass

class TAddress(OctetString):
    ranges = Ranges(Range(1,255))

# keep request IDs unique for all sessions
class _RequestId(Integer32):
    pass
_current_request_id = 0
def get_RequestId():
    global _current_request_id
    _current_request_id += 1
    return _RequestId(_current_request_id)

class VarBind(SequenceOf):
    def __init__(self, oid, value=None, Object=None):
        super(VarBind, self).__init__()
        self.append(oid)
        self.append(value)
        self.Object = Object # cached leaf class object from decoder.
    def clear(self):
        self[1] = None
        return self
    def __str__(self):
        if self.Object:
            return str(self.Object(self[1])) # an object initialized with the value
        else:
            return "(%s = %s)" % (self[0], self[1])
    def __repr__(self):
        return "%s.%s(%r, %r)" % (self.__class__.__module__, self.__class__.__name__, self[0], self[1])
    def get_value(self):
        return self[1]
    def set_value(self, value):
        self[1] = value
    def get_oid(self):
        return self[0]
    oid = property(get_oid)
    name = oid # alias
    value = property(get_value, set_value, clear)

class VarBindList(SequenceOf):
    def __str__(self):
        s = []
        for vb in self:
            s.append(str(vb))
        return "\n".join(s)

#### abstract base class for PDU objects
class _ImplicitPDU(object):
    def __init__(self, request_id=0, error_status=0, error_index=0, varbinds=None):
        self.request_id = request_id or get_RequestId()
        self.error_status = INTEGER(error_status)
        self.error_index = INTEGER(error_index)
        self.varbinds = varbinds or VarBindList()
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r, %r, %r)" % (cl.__module__, cl.__name__, self.request_id, \
                    self.error_status, self.error_index, self.varbinds)
    def _ber_(self):
        return _encode_pdu(self._ber_tag, self.request_id, self.error_status, 
                    self.error_index, self.varbinds)

    def add_varbind(self, varbind):
        self.varbinds.append(varbind)
    def add_oid(self, oid):
        self.varbinds.append(VarBind(oid))
    def get_varbinds(self):
        return self.varbinds
    # alias
    get_VarBindList = get_varbinds

# abstract base class for bulk PDU objects
class _BulkPDU(object):
    def __init__(self,  request_id=0, non_repeaters=0, max_repetitions=10, varbinds=None):
        self.request_id = request_id or get_RequestId()
        self.non_repeaters = non_repeaters  or INTEGER(0)
        self.max_repetitions = max_repetitions or INTEGER(0)
        self.varbinds = varbinds or VarBindList()
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r, %r, %r)" % (cl.__module__, cl.__name__, self.request_id, \
                    self.non_repeaters, self.max_repetitions, self.varbinds)
    def _ber_(self):
        return _encode_pdu(self._ber_tag, self.request_id, self.non_repeaters, 
                    self.max_repetitions, self.varbinds)
    def add_nonrepeater(self, oid):
        self.varbinds.insert(0, VarBind(ObjectIdentifier(oid)))
        self.non_repeaters += 1
    def add_repeater(self, oid):
        self.varbinds.append(VarBind(ObjectIdentifier(oid)))
    def set_repeater(self, oid):
        self.varbinds = VarBindList()
        self.varbinds.append(VarBind(ObjectIdentifier(oid)))
    def set_max_repetitions(self, val):
        self.max_repetitions =INTEGER(val)


### concrete PDUs from rfc1905
class GetRequestPDU(_ImplicitPDU):
    _ber_tag = '\xa0'

class GetNextRequestPDU(_ImplicitPDU):
    _ber_tag = '\xa1'

class ResponsePDU(_ImplicitPDU):
    _ber_tag = '\xa2'
    def __init__(self, request_id, error_status, error_index, varbinds):
        self.request_id = request_id
        self.error_status = error_status
        self.error_index = error_index
        self.varbinds = varbinds

class SetRequestPDU(_ImplicitPDU):
    _ber_tag = '\xa3'

class GetBulkRequestPDU(_BulkPDU):
    _ber_tag = '\xa5'

class InformRequestPDU(_ImplicitPDU):
    _ber_tag = '\xa6'

class SNMPv2TrapPDU(_ImplicitPDU):
    _ber_tag = '\xa7'

class ReportPDU(_ImplicitPDU):
    _ber_tag = '\xa8'

class SNMPv1TrapPDU(object):
    _ber_tag = '\xa4'
    def __init__(self, enterprise=None, agent=None, generic=None, specific=None, time_stamp=None, varbinds=None):
        self.enterprise = self._setdefault(enterprise, ObjectIdentifier)
        self.agent = self._setdefault(agent, IpAddress)
        self.generic = self._setdefault(generic, INTEGER)
        self.specific = self._setdefault(specific, INTEGER)
        self.time_stamp = self._setdefault(time_stamp, TimeTicks)
        self.varbinds = self._setdefault(varbinds, VarBindList)

    def _setdefault(self, param, obj):
        if param:
            return obj(param)
        else:
            return obj()

    def __repr__(self):
        return "%s(%s, %s, %s, %s, %s, %s)" % (self.__class__.__name__, repr(self.enterprise), \
                    repr(self.agent), repr(self.generic), repr(self.specific), \
                    repr(self.time_stamp), repr(self.varbinds))

# BER encoding helpers
def encode_length(l):
    if l < 0x80:
        return chr(l)
    elif l < 0xFF: # two bytes required
        return '\x81' + chr(l)
    else: # three bytes required
        return '\x82' + pack("!h", l)

def encode_length_long(l):
    return '\x82' + pack("!h", l)

def ber(obj):
    return obj._ber_()
#add2builtin("ber", ber)

def oid(obj):
    return obj._oid_()
#add2builtin("oid", oid)

def _encode_pdu(tag, *args):
    encodings = []
    for arg in args:
        if arg is None:
            encodings.append('\x05\0') # Null
        else:
            encodings.append(ber(arg))
    res = "".join(encodings)
    return tag + encode_length_long(len(res)) + res

def check_encoding(obj):
    from string import ascii_letters, digits
    """print a hex dump of the object's BER encoding (for debugging)."""
    def character(c):
        if c in ascii_letters:
            return "(%c)" % c
        elif c in digits:
            return "(%c)" % c
        else:
            return ""
    for i, e in enumerate(ber(obj)):
        print "%-3d: %s %s" % (i, hex(ord(e)), character(e) )


