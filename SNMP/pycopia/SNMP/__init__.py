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
Pure Python SNMP module. This implementation supports SNMPv1 and SNMPv2c.

Example usage:

# 1. Create a sessionData instance with appropriate settings for the
# device.
sd = SNMP.sessionData("172.20.149.40")
sd.add_community("public", SNMP.RO)
sd.add_community("private", SNMP.RW)

# 2. Create a new SNMP session
session = SNMP.new_session(sd)

# 3. You may now use the session directly using its get and set methods,
# but it's easier to use the Manager object as it allows MIB access by
# name.
box = SNMP.Util.Manager(session)

# 4. tell the Manager what MIBs this device supports
box.add_mibs("SNMPv2_MIB", "UDP_MIB")

# 5. now do stuff with the device!
print "System Name       :", box.sysName
print "System Uptime     :", box.sysUpTime
 
"""

__all__ = ["Basetypes", "Manager", "Agent", "Objects"]


# base exception class
class NMSException(Exception):
    def getname(self):
        return self.__class__.__name__
    def getvalue(self):
        return self.__class__.value

class SNMPException(NMSException):
    value = -1
    
# SNMP module specific exceptions
class SNMPBadParameters(SNMPException):
    value = 0

class SNMPBadArgument(SNMPException):
    value = 1

class SNMPNotConnected(SNMPException):
    value = 2

class SNMPNoResponse(SNMPException):
    value = 3

class SNMPBadVersion(SNMPException):
    value = 4

class SNMPBadCommunity(SNMPException):
    value = 5

class SNMPBadRequestID(SNMPException):
    value = 6

class SNMPEmptyResponse(SNMPException):
    value = 7

class SNMPIllegalArgument(SNMPException):
    value = 8

class SNMPNotImplemented(SNMPException):
    value = 9


class BERError(NMSException):
    value = -1

# BER module specific exceptions
class BERUnknownTag(BERError):
    value = 9

class BERBadEncoding(BERError):
    value = 10

class BERBadSubjid(BERError):
    value = 11

class BERBadIPAddress(BERError):
    value = 12

class BERTypeError(BERError):
    value = 13

class BERBadArgument(BERError):
    value = 14


# Abstract base class for SNMP protocol errors
class SNMPError(SNMPException):
    value = -1
    def __str__(self):
        return _SNMP_ERROR_STRINGS[self.__class__.value] 

class SNMPnoError(SNMPError):
    value = 0

class SNMPtooBig(SNMPError):
    value = 1

class SNMPnoSuchName(SNMPError):
    value = 2

class SNMPbadValue(SNMPError):
    value = 3

class SNMPreadOnly(SNMPError):
    value = 4

class SNMPgenError(SNMPError):
    value = 5

class SNMPnoAccess(SNMPError):
    value = 6

class SNMPwrongType(SNMPError):
    value = 7

class SNMPwrongLength(SNMPError):
    value = 8

class SNMPwrongEncoding(SNMPError):
    value = 9

class SNMPwrongValue(SNMPError):
    value = 10

class SNMPnoCreation(SNMPError):
    value = 11

class SNMPinconsistentValue(SNMPError):
    value = 12

class SNMPresourceUnavailable(SNMPError):
    value = 13

class SNMPcommitFailed(SNMPError):
    value = 14

class SNMPundoFailed(SNMPError):
    value = 15

class SNMPauthorizationError(SNMPError):
    value = 16

class SNMPnotWritable(SNMPError):
    value = 17

class SNMPinconsistentName(SNMPError):
    value = 18


# SNMP error exceptions (taken from UCD SNMP code)
_SNMP_ERROR_STRINGS = {
    0: '(noError) No Error',
    1: '(tooBig) Response message would have been too large.',
    2: '(noSuchName) There is no such variable name in this MIB.',
    3: '(badValue) The value given has the wrong type or length.',
    4: '(readOnly) The two parties used do not have access to use the specified SNMP PDU.',
    5: '(genError) A general failure occured.',
    6: '(noAccess) Access denied.',
    7: '(wrongType) Wrong BER type',
    8: '(wrongLength) Wrong BER length.',
    9: '(wrongEncoding) Wrong BER encoding.',
    10: '(wrongValue) Wrong value.',
    11: '(noCreation) ',
    12: '(inconsistentValue) ',
    13: '(resourceUnavailable) ',
    14: '(commitFailed) ',
    15: '(undoFailed) ',
    16: '(authorizationError) ',
    17: '(notWritable) ',
    18: '(inconsistentName) '
}

