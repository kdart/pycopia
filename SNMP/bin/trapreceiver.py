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
Simple trap reciever that prints traps to stdout.

"""

import sys

from pycopia import module
from pycopia import asyncio
from pycopia import interactive # sets up nicer CLI

from pycopia.SNMP import traps

trap = None


def _handler(traprecord):
    global trap
    trap = traprecord
    print trap
    print

def load(mibname):
    module.Import("pycopia.mibs.%s" % (mibname.replace("-", "_"),))
    return "OK"


# Sets up trap receiver that goes into interactive mode.
# note that this only works when the Python readline module is the one from
# pycopia, or Python later than 2.5.
def main(argv):
    for mibname in argv[1:]:
        load(mibname)
    traps.get_dispatcher(_handler)
    asyncio.start_sigio()

main(sys.argv)
# exits into interactive mode...
print "Entering interactive mode."
print "SNMP traps will be displayed as they arrive. "
print "Load new MIBS with the 'load' function."
print "The last trap is available in the 'trap' object."

