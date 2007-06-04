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


"""

import unittest

from pycopia.SMI import SMI

class SMITests(unittest.TestCase):
    def setUp(self):
        SMI.load_modules("SNMPv2-SMI", "SNMPv2-TC", "SNMPv2-MIB", "UDP-MIB", "TCP-MIB")
        mods = list(SMI.get_modules())
        self.mod = mods[-1]

    def test_get_modules(self):
        """Get all loaded modules and print first one."""
        print self.mod

    def test_get_scalars(self):
        print "getScalars test"
        scalars = list(self.mod.get_scalars())
        scalar = scalars[1]
        print scalar

    def test_get_rows(self):
        print "getRows test"
        rows = list(self.mod.get_rows(SMI.SMI_STATUS_CURRENT))
        print rows[0]

    def test_types(self):
        print " types test:"
        tcmib = SMI.get_module("SNMPv2-TC")
        smi_types = tcmib.get_types()
        for smi_type in smi_types:
            print "Type: ", smi_type, smi_type.snmptype

    def test_index(self):
        print "index test: get an Index object of a row"
        rtpmib = SMI.get_module("RTP-MIB")
        rtpsess = rtpmib.get_node("rtpSessionInverseEntry")
        rtpsess_index = rtpsess.get_index()
        for ind in rtpsess_index:
            print rtpmib.get_node(ind.name).value

    def test_augments(self):
        print "augments test: should see base conceptual row index."
        snmpmib = SMI.get_module("SNMP-COMMUNITY-MIB")

        taenode = snmpmib.get_node("snmpTargetAddrExtEntry") # base row with implied index
        taenode_index = taenode.get_index()
        print repr(taenode_index)

        comm = snmpmib.get_node("snmpCommunityEntry") # augmented row
        comm_index = comm.get_index()
        print repr(comm_index)

        newoid = comm.OID
        print newoid

    def test_ipmib(self):
        ipmod = SMI.get_module("IP-MIB")
        eslist = ipmod.get_scalars()
        for es in eslist:
            print es.name, es.syntax
        n = ipmod.get_node("ipForwarding")
        print n.syntax.enumerations


if __name__ == '__main__':
    unittest.main()
