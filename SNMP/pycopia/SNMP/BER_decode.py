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

import sys
from struct import pack, unpack

from pycopia.aid import str2hex
from pycopia.SMI import Basetypes
from pycopia.SMI import OIDMAP

from pycopia.SNMP import BER_tags

# BER decoders

class TLV(object):
    def __init__(self, tag, length, value, lol):
        self.tag = tag
        self.length = length
        self.value = value
        self.lol = lol # length of length - needed for sequence decoding - kludgy
    def __str__(self):
        return "<TLV: tag='%s', length=%d, value='%s'>" % (str2hex(self.tag), self.length, str2hex(self.value))
    def __repr__(self):
        return "%s(0x%x, %r, %r)" % (self.__class__.__name__, self.tag, self.length, self.value)
    def decode(self):
        try:
            return DECODE_METHODS[self.tag](self.length, self.value)
        except KeyError:
            raise BERUnknownTag, "TLV.decode: tag %r is unknown" % (str2hex(self.tag),)

def get_tlv(message):
    if len(message) > 1:
        tag = message[0]
        length, inc = _decode_message_length(message)
        value = message[inc:length+inc]
        return TLV(tag, length, value, inc)
    else:
        raise BERBadArgument, "ber.get_tlv: message too small"

def _decode_message_length(message):
    # message[0] is the tag
    fb = ord(message[1])
    msb = fb & 0x80
    if not msb:
        return fb & 0x7F, 2
    # else otet is length of length value
    size = fb & 0x7F
    return unpack("!l", ("\x00\x00\x00\x00" + message[2:size+2])[-4:])[0], size+2


# A SEQUENCE is implicitly a list
def decode_sequence(length, message):
    assert length == len(message)
    sequence = []
    index = 0
    if length:
        while index < length:
            newtlv = get_tlv(message[index:])
            index = index + newtlv.length + newtlv.lol
            sequence.append(newtlv.decode())
    return sequence

def decode_boolean(length, message):
    return Basetypes.Boolean(ord(message[0]))

# this decodes any basic integer type, and returns a long to handle
# unsigned types. 
def _decode_an_integer(length, message):
    if ord(message[0]) & 0x80:
        val = -1
    else:
        val = 0
    for c in message:
        val = val << 8 | ord(c)
    return val

def _decode_an_unsigned(length, message):
    val = 0L
    for i in xrange(length):
        val = (val << 8) + ord(message[i])
    return val 

def decode_integer(length, message):
    return Basetypes.Integer32(_decode_an_integer(length, message))

def decode_string(length, message):
    assert length == len(message)
    return Basetypes.OctetString(message)

def decode_opaque(length, message):
    assert length == len(message)
    return Basetypes.Opaque(message)

def decode_null(length, message):
    return None

def decode_exception(length, message):
    return None

def decode_nosuchobject(length, message):
    return Basetypes.noSuchObject()
    
def decode_nosuchinstance(length, message):
    return Basetypes.noSuchInstance()
    
def decode_endofmibview(length, message):
    return Basetypes.endOfMibView()
    

def decode_oid(length, message):
    """decode ASN.1 object ID"""
    oid = []
    # get the first subid
    subid = ord(message[0])
    oid.append(subid / 40)
    oid.append(subid % 40)

    index = 1
    # loop through the rest
    while index < length:
        # get a subid
        subid = ord(message[index])
        if subid < 128:
            oid.append(subid)
            index = index + 1
        else:
            # construct subid from a number of octets
            next = subid
            subid = 0
            while next >= 128:
                # collect subid
                subid = (subid << 7) + (next & 0x7F)
                # take next octet
                index = index + 1
                next = ord(message[index])
                # just for sure
                if index > length:
                    return bad_integer
            # append a subid to oid list
            subid = (subid << 7) + next
            oid.append(subid)
            index = index + 1
    # return objid
    return Basetypes.OBJECT_IDENTIFIER(oid)

def decode_ipv4(length, message):
    """decode ASN.1 IP address"""
    assert length == 4
    address = (ord(message[0])<<24) + (ord(message[1])<<16) + \
                    (ord(message[2])<<8) + ord(message[3])
    return Basetypes.IpAddress(address)

def decode_counter32(length, message):
    return Basetypes.Counter32(_decode_an_unsigned(length, message))
    
def decode_gauge32(length, message):
    return Basetypes.Gauge32(_decode_an_unsigned(length, message))

def decode_timeticks(length, message):
    return Basetypes.TimeTicks(_decode_an_unsigned(length, message))

def decode_counter64(length, message):
    return Basetypes.Counter64(_decode_an_unsigned(length, message))

def decode_unsigned32(length, message):
    return Basetypes.Unsigned32(_decode_an_unsigned(length, message))

# PDU decoders

