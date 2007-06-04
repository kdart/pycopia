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

from pycopia.aid import Enum

_FLAGS = { 
    'UNIVERSAL': 0x00,
    'APPLICATION' : 0x40,
    'CONTEXT' : 0x80,
    'PRIVATE' : 0xC0,
    # extended tags
    'PRIMITIVE': 0x00,
    'CONSTRUCTOR' : 0x20
}

# universal BER tags
FALSE                   = Enum(0, 'FALSE')
TRUE                    = Enum(0xFF, 'TRUE')
INTEGER                 = Enum(0x02, 'INTEGER')
OCTETSTRING             = Enum(0x04, 'OCTET_STRING')
NULL                    = Enum(0x05, 'NULL')
OBJID                   = Enum(0x06, 'ObjectIdentifier')
#not defined by SNMP
SEQUENCE                = Enum(0x10, 'SEQUENCE')
BOOLEAN                 = Enum(0x01, 'BOOLEAN')
BITSTRING               = Enum(0x03, 'BITSTRING')
SET                     = Enum(0x11, 'SET')
#SNMPv2specifictags
IPADDRESS               = Enum(0x00|_FLAGS['APPLICATION'], 'IPAddress')
COUNTER32               = Enum(0x01|_FLAGS['APPLICATION'], 'Counter32')
GAUGE32                 = Enum(0x02|_FLAGS['APPLICATION'], 'Gauge32')
UNSIGNED32              = Enum(0x02|_FLAGS['APPLICATION'], 'Unsigned32')
TIMETICKS               = Enum(0x03|_FLAGS['APPLICATION'], 'TimeTickS')
OPAQUE                  = Enum(0x04|_FLAGS['APPLICATION'], 'Opaque')
NSAPADDRESS             = Enum(0x05|_FLAGS['APPLICATION'], 'NsapAddress')
COUNTER64               = Enum(0x06|_FLAGS['APPLICATION'], 'Counter64')
#SNMP PDU specifics
GETREQUEST              = Enum(0x00|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'GetRequest-PDU')
GETNEXTREQUEST          = Enum(0x01|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'GetNextRequest-PDU')
GETRESPONSE             = Enum(0x02|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'Response-PDU')
SETREQUEST              = Enum(0x03|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'SetRequest-PDU')
TRAPREQUEST             = Enum(0x04|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'Trap-PDU') # obsolete
GETBULKREQUEST          = Enum(0x05|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'GetBulkRequest-PDU')
INFORMREQUEST           = Enum(0x06|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'InformRequest-PDU')
SNMPV2TRAP              = Enum(0x07|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'SNMPv2-Trap-PDU')
REPORT                  = Enum(0x08|_FLAGS['CONTEXT']|_FLAGS['CONSTRUCTOR'], 'Report-PDU')
TAGGEDSEQUENCE          = Enum(0x10|_FLAGS['CONSTRUCTOR'], 'TAGGEDSEQUENCE')

# SNMPv2 errorvalues
NOSUCHOBJECT            = Enum(0x00|_FLAGS['CONTEXT'], 'noSuchObject')
NOSUCHINSTANCE          = Enum(0x01|_FLAGS['CONTEXT'], 'noSuchInstance')
ENDOFMIBVIEW            = Enum(0x02|_FLAGS['CONTEXT'], 'endOfMibView')



if __name__ == "__main__":
    import sys
    from pycopia.aid import str2hex
    print "%20s | %6s | %6.6s | %s" % ("Token name", "intval", "hexstr", "Enum name")
    print "--------------------------------------------------------------------------"
    for _tn in dir(sys.modules[__name__]):
        if _tn.startswith("_"):
            continue
        val = getattr(sys.modules[__name__], _tn)
        if type(val) is Enum:
            print "%20s | %6d | %6.6s | %s" % (_tn, val, str2hex(chr(val)), val)

