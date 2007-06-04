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

import sys
import select # XXX Fix this to use asyncio
#import asyncio # XXX

from pycopia import socket 
from pycopia.aid import Enum 
from pycopia.SMI.Basetypes import *

from pycopia.SNMP import (
        SNMPnoError,
        SNMPtooBig,
        SNMPnoSuchName,
        SNMPbadValue,
        SNMPreadOnly,
        SNMPgenError,
        SNMPnoAccess,
        SNMPwrongType,
        SNMPwrongLength,
        SNMPwrongEncoding,
        SNMPwrongValue,
        SNMPnoCreation,
        SNMPinconsistentValue,
        SNMPresourceUnavailable,
        SNMPcommitFailed,
        SNMPundoFailed,
        SNMPauthorizationError,
        SNMPnotWritable,
        SNMPinconsistentName,
        )
from pycopia.SNMP import BER_decode

# used to map SNMP error responses to exceptions
EXCEPTION_MAP = {
    0: SNMPnoError,
    1: SNMPtooBig,
    2: SNMPnoSuchName,
    3: SNMPbadValue,
    4: SNMPreadOnly,
    5: SNMPgenError,
    6: SNMPnoAccess,
    7: SNMPwrongType,
    8: SNMPwrongLength,
    9: SNMPwrongEncoding,
    10: SNMPwrongValue,
    11: SNMPnoCreation,
    12: SNMPinconsistentValue,
    13: SNMPresourceUnavailable,
    14: SNMPcommitFailed,
    15: SNMPundoFailed,
    16: SNMPauthorizationError,
    17: SNMPnotWritable,
    18: SNMPinconsistentName
}

# access permission enumerations
RO = Enum(0, "RO")
RW = Enum(1, "RW")

class CommunityName(object):
    def __init__(self, name, access=RO):
        self.name = name
        self.access = access
    def __repr__(self):
        return "%s(name=%s, access=%s)" % (self.__class__.__name__, 
                        self.name, self.access)

class CommunitySet(list):
    def add_community(self, community, access=RO):
        self.append(CommunityName(community, access))
    def add_RO(self, community):
        self.append(CommunityName(community, RO))
    def add_RW(self, community):
        self.append(CommunityName(community, RW))
    def get_by_access(self, access_enum):
        for c in self:
            if c.access == access_enum:
                return c.name
        return None
    def get_RO(self):
        return self.get_by_access(RO)
    def get_RW(self):
        return self.get_by_access(RW)


# A sessionData instance holds all the parameters for an SNMP session.
# Make (instantiate) one of these and supply it to a session object.
# Usually that would be done with the new_session() factory function.
# This object holds information for all types of SNMP administrative
# framworks. Use what you need. The new_session() function figures out
# what framework to use based on what is contained in this object.
# However, only community based is currently implemented. So, just add
# community names to this object to use community based framework. 
class sessionData(object):
    def __init__(self, agent=None, communities=None, retries=3, timeout=10, polltime=20, 
            port=161, version=1, user=None, context=None):
        self.communities = CommunitySet(communities or CommunitySet())
        self.default_community = None
        self.agent = agent
        self.retries = retries
        self.timeout = float(timeout)
        self.polltime = polltime
        # version actually  = 0 for SNMPv1 and 1 for SNMPv2
        self.version = Integer32(version)
        self.port = port
        self.user = user
        self.context = context
    def __str__(self):
        s = []
        s.append("Agent:         %s" % self.agent)
        s.append("Communities:   %s" % self.communities)
        s.append("SNMP retries:  %d" % self.retries)
        s.append("SNMP timeout:  %f" % self.timeout)
        s.append("SNMP polltime: %d" % self.polltime)
        s.append("SNMP port:     %d" % self.port)
        s.append("SNMP version:  %d" % self.version)
        s.append("SNMP user:     %s" % self.user)
        s.append("SNMP context:  %s" % self.context)
        return "\n".join(s)
    def add_community(self, cname, access=RO):
        self.communities.add_community(cname, access)
    def add_community_RW(self, cname):
        self.communities.add_community(cname, RW)
        self.default_community = cname
    def del_community(self, cname):
        self.communities.del_community(cname)
    def get_community(self, access):
        return self.communities.get_by_access(access)
    def get_community_RO(self):
        return self.communities.get_by_access(RO)
    def get_community_RW(self):
        return self.communities.get_by_access(RW)
    def new_communities(self, cset):
        if not isinstance(cset, communitySet):
            raise ValueError, "new_communities: must pass in communitySet instance"
        self.communities = cset
    def set_default_community(self, access):
        self.default_community = self.communities.get_by_access(access)
    def get_default_community(self):
        if self.default_community is None:
            return intern("public")
        else:
            return self.default_community


