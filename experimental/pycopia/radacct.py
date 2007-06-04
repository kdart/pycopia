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

import re
import string
import exceptions

class RADException(Exception):
    """
    Exceptions that may be raised by this module
    """

class RADbadavpair(RADException):
    """
    Bad form for an AVpair entry. No '=' sign.
    """


# The base class for attribute value pairs
class AVpair(object):
    "The base class for RADIUS attribute-value pairs"
    def __init__(self, value):
        self.value=value
        self.verifier_re = "OOPS"   # should get this from child class
        self.typeclass = ""
        self.typenum = 0
        self.attrname = ""

    # Return the AVpair as a string
    def __repr__(self):
        return "%s = %s" % (self.attrname, self.value)

    # The verify method should return 0 (false) if the value is not considered
    # good, or 1 (true) if the value matches the testing RE.
    def verify(self):
        if re.match(self.verifier_re, self.value) == None:
            return 0
        else:
            return 1
        pass

    def printdebug(self):
        print "Attribute: [%d]%s (type %s)" % (self.typenum, self.attrname, self.typeclass)
        print "   verifier_re =", self.verifier_re 

# second level classes to facter out class attributes common to specific
# types.
class AVpair_integer(AVpair):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.typeclass = 'integer'
        self.verifier_re = "^[0-9]+$"


class AVpair_ipaddr(AVpair):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.typeclass = 'ipaddr'
        self.verifier_re = "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]$"


class AVpair_string(AVpair):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.typeclass = 'string'
        self.verifier_re = ".+"   # could contain anything, but should have something


class AVpair_enumerated(AVpair):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.typeclass = 'enumerated'
    

class AVpair_date(AVpair):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.typeclass = 'date'
        self.verifier_re = ".+"   # XXX Date format currently unknown

# Start of attribute specific classes

