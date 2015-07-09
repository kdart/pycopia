#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
