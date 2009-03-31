#!/usr/bin/python2
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2009 Keith Dart <keith@kdart.com>
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
Defines an interactive command line that wraps an SMTP session.
"""

import os

from pycopia import getopt
from pycopia import CLI
from pycopia import aid
from pycopia.SNMP import SNMP
from pycopia.SNMP import Manager
from pycopia.mibs import SNMPv2_MIB, IF_MIB

from pycopia.SMI import OIDMAP


class SNMPManagerCommands(CLI.GenericCLI):

    def mib(self, argv):
        """mib [add] <modulename>
    Add a MIB module to the known set. You must add a mib module before
    it's attributes can be accessed by this command session.  """
        if argv[1] in ("add", "load"):
            del argv[1]
        mibs = [get_mib(name) for name in argv[1:]]
        self._obj.add_mibs(mibs)

    def show(self, argv):
        """show [scalars | tables | notifications | all <tablename>]
    If not arguments given then display basic system information.
    Otherwise show information about the specified item."""
        if len(argv) < 2:
            self._print(self._obj.sysDescr)
            self._print(self._obj.sysName)
            self._print(get_oidname(self._obj.sysObjectID))
            self._print(self._obj.sysLocation)
            self._print(self._obj.sysContact)
        else:
            item = argv[1]
            if item.startswith("scal"):
                self._ui.print_list(self._obj.get_scalar_names())
            elif item.startswith("tab"):
                self._ui.print_list(self._obj.get_table_names())
            elif item.startswith("not"):
                self._ui.print_list(self._obj.get_notification_names())
            elif item.startswith("sysor"):
                for sysor_entry in self._obj.getall("sysOR"):
                    self._print(sysor_entry.sysORDescr)
                    try:
                        self._print(get_oidname(sysor_entry.sysORID))
                    except AttributeError:
                        pass # XXX I think this is a bug workaround
                    self._print("\n")
            elif item.startswith("all"):
                for row in self._obj.getall(argv[2]):
                    self._print(row)

    def getall(self, argv):
        """getall <tablename>
    Display all rows of the given table."""
        tname = argv[1]
        for row in self._obj.getall(tname):
            self._print(row)


def get_mib(name):
    name = name.replace("-", "_")
    if not name.endswith("_MIB"):
        name += "_MIB"
    return aid.Import("pycopia.mibs." + name)


def get_oidname(soid):
    soid = str(soid)
    obj = OIDMAP.get(soid)
    if obj is None:
        return soid
    else:
        return obj.__name__

def get_manager(device, community):
    sd = SNMP.sessionData(device, version=1)
    sd.add_community(community, SNMP.RW)
    sess = SNMP.new_session(sd)
    dev = Manager.Manager(sess)
    dev.add_mibs([SNMPv2_MIB, IF_MIB])
    return dev


def snmpcli(argv):
    """snmpcli [-h] [-p <port>] [-s <scriptname>] host community

Provides an interactive session to an SNMP agent.
    """
    port = 161
    sourcefile = None
    logfile = None
    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "hl:p:s:")
    except getopt.GetoptError:
            print snmpcli.__doc__
            return
    for opt, val in optlist:
        if opt == "-s":
            sourcefile = val
        elif opt == "-l":
            logfile = val
        elif opt == "-h":
            print snmpcli.__doc__
            return
        elif opt == "-p":
            try:
                port = int(val)
            except ValueError:
                print snmpcli.__doc__
                return

    if not args:
        print snmpcli.__doc__
        return

    host = args[0]
    if len(args) > 1:
        community = args[1]
    else:
        community = "public"

    manager = get_manager(host, community)

    parser = CLI.get_generic_cli(manager, SNMPManagerCommands, logfile=logfile, 
            historyfile=os.path.expandvars("$HOME/.hist_snmpcli"))

    if sourcefile:
        try:
            parser.parse(sourcefile)
        except CLI.CommandQuit:
            pass
    else:
        parser.interact()

if __name__ == "__main__":
    import sys
    snmpcli(sys.argv)

