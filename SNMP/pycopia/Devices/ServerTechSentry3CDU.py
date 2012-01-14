#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab:fenc=utf-8
#
#    Copyright (C) 2012 Keith Dart <keith@dartworks.biz>
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
Manager for ServerTechnology Sentry 3 CDU/PDU devices.

"""


from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

import sys

from pycopia import scheduler

#from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB
from pycopia.mibs import Sentry3_MIB




# main manager object
class Sentry3Manager(Manager.Manager):
    def get_outlet(self, tower, outlet):
        outlet = self.getall("outlet", [tower,1,outlet])[0]
        return outlet

    def get_outlet_by_id(self, ID):
        outlets = self.get_outlets()
        o = outlets.get_outlet(ID)
        o.set_session(self.session)
        return o

    def get_outlets_by_ids(self, idlist):
        rv = []
        outlets = self.get_outlets()
        for ID in idlist:
            rv.append(outlets.get_outlet(ID))
        return rv

    def get_outlets(self):
        return OutletControls(self.getall("outlet"))

    def reboot(self, outletID):
        outlet = self.get_outlet_by_id(outletID)
        outlet.reboot()

    def get_outlet_report(self):
        t = self.getall("outlet")
        return OutletConfigReport(t)



class OutletControls(object):
    def __init__(self, entries):
        newent = {}
        for entry in entries.values():
            newent[str(entry.outletID)] = entry
        self._entries = newent

    def __str__(self):
        s = []
        for outlet in self._entries.values():
            s.append("%-6.6s %-18.18s %s" % (outlet.outletID, outlet.outletName, outlet.outletStatus))
        s.insert(0, "Outlet Name               Status")
        return "\n".join(s)

    def get_outlet(self, ID):
        return self._entries[ID]


class OutletConfigReport(object):
    def __init__(self, entries):
        self._entries = []
        for entry in entries:
            self._entries.append((str(entry.outletID),
                    str(entry.outletName),
                    str(entry.outletControlState)))
        self._entries.sort()

    def __str__(self):
        s = ["Outlet Name               Mode"]
        s.extend(map(lambda t: "%-6.6s %-18.18s %s" % t, self._entries))
        return "\n".join(s)


class outlet(Sentry3_MIB.outletEntry):

    def _control(self, val):
        try:
            self.outletControlAction = val
        except:
            pass # agent does not respond to this
        scheduler.sleep(5)
        self.refresh()

    def __cmp__(self, other):
        return cmp(self.outletControlAction, other.outletControlAction)

    def immediate_on(self):
        """Setting this variable to on (1) will immediately turn the outlet on.  """
        self._control(self._get_enums(1))
        assert self.outletControlAction == self._get_enums(1)

    def immediate_off(self):
        """Setting this variable to off (2) will immediately turn the outlet off."""
        self._control( self._get_enums(2))
        assert self.outletControlAction == self._get_enums(2)

    def reboot(self):
        """Setting this variable to reboot (3) will immediately reboot the outlet."""
        self._control( self._get_enums(3))

    def status(self):
        """Return the current state."""
        return self.outletControlAction

    def _get_enums(self, idx):
        return self.columns["outletControlAction"].enumerations[idx]



def get_manager(device, community):
    mgr = Manager.get_manager(device, community, Sentry3Manager)
    mgr.add_mib(SNMPv2_MIB)
    mgr.add_mib(Sentry3_MIB, subclassmodule=sys.modules[__name__])
    return mgr

def _test(argv):
    device = argv[1]
    community = "Private" if len(argv) < 2 else argv[2]
    mgr = Manager.get_manager(device, community)
    print(mgr.get_outlets())

if __name__ == "__main__":
    _test(sys.argv)