def _find_object(oid):
    oidmap = OIDMAP
    for i in range(len(oid), 6, -1):
        obj = oidmap.get(str(oid[:i]), None)
        if obj:
            return obj
    return None

def _decode_a_varbindlist(vbl_tuple):
    vbl = Basetypes.VarBindList()
    for [oid, value] in vbl_tuple:
        obj = _find_object(oid)
        if obj is not None:
            if value is not None:
                if obj.syntaxobject:
                    value = obj.syntaxobject(value)
                if obj.enumerations:
                    value.enumerations = obj.enumerations
            vbl.append(Basetypes.VarBind(oid, value, obj))
        else: # unknown varbind, deal with it later
            vbl.append(Basetypes.VarBind(oid, value))
    return vbl

def _decode_a_pdu(pdu_object, length, message):
    rawpdu = decode_sequence(length, message)
    assert len(rawpdu) == 4
    return pdu_object(rawpdu[0], rawpdu[1], rawpdu[2], _decode_a_varbindlist(rawpdu[3]))

def decode_getrequest(length, message):
    return _decode_a_pdu(Basetypes.GetRequestPDU, length, message)

def decode_getnextrequest(length, message):
    return _decode_a_pdu(Basetypes.GetNextRequestPDU, length, message)

def decode_response(length, message):
    return _decode_a_pdu(Basetypes.ResponsePDU, length, message)

def decode_setrequest(length, message):
    return _decode_a_pdu(Basetypes.SetRequestPDU, length, message)

def decode_traprequest(length, message):
    return _decode_a_pdu(Basetypes.SNMPv2TrapPDU, length, message)

def decode_getbulkrequest(length, message):
    return _decode_a_pdu(Basetypes.GetBulkRequestPDU, length, message)

def decode_informrequest(length, message):
    return _decode_a_pdu(Basetypes.InformRequestPDU, length, message)

def decode_v1traprequest(length, message):
    rawpdu = decode_sequence(length, message)
    assert len(rawpdu) == 6
    return Basetypes.SNMPv1TrapPDU(rawpdu[0], rawpdu[1], rawpdu[2], rawpdu[3], rawpdu[4], _decode_a_varbindlist(rawpdu[5]))


DECODE_METHODS = {}
DECODE_METHODS[chr(BER_tags.BOOLEAN)] = decode_boolean
DECODE_METHODS[chr(BER_tags.INTEGER)] = decode_integer
DECODE_METHODS[chr(BER_tags.BITSTRING)] = NotImplemented
DECODE_METHODS[chr(BER_tags.OCTETSTRING)] = decode_string
DECODE_METHODS[chr(BER_tags.NULL)] = decode_null
DECODE_METHODS[chr(BER_tags.OBJID)] = decode_oid
DECODE_METHODS[chr(BER_tags.SEQUENCE)] = NotImplemented
DECODE_METHODS[chr(BER_tags.SET)] = NotImplemented
DECODE_METHODS[chr(BER_tags.IPADDRESS)] = decode_ipv4
DECODE_METHODS[chr(BER_tags.COUNTER32)] = decode_counter32
DECODE_METHODS[chr(BER_tags.GAUGE32)] = decode_gauge32
DECODE_METHODS[chr(BER_tags.TIMETICKS)] = decode_timeticks
DECODE_METHODS[chr(BER_tags.OPAQUE)] = decode_opaque
DECODE_METHODS[chr(BER_tags.NSAPADDRESS)] = NotImplemented
DECODE_METHODS[chr(BER_tags.COUNTER64)] = decode_counter64
DECODE_METHODS[chr(BER_tags.UNSIGNED32)] = decode_unsigned32
DECODE_METHODS[chr(BER_tags.TAGGEDSEQUENCE)] = decode_sequence
DECODE_METHODS[chr(BER_tags.GETREQUEST)] = decode_getrequest
DECODE_METHODS[chr(BER_tags.GETNEXTREQUEST)] = decode_getnextrequest
DECODE_METHODS[chr(BER_tags.GETRESPONSE)] = decode_response
DECODE_METHODS[chr(BER_tags.SETREQUEST)] = decode_setrequest
DECODE_METHODS[chr(BER_tags.TRAPREQUEST)] = decode_v1traprequest
DECODE_METHODS[chr(BER_tags.GETBULKREQUEST)] = decode_getbulkrequest
DECODE_METHODS[chr(BER_tags.INFORMREQUEST)] = decode_informrequest
DECODE_METHODS[chr(BER_tags.SNMPV2TRAP)] = decode_traprequest
DECODE_METHODS[chr(BER_tags.NOSUCHOBJECT)] = decode_nosuchobject
DECODE_METHODS[chr(BER_tags.NOSUCHINSTANCE)] = decode_nosuchinstance
DECODE_METHODS[chr(BER_tags.ENDOFMIBVIEW)] = decode_endofmibview

