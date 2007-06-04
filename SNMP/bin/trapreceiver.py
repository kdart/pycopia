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
Simple trap reciever that prints traps to stdout.

"""

import sys

from pycopia import scheduler
from pycopia import asyncio
from pycopia import interactive

from pycopia.SNMP import traps

trap = None


def _handler(timestamp, ip, community, pdu):
    global trap
    tr = traps.TrapRecord(timestamp, ip, community, pdu)
    trap = tr
    print tr
    print

def load(mibname):
    exec "import mibs.%s" % (mibname,) in globals(), globals()


# sets up trap reciever and goes into interactive mode. 
# note that this only works when the Python readline module is the one from
# pyNMS.
def main(argv):
    for mibname in argv[1:]:
        load(mibname)
    traps.start_straps()
    scheduler.sleep(2)
    trapreceiver = traps.TrapDispatcher(_handler)
    asyncio.register(trapreceiver)

main(sys.argv)
# exits into interactive mode...