class User_Name(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 1 
        self.attrname = "User-Name"

class Password(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 2 
        self.attrname = "Password"

class CHAP_Password(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 3 
        self.attrname = "CHAP-Password"

class Client_Id(AVpair_ipaddr):
    def __init__(self, value):
        AVpair_ipaddr.__init__(self, value)
        self.value=value
        self.typenum = 4 
        self.attrname = "Client-Id"

class Client_Port_Id(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 5 
        self.attrname = 'Client-Port-Id'

class User_Service_Type(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 6 
        self.attrname = 'User-Service-Type'
        self.verifier_re = "Login-User|Framed-User|Dialback-Login-User|Dialback-Framed-User|Outbound-User|Shell-User|NAS-Prompt|Authenticate-only|Callback-NAS-prompt"
#   User Service Types
# VALUE     User-Service-Type   Login-User      1
# VALUE     User-Service-Type   Framed-User     2
# VALUE     User-Service-Type   Dialback-Login-User 3
# VALUE     User-Service-Type   Dialback-Framed-User    4
# VALUE     User-Service-Type   Outbound-User       5
# VALUE     User-Service-Type   Shell-User      6
# VALUE User-Service-Type NAS-Prompt 7
# VALUE User-Service-Type Authenticate-only 8
# VALUE User-Service-Type Callback-NAS-prompt 9

class Framed_Protocol(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 7 
        self.attrname = 'Framed-Protocol'
        self.verifier_re = "PPP|SLIP|ARAP|Gandalf|Xylogics"
#   Framed Protocols
# VALUE     Framed-Protocol     PPP         1
# VALUE     Framed-Protocol     SLIP            2
# VALUE Framed-Protocol ARAP 3
# VALUE Framed-Protocol Gandalf 4
# VALUE Framed-Protocol Xylogics 5

class Framed_Address(AVpair_ipaddr):
    def __init__(self, value):
        AVpair_ipaddr.__init__(self, value)
        self.value=value
        self.typenum = 8 
        self.attrname = 'Framed-Address'

class Framed_Netmask(AVpair_ipaddr):
    def __init__(self, value):
        AVpair_ipaddr.__init__(self, value)
        self.value=value
        self.typenum = 9 
        self.attrname = 'Framed-Netmask'

class Framed_Routing(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 10 
        self.attrname = 'Framed-Routing'
        self.verifier_re = "None|Broadcast|Listen|Broadcast-Listen"
#   Framed Routing Values
# VALUE     Framed-Routing      None            0
# VALUE     Framed-Routing      Broadcast       1
# VALUE     Framed-Routing      Listen          2
# VALUE     Framed-Routing      Broadcast-Listen    3

class Framed_Filter_Id(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 11 
        self.attrname = 'Framed-Filter-Id'

class Framed_MTU(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 12 
        self.attrname = 'Framed-MTU'

class Framed_Compression(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 13 
        self.attrname = 'Framed-Compression'
        self.verifier_re = "None|Van-Jacobsen-TCP-IP|IPX-header-compression"
#   Framed Compression Types
# VALUE     Framed-Compression  None            0
# VALUE     Framed-Compression  Van-Jacobsen-TCP-IP 1
# VALUE Framed-Compression IPX-header-compression 2

class Login_Host(AVpair_ipaddr):
    def __init__(self, value):
        AVpair_ipaddr.__init__(self, value)
        self.value=value
        self.typenum = 14 
        self.attrname = 'Login-Host'

class Login_Service(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 15 
        self.attrname = 'Login-Service'
        self.verifier_re = "Telnet|Rlogin|TCP-Clear|PortMaster|LAT"
#   Login Services
# VALUE     Login-Service       Telnet          0
# VALUE     Login-Service       Rlogin          1
# VALUE     Login-Service       TCP-Clear       2
# VALUE     Login-Service       PortMaster      3
# VALUE     Login-Service       LAT              4


class Login_TCP_Port(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 16 
        self.attrname = 'Login-TCP-Port'

class Old_Password(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 17 
        self.attrname = 'Old-Password'

class Port_Message(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 18 
        self.attrname = 'Port-Message'

class Dialback_No(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 19 
        self.attrname = 'Dialback-No'

class Dialback_Name(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 20 
        self.attrname = 'Dialback-Name'

class Expiration(AVpair_date):
    def __init__(self, value):
        AVpair_date.__init__(self, value)
        self.value=value
        self.typenum = 21 
        self.attrname = 'Expiration'

class Framed_Route(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 22 
        self.attrname = 'Framed-Route'

class Framed_IPX_Network(AVpair_ipaddr):
    def __init__(self, value):
        AVpair_ipaddr.__init__(self, value)
        self.value=value
        self.typenum = 23 
        self.attrname = 'Framed-IPX-Network'

class Challenge_State(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 24 
        self.attrname = 'Challenge-State'

class Challenge_Class(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 25
        self.attrname = 'Challenge-Class'

class Vendor_Specific(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 26 
        self.attrname = 'Vendor-Specific'

class Session_Timeout(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 27 
        self.attrname = 'Session-Timeout'

class Idle_Timeout(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 28 
        self.attrname = 'Idle-Timeout'

class Termination_Action(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value = value
        self.typenum = 29 
        self.attrname = 'Termination-Action'
        self.verifier_re = "Default|RADIUS-Request"
# Actions to be taken on service termination
# VALUE Termination-Action Default 0
# VALUE Termination-Action RADIUS-Request 1

class Called_Station_Id(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.typenum = 30 
        self.attrname = 'Called-Station-Id'

class Calling_Station_Id(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value=value
        self.verifier_re = ".*"   # something or nothing here. Azita says no problem.
        self.typenum = 31 
        self.attrname = 'Calling-Station-Id'

class NAS_Identifier(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 32 
        self.attrname = 'NAS-Identifier'

class Proxy_State(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 33 
        self.attrname = 'Proxy-State'

class Login_LAT_Service(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 34 
        self.attrname = 'Login-LAT-Service'

class Login_LAT_Node(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 35 
        self.attrname = 'Login-LAT-Node'

class Login_LAT_Group(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 36 
        self.attrname = 'Login-LAT-Group'

class Framed_AppleTalk_Link(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 37 
        self.attrname = 'Framed-AppleTalk-Link'

class Framed_AppleTalk_Network(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 38 
        self.attrname = 'Framed-AppleTalk-Network'

class Framed_AppleTalk_Zone(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 39 
        self.attrname = 'Framed-AppleTalk-Zone'

class Acct_Status_Type(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 40 
        self.attrname = 'Acct-Status-Type'
        self.verifier_re = "Start|Stop|Interim-Update|Accounting-On|Accounting-Off"
#   Status Types
# VALUE     Acct-Status-Type    Start           1
# VALUE     Acct-Status-Type    Stop            2
# VALUE     Acct-Status-Type    Update          3
# VALUE     Acct-Status-Type    Accounting-On 3
# VALUE     Acct-Status-Type    Accounting-Off 4


class Acct_Delay_Time(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 41 
        self.attrname = 'Acct-Delay-Time'

class Acct_Input_Octets(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 42 
        self.attrname = 'Acct-Input-Octets'

class Acct_Output_Octets(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 43 
        self.attrname = 'Acct-Output-Octets'


class Acct_Session_Id(AVpair_integer):
    def __init__(self, value):
        AVpair.__init__(self, value)
        self.value=value
        self.typenum = 44 
        self.typeclass = 'integer'
        self.attrname = 'Acct-Session-Id'
        
class Acct_Authentic(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value=value
        self.typenum = 45 
        self.attrname = 'Acct-Authentic'
        self.verifier_re = "None|RADIUS|Local"
#   Authentication Types
# VALUE     Acct-Authentic      None            0
# VALUE     Acct-Authentic      RADIUS          1
# VALUE     Acct-Authentic      Local           2


class Acct_Session_Time(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 46 
        self.attrname = 'Acct-Session-Time'

class Acct_Input_Packets(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 47 
        self.attrname = 'Acct-Input-Packets'

class Acct_Output_Packets(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 48 
        self.attrname = 'Acct-Output-Packets'

class Acct_Terminate_Cause(AVpair_enumerated):
    def __init__(self, value):
        AVpair_enumerated.__init__(self, value)
        self.value = value
        self.typenum = 49 
        self.attrname = 'Acct-Terminate-Cause'
        self.verifier_re = "User-Request|Lost-Carrier|Lost-Service|Idle-Timeout|Session-Timeout|Admin-Reset|Admin-Reboot|Port-Error|NAS-Error|NAS-Request|NAS-Reboot|Port-Unneeded|Port-Preempted|Port-Suspended|Service-Unavailable|Callback|User-Error|Host-Request"
# Termination causes
# VALUE Acct-Terminate-Cause User-Request 1
# VALUE Acct-Terminate-Cause Lost-Carrier 2
# VALUE Acct-Terminate-Cause Lost-Service 3
# VALUE Acct-Terminate-Cause Idle-Timeout 4
# VALUE Acct-Terminate-Cause Session-Timeout 5
# VALUE Acct-Terminate-Cause Admin-Reset 6
# VALUE Acct-Terminate-Cause Admin-Reboot 7
# VALUE Acct-Terminate-Cause Port-Error 8
# VALUE Acct-Terminate-Cause NAS-Error 9
# VALUE Acct-Terminate-Cause NAS-Request 10
# VALUE Acct-Terminate-Cause NAS-Reboot 11
# VALUE Acct-Terminate-Cause Port-Unneeded 12
# VALUE Acct-Terminate-Cause Port-Preempted 13
# VALUE Acct-Terminate-Cause Port-Suspended 14
# VALUE Acct-Terminate-Cause Service-Unavailable 15
# VALUE Acct-Terminate-Cause Callback 16
# VALUE Acct-Terminate-Cause User-Error 17
# VALUE Acct-Terminate-Cause Host-Request 18



class Acct_Multi_Session_Id(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 50 
        self.attrname = 'Acct-Multi-Session-Id'

class Acct_Link_Count(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 51 
        self.attrname = 'Acct-Link-Count'

class CHAP_Challenge(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 60 
        self.attrname = 'CHAP-Challenge'

class NAS_Port_Type(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value=value
        self.typenum = 61 
        self.attrname = 'NAS-Port-Type'

class Port_Limit(AVpair_integer):
    def __init__(self, value):
        AVpair_integer.__init__(self, value)
        self.value = value
        self.typenum = 62 
        self.attrname = 'Port-Limit'

class Login_LAT_Port(AVpair_string):
    def __init__(self, value):
        AVpair_string.__init__(self, value)
        self.value = value
        self.typenum = 63 
        self.attrname = 'Login-LAT-Port'


# some useful global functions

def extract_avpair(avline):
    avlist = string.split(avline, "=", 1)
    if len(avlist) == 2:
        Attribute = string.strip(avlist[0])
        Value = string.strip(avlist[1])
        if Value[0] == "\"" and Value[-1] == "\"":
            Value = Value[1:-1]
        return (Attribute, Value)
    else:
        raise RADbadavpair()
