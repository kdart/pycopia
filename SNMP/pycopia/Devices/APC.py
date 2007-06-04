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

"""
Device manager for the APC managed power.
Note that the APC uses SNMPv1.

"""


import sys

from pycopia import scheduler

from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager

from pycopia.mibs import SNMPv2_MIB
from pycopia.mibs import PowerNet_MIB

# for the Web/SNMP management module,
# only these scalars seem to work.

SCALARS = \
["mconfigBOOTPEnabled",
 "mconfigClockDate",
 "mconfigClockTime",
 "mconfigNumTrapReceivers",
 "mcontrolRestartAgent",
 "mfiletransferConfigFTPServerAddress",
 "mfiletransferConfigFTPServerPassword",
 "mfiletransferConfigFTPServerUser",
 "mfiletransferConfigSettingsFilename",
 "mfiletransferConfigTFTPServerAddress",
 "mfiletransferControlInitiateFileTransfer",
 "mfiletransferStatusLastTransferResult",
 "mtrapargsGauge",
 "mtrapargsInteger",
 "mtrapargsIpAddress",
 "mtrapargsString",
 "mtrapargsTimeTicks",
 "snmpEnableAuthenTraps",
 "snmpInASNParseErrs",
 "snmpInBadCommunityNames",
 "snmpInBadCommunityUses",
 "snmpInBadVersions",
 "snmpInPkts",
 "sysContact",
 "sysDescr",
 "sysLocation",
 "sysName",
 "sysObjectID",
 "sysServices",
 "sysUpTime",]


# working tables:
TABLES = \
["sPDUMasterConfigMSP",
 "sPDUOutletStatusMSP",
 "sPDUOutletConfigMSPmups",
 "sPDUOutletConfigMSPgs",
 "sPDUOutletControlMSP",
 "sPDUMasterStatusMSP",
 "sPDUMasterControlMSP",
 "sPDUIdentMSP",
 "mconfigTrapReceiver",
 "sPDUOutletConfigMSPall",
 "sPDUOutletConfigMSPannun"]


# main manager object
class APCManager(Manager.Manager):
    def get_outlet(self, outlet):
        outlet  = self.getall("OutletControlMSP", [1,1,outlet], cached=False)[0]
        return outlet

    def get_outlets(self):
        outlets  = self.getall("OutletControlMSP", cached=False)
        return OutletControls(outlets)

    def get_unit_report(self):
        t  = self.getall("MasterStatusMSP")[0]
        return APCReport(t.sPDUMasterStatusMSPName, t.sPDUMasterStatusMSPOutletCount)

    def get_outlet_report(self):
        t = self.getall("OutletConfigMSPall")
        return OutletConfigReport(t)


# reports
class APCReport(object):
    def __init__(self, name, outletcount):
        self.name = str(name)
        self.count = int(outletcount)
    def __str__(self):
        return "APC MasterSwitch Plus '%s' has %d outlets." % (self.name, self.count)

class OutletConfigReport(object):
    def __init__(self, entries):
        self._entries = []
        for entry in entries:
            self._entries.append((int(entry.sPDUOutletConfigMSPallOutletIndex),
                    str(entry.sPDUOutletConfigMSPallOutletName),
                    str(entry.sPDUOutletConfigMSPallOutletCtrlMode)))
        self._entries.sort()
    def __str__(self):
        s = ["Outlet Name               Mode"]
        s.extend(map(lambda t: "%-6.6s %-18.18s %s" % t, self._entries))
        return "\n".join(s)

class OutletControls(object):
    def __init__(self, entries):
        self._entries = entries
        self._entries.sort()

    def __str__(self):
        s = []
        for outlet in self._entries:
            s.append("%-6.6s %-18.18s %s" % (outlet.sPDUOutletControlMSPOutletIndex, 
                outlet.sPDUOutletControlMSPOutletName, 
                outlet.sPDUOutletControlMSPOutletCommand))
        s.insert(0, "Outlet Name               Status")
        return "\n".join(s)

    def get_outlet(self, num):
        return self._entries[num-1]


class OutletControlMSP(PowerNet_MIB.sPDUOutletControlMSPEntry):
    def _control(self, val):
        try:
            self.sPDUOutletControlMSPOutletCommand = val
        except:
            pass # agent does not respond to this
        scheduler.sleep(5)
        self.refresh()

    def __cmp__(self, other):
        return cmp(self.sPDUOutletControlMSPOutletIndex, other.sPDUOutletControlMSPOutletIndex)

    def immediate_on(self):
        """Setting this variable to immediateOnMSP (1) will immediately turn the outlet on.  """
        self._control(self._get_enums(0))
        assert self.sPDUOutletControlMSPOutletCommand == self._get_enums(0)

    def delayed_on(self):
        """Setting this variable to delayedOnMSP (2) will turn the outlet on
       after the sPDUOutletConfigMSPPowerOnDelay OID time has elapsed. """
        self._control( self._get_enums(1))

    def immediate_off(self):
        """Setting this variable to immediateOffMSP (3) will immediately turn the outlet off."""
        self._control( self._get_enums(2))
        assert self.sPDUOutletControlMSPOutletCommand == self._get_enums(2)

    def reboot(self):
        """Setting this variable to immediateRebootMSP (5) will immediately reboot the outlet."""
        self._control( self._get_enums(4))

    def shutdown(self):
        """Setting this variable to gracefulshutdownMSP (6) will cause the outlet to wait for
       device confirmation (if applicable) and then turn the outlet off after the
       sPDUOutletConfigMSPPowerOffDelay OID time has elapsed.  The outlet will then turn
       on after the sum of the sPDUOutletConfigMSPRestartTime OID time and the 
       sPDUOutletConfigMSPPowerOnDelay OID time has elapsed. """
        self._control( self._get_enums(5))

    def status(self):
        """Return the current state."""
        return self.sPDUOutletControlMSPOutletCommand

    def _get_enums(self, idx):
        return self.columns["sPDUOutletControlMSPOutletCommand"].enumerations[idx]

#   SNMP.Basetypes.Enumeration(1, 'immediateOnMSP'),
#   SNMP.Basetypes.Enumeration(2, 'delayedOnMSP'),
#   SNMP.Basetypes.Enumeration(3, 'immediateOffMSP'),
#   SNMP.Basetypes.Enumeration(4, 'gracefulRebootMSP'),
#   SNMP.Basetypes.Enumeration(5, 'immediateRebootMSP'),
#   SNMP.Basetypes.Enumeration(6, 'gracefulshutdownMSP'),
#   SNMP.Basetypes.Enumeration(7, 'overrideBatCapThreshMSP'),
#   SNMP.Basetypes.Enumeration(8, 'cancelPendingCommandMSP')


# remove ugly prefixes from names
def apc_mangler(oid_name):
    end = len(oid_name)
    start = 0
    if oid_name.endswith("Entry"): # also remove possible "...Entry" from tail.
        end = end - 5
    if oid_name.startswith("sPDU"):
        start = start + 4
    return oid_name[start:end]

# factory function
def get_manager(sessiondata):
    sessiondata.version = 0 # APC still only SNMPv1 !
    sess = SNMP.new_session(sessiondata)
    dev = APCManager(sess)
    dev.add_mibs([SNMPv2_MIB])
    dev.add_mib(PowerNet_MIB, apc_mangler, subclassmodule=sys.modules[__name__])
    return dev