max_bindings = INTEGER(2147483647)


## Abstract base class for SNMP messages
class Message(object):
    pass

# community based message, SNMPv2c
class CommunityBasedMessage(Message):
    def __init__(self, community='public', pdu=None, version=1):
        self.version = Integer32(version)
        self.community = OctetString(community)
        self.pdu = pdu
    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.community, \
                    self.pdu, self.version )
    
    def _ber_(self):
        return ber(SequenceOf([self.version, self.community, self.pdu]))
    
    def set_pdu(self, pdu):
        if isinstance(pdu, _ImplicitPDU) or isinstance(pdu, _BulkPDU):
            self.pdu = pdu
        else:
            raise ValueError, "Given PDU must be a PDU type."

    def set_community(self, community_string):
        self.community = OctetString(community_string)

    def add_varbind(self, varbind):
        self.pdu.add_varbind(varbind)

    def add_oid(self, oid, value=None):
        self.pdu.add_varbind(VarBind(ObjectIdentifier(oid), value))

    def get_varbinds(self):
        return self.pdu.get_varbinds()
    get_VarBindList = get_varbinds


## User based message (SNMPv2u) - NOT IMPLEMENTED
class UserBasedMessage(Message):
    pass

# these session objects deal with OIDs, and hide authentication and message handling.
class Session(object):
    # init the session
    def __init__ (self, sessiondata=None):
        self.sessiondata = sessiondata
        self.socket = None
        self._OUTSTANDING = {}
        if self.sessiondata:
            self.open()

    def open(self, sessiondata=None):
        """create a UDP socket to SNMP agent"""
        if isinstance(sessiondata, sessionData):
            self.sessiondata = sessiondata
        if self.sessiondata:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#           self.socket = SNMPDispatcher(self._receiver)
            self.socket.connect((self.sessiondata.agent, self.sessiondata.port))

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.sessiondata))

    def __del__(self):
        if self.socket:
            self.socket.close()

    def _receiver(self):
        pass # XXX

    def _receive(self):
        """receive a response from SNMP agent"""
        # initialize sockets map
        r, w, x = [self.socket], [], []
        r, w, x = select.select(r, w, x, self.sessiondata.timeout)
        if r:
            return self.socket.recv(4096)
        # return nothing on timeout
        return None

    # send request and receive a reply
    def _send_and_receive(self, msgobj):
        if not self.socket:
            raise SNMPNotConnected, "Not connected."
        sent_request_id = msgobj.pdu.request_id
        self._OUTSTANDING[sent_request_id] = msgobj
        msg = ber(msgobj)
        if not msg:
            raise SNMPBadParameters, "No message"
        retries = 0
        # send request till response or retry counter hits the limit
        while retries < self.sessiondata.retries:
            # send a request
            self.socket.sendall(msg)
            # wait for response
            while True:
                response = self._receive()
                if response:
                    resp = self._decode_message(response)
                    orig = self._OUTSTANDING.pop(resp.pdu.request_id, None) 
                    if orig is None:
                        print >>sys.stderr, "warning: got strange response (ID %s)" % (resp.pdu.request_id,)
                        continue
                    else:
                        if resp.pdu.request_id == sent_request_id:
                            return resp
                        else:
                            print >>sys.stderr, "warning: This is not the response we are looking for (ID %s)" % (resp.pdu.request_id,)
                            continue
                            #raise SNMPBadRequestID, "SNMP response has wrong ID: should be %s, is %s" % (sent_request_id, resp.pdu.request_id)
                # otherwise, try it again
                break
            retries += 1
        # no answer
        raise SNMPNoResponse, "No resonse from agent after %d tries." % (retries,)

    def close(self):
        """close UDP socket to SNMP agent"""
        if self.socket:
            self.socket.close()
            self.socket = None  

    # note theses get_table implementations are simplified. They always get the whole table.
    def get_table(self, rowobj, insert_cb):
        if self.sessiondata.version >= 1:
            return self.get_table_with_bulk(rowobj, insert_cb)
        else:
            return self.get_table_with_getnext(rowobj.OID, insert_cb)

    def get_table_with_getnext(self, rowoid, insert_cb):
        prefixlen = len(rowoid)
        fetchoid = rowoid
        while True:
            try:
                varbinds = self.getnext(fetchoid)
            except SNMPError, e:
                if varbinds:
                    for vb in varbinds:
                        if vb.name[:prefixlen] == rowoid:
                            insert_cb(vb)
                return
            if varbinds:
                for vb in varbinds:
                    if vb.name[:prefixlen] != rowoid:
                        return
                    else:
                        insert_cb(vb)
                fetchoid = varbinds[-1].name
            else:
                return

    def get_table_with_bulk(self, rowobj, insert_cb):
        rowoid = rowobj.OID
        bpdu = GetBulkRequestPDU()
        bpdu.add_repeater(rowoid)
        bpdu.set_max_repetitions(25)
        prefixlen = len(rowoid)
        gblist = None
        while True:
