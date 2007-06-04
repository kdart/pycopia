#!/usr/bin/python3.4
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
SNMP trap dispatcher. This uses the straps program as a simple proxy to allow
non-root programs and scripts to receive traps.
See straps(8) for details on how this works.

"""



import struct
from pycopia import socket
from pycopia.timelib import now

from pycopia.SNMP import BER_decode
from pycopia.SNMP.SNMP import SNMPv2TrapPDU, TimeTicks, ObjectIdentifier, IpAddress

from pycopia.mibs.SNMPv2_MIB import (sysUpTime, snmpTrapOID, snmpTrapEnterprise,
                            coldStart, warmStart, authenticationFailure)

from pycopia.mibs.IF_MIB import linkDown, linkUp
from pycopia.mibs.SNMP_COMMUNITY_MIB import snmpTrapAddress, snmpTrapCommunity

# egpNeighborLoss not in mibs! So fake it here. This should occur only
# rarely, anyway...
class _egpNeighborLoss(object):
    status = 1
    OID = ObjectIdentifier([1,3,6,1,6,3,1,1,5,6]) 
    def __init__(self, value=None):
        self.value=value


# translate SNMPv1 generic trap ID to SNMPv2 object
_TRAPMAP = {
    0: coldStart.OID,
    1: warmStart.OID,
    2: linkDown.OID,
    3: linkUp.OID,
    4: authenticationFailure.OID,
    6: _egpNeighborLoss.OID,
}

def _translate2v2(ip, community, pdu):
    """Translate an SNMPv1 trap to an SNMPv2 trap per RFC2576. This is
    done so that the rest of the API only has to deal with V2 traps.
    """
    varbinds = pdu.varbinds
    # 3.1.(1)
    varbinds.insert(0, sysUpTime(pdu.time_stamp).varbind)
    # 3.1.(2)
    if pdu.generic == 6:  # enterpriseSpecific(6)
        trapoid = ObjectIdentifier(pdu.enterprise+[0, pdu.specific])
    else: # 3.1.(3)
        trapoid = _TRAPMAP[pdu.generic]
    varbinds.insert(1, snmpTrapOID(trapoid).varbind)
    # 3.1.(4)
    varbinds.append(snmpTrapAddress(ip).varbind)
    varbinds.append(snmpTrapCommunity(community).varbind)
    varbinds.append(snmpTrapEnterprise(pdu.enterprise).varbind)
    return SNMPv2TrapPDU(varbinds=varbinds)


# all trap callbacks should match this signature.
def _default_trap_handler(timestamp, ip, community, pdu):
    tr = TrapRecord(timestamp, ip, community, pdu)
    print tr


class TrapRecord(object):
    """Holder for SNMP Traps.
    """
    def __init__(self, timestamp, ip, community, pdu):
        self.timestamp = timestamp
        self.ip = ip
        self.community = community
        self.pdu = pdu

    def __str__(self):
        pdu = self.pdu
        trapoid = pdu.varbinds[1]
        s = ["Trap from %s with ID %s for %s at %s:" % (self.ip, pdu.request_id, 
                                self.community, self.timestamp)]
        s.append("  Uptime: %s" % (pdu.varbinds[0],))
        obj = trapoid.value.get_object()
        if obj:
            s.append("  Trap OID: %s (%s)" % (trapoid, obj.__name__))
        else:
            s.append("  Trap OID: %s" % (trapoid,))
        for vb in pdu.varbinds[2:]:
            if vb.Object:
                s.append("    %s (%s) = %s" % (vb.oid, vb.Object.__name__, vb.value))
            else:
                s.append("    %s = %s" % (vb.oid, vb.value))
        return "\n".join(s)

    def __repr__(self):
        return "TrapRecord(%r, %r, %r, %r)" % (self.timestamp, self.ip, self.community, self.pdu)


class TrapDispatcher(socket.AsyncSocket):
    def __init__(self, traphandler=_default_trap_handler, port=162, debug=False):
        super(TrapDispatcher, self).__init__(socket.AF_UNIX, socket.SOCK_STREAM)
        self.traphandler = traphandler # should be a callable object
        if type(traphandler) is list:
            self._handlers = traphandler
        else:
            self._handlers = [traphandler]
        self._debug = debug
        self.connect("/tmp/.straps-%d" % port)

    def _get_debug(self):
        return self._debug
    def _set_debug(self, val):
        self._debug = bool(val)
    def _del_debug(self):
        self._debug = False
    debug = property(_get_debug, _set_debug, _del_debug)

    def register_handler(self, handler):
        if callable(handler):
            self._handlers.append(handler)

    def readable(self):
        return True

    def writable(self):
        return False

    def handle_read(self):
        ip = struct.unpack("!I", self.recv(4))[0] # network byte-order
        port = struct.unpack("!H", self.recv(2))[0] # network byte-order
        length = struct.unpack("i", self.recv(4))[0] # host byte-order
        src = IpAddress(ip)
        src.port = port
        msg = self.recv(length)
        assert length == len(msg)
        tlv = BER_decode.get_tlv(msg) # should be community based message
        version, community, pdu = tlv.decode()
        if version == 0:
            pdu = _translate2v2(ip, community, pdu)
        arglist = (now(), src, community, pdu)
        for handler in self._handlers:
            # handler returns False/None if other handlers may run,
            # returns True if handled, and no further processing required.
            if handler(*arglist):
                break
    
    def handle_connect(self):
        pass

    def handle_error(self, ex, val, tb):
        if self._debug:
            from pycopia import debugger
            debugger.post_mortem(ex, val, tb)
        else:
            import traceback
            traceback.print_exception(ex, val, tb)

def start_straps(port=162):
    # the daemonize and straps program source code is in the pycopia-utils
    # package.
    import os
    if port != 162:
        cmd = "daemonize -f /tmp/straps.log straps %d" % port
    else:
        cmd = "daemonize -f /tmp/straps.log straps"
    rv =  os.system(cmd)
    return rv

def get_dispatcher(*handlers):
    """Return a TrapDispatcher instance ready to respond to traps.
    """
    from pycopia import scheduler
    from pycopia import asyncio
    start_straps()
    scheduler.sleep(2)
    dispatcher = TrapDispatcher(list(handlers))
    asyncio.register(dispatcher)
    return dispatcher


if __name__ == "__main__":
    from pycopia import asyncio
    get_dispatcher([_default_trap_handler])
    while True:
        asyncio.pause()


