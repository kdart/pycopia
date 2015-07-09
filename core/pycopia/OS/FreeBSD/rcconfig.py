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
Woohoo! the FreeBSD /etc/rc.conf file is directly parseable by Python!
Use that to get interface and other configuration information from the
box running tests.

"""

import sys, os
import config
import netobjects
import socketlib

RCCONF = "/etc/rc.conf"

def _get_name(addr):
    try:
        return socketlib.gethostbyaddr(str(addr))[0]
    except:
        return ""

def _get_rcfile(devname=None):
    if devname is None or str(devname) == socketlib.getfqdn(): # myself
        rcfile = RCCONF
    else:
        rcfile = os.path.join(os.environ["PYNMS_HOME"], "etc", "rc_conf.d", str(devname).replace(".", "_") )
    if os.path.isfile(rcfile):
        return rcfile
    else:
        print >>sys.stderr, "rcconfig: I don't see the file %s" % (rcfile,)
        return None

class RcConfFile(config.ConfigHolder):
    pass

def get_rcconf(devname=None):
    rcconf = _get_rcfile(devname)
    if rcconf is None:
        return None
    rc = RcConfFile()
    rc["interfaces"] = ifc = config.SECTION("interfaces")
    tempspace = {}
    tempsubs = {}
    execfile(rcconf, tempspace, tempspace)
    del tempspace["__builtins__"] # execfile puts this here
    for key, value in tempspace.items():
        if key == "interfaces":
            continue # just in case, don't clobber our interfaces name
        if key.startswith("ifconfig"):
            parts = key.split("_")
            if len(parts) == 2: # main interface
                [inet, addr, netmask, themask] = value.split()
                ifc[parts[1]] = netobjects.Interface(parts[1], addr, themask, _get_name(addr))
            elif len(parts) == 3: # alias - alas, can be out of order
                [inet, addr, netmask, themask] = value.split()
                alias = int(parts[2][5:]) # chop alias word
                intf = ifc.get(parts[1], None)
                if intf:
                    intf.add_subinterface(alias, addr, themask, _get_name(addr))
                else: # have not seen main interface yet, so save it in a temporary list
                    subint = netobjects.Interface(alias, addr, themask, _get_name(addr))
                    try:
                        tempsubs[parts[1]].append(subint)
                    except KeyError:
                        tempsubs[parts[1]] = [subint]
            else:
                print "rconfig warning: bad ifconfig line:", key, "=", value
        else:
            rc[key] = value
    # now, put in the saved aliases
    for name, subintlist in tempsubs.items():
        for subint in subintlist:
            ifc[name].set_subinterface(subint)
    return rc

if __name__ == "__main__":
    import os
    rc = get_rcconf("qa19.qa")
    print rc


