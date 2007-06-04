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
List system Object Requirements.

Usage:

    sysOR <agent> [<community>]

"""

import sys

from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB 


def main(argv):
    host = argv[1]
    sd = SNMP.sessionData(host)
    if len(argv) > 2:
        sd.add_community(argv[2])
    else:
        sd.add_community("public")
    sess = SNMP.new_session(sd)
    mgr = Manager.Manager(sess)
    mgr.add_mib(SNMPv2_MIB)
    ors = mgr.getall("sysOR")
    for ore in ors:
        print ore

main(sys.argv)