#           try:
            gblist = self.getbulk(bpdu)
#           except SNMPError, e:
#               if gblist:
#                   for vb in gblist:
#                       if vb.name[:prefixlen] == rowoid:
#                           insert_cb(vb)
#               return
            if gblist:
                for vb in gblist:
                    if vb.name[:prefixlen] != rowoid:
                        return
                    elif isinstance(vb.value, endOfMibView):
                        return
                    else:
                        insert_cb(vb)
                bpdu.set_repeater(gblist[-1].name)
            else:
                return
            gblist = None

    def get_table_row(self, index, col_oids):
        oids = []
        for oid in col_oids:
            oids.append(oid+index)
        return self.get(oids)


    # override these in a subclass implementing security framework
    def set(self, *args):
        raise NotImplementedError

    def get(self, *args):
        raise NotImplementedError

    def getnext(self, *args):
        raise NotImplementedError

    def getbulk(self, *args):
        raise NotImplementedError

    def inform(self, *args):
        raise NotImplementedError



# community based session handler. (SNMPv2c)
class CommunityBasedSession(Session):
    def _decode_message(self, message):
        tlv = BER_decode.get_tlv(message)
        version, community, pdu = tlv.decode()
        return CommunityBasedMessage(community, pdu, version)

    def _get_request_message(self):
        comm = self.sessiondata.get_community(RO)
        if not comm: # then try to use a RW community if no RO community
            comm = self.sessiondata.get_community(RW)
            if not comm:
                raise SNMPBadCommunity, "No community strings!"
        return CommunityBasedMessage(comm, GetRequestPDU(), self.sessiondata.version )

    def get_varbindlist(self, vbl):
        try:
            mo = self._get_request_message()
            map(mo.add_varbind, vbl)
            rv = self._send_mo(mo)
        except SNMPtooBig: # ack, agent reports response would be too big
            return self._get_varbindlist_big(vbl)
        else:
            return rv
    
    # a nifty double-recursion halving algorithm
    def _get_varbindlist_big(self, vbl):
        middle = len(vbl)/2
        bot = self.get_varbindlist(vbl[:middle])
        top = self.get_varbindlist(vbl[middle:])
        return bot + top

    def get(self, *oids):
        mo = self._get_request_message()
        for oid in oids:
            mo.add_oid(oid)
        return self._send_mo(mo)

    def _send_mo(self, mo):
        resp = self._send_and_receive(mo)
        if resp.pdu.error_status:
            raise EXCEPTION_MAP[resp.pdu.error_status], resp.pdu.error_index
        else:
            return resp.pdu.varbinds

    def set(self, varbindlist):
        """
set(varbindlist)
Where varbindlist is a VarBindList containing VarBind objects.

        """
        comm = self.sessiondata.get_community(RW)
        if not comm:
            raise SNMPBadCommunity, "No community!"
        mo = CommunityBasedMessage(comm, SetRequestPDU() , self.sessiondata.version )
        map(mo.add_varbind, varbindlist)
        resp = self._send_and_receive(mo)
        if resp.pdu.error_status:
            raise EXCEPTION_MAP[resp.pdu.error_status], resp.pdu.error_index
        else:
            return resp.pdu.varbinds

    def set_varbind(self, varbind):
        vbl = VarBindList()
        vbl.append(varbind)
        return self.set(vbl)
    
    def getnext(self, *oids):
        comm = self.sessiondata.get_community(RO)
        if not comm: # then try to use a RW community if no RO community
            comm = self.sessiondata.get_community(RW)
            if not comm:
                raise SNMPBadCommunity, "No community!"
        mo = CommunityBasedMessage(comm, GetNextRequestPDU(), self.sessiondata.version  )
        for oid in oids:
            mo.add_oid(oid)
        resp = self._send_and_receive(mo)
        if resp.pdu.error_status:
            raise EXCEPTION_MAP[resp.pdu.error_status], resp.pdu.error_index
        else:
            return resp.pdu.varbinds
    
    # The getbulk method has a different interface. Pass in a
    # GetBulkRequestPDU instance instead of OIDs. This gives the user a
    # chance to set the repeaters and nonrepeaters. This module has
    # no way of knowing what those will be.
    def getbulk(self, bulkpdu):
        comm = self.sessiondata.get_community(RO)
        if not comm: # then try to use a RW community if no RO community
            comm = self.sessiondata.get_community(RW)
            if not comm:
                raise SNMPBadCommunity, "No community!"
        mo = CommunityBasedMessage(comm, bulkpdu, self.sessiondata.version  )
        resp = self._send_and_receive(mo)
        if resp.pdu.error_status:
            raise EXCEPTION_MAP[resp.pdu.error_status], resp.pdu.error_index
        else:
            return resp.pdu.varbinds
    
    def inform(self, varbindlist):
        raise NotImplementedError


### User based administrative framework session
class UserBasedSession(Session):
    def __init__(self, sessiondata):
        raise NotImplementedError


### View based administrative framework session
class ViewBasedSession(Session):
    def __init__(self, sessiondata):
        raise NotImplementedError


### use these factory functions
def new_session(sessiondata):
    # Use a heuristic to figure out what kind of administrative framework to
    # use.
    # If we have communities, assume community based session.
    if sessiondata.communities:
        return CommunityBasedSession(sessiondata)
    # if we have user, assume user based
    elif sessiondata.user:
        return UserBasedSession(sessiondata)
    else:
        raise ValueError, "new_session: cannot determine Administrative Framework. Are communities set?"

# simplified method of getting an SNMPv2c or v1 session. 
def get_session(host, readcommunity, writecommunity=None, version=1):
    sd = sessionData(host, version=version)
    sd.add_community(readcommunity, RO)
    if writecommunity:
        sd.add_community(writecommunity, RW)
    return new_session(sd)


