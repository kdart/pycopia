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
Use nsupdate to update a DNS server (running Bind version 9.x).

"""

import sys, os
from pycopia import proctools

NSUPDATE = proctools.which("nsupdate")

class _DNSUpdate(proctools.ProcessPipe):
    def __init__(self, cmd, logfile=None,  env=None, callback=None, merge=0, async=False):
        proctools.ProcessPipe.__init__(self, cmd, logfile,  env, callback, merge, async)
        self._zone=None
        self._dnsclass = "IN" # default class
        self._ttl = 86400 # default ttl

    def close(self):
        self.write(chr(4)) # ^D
        super(_DNSUpdate, self).close()

    def _readerr_fill(self):
        try:
            c = self._readerr(1024)
            if not c:
                return
            print >>sys.stderr, "nsupdate ERROR: %s" % (c)
        except (IOError, EOFError):
            ex, val, tb = sys.exc_info()
            print >>sys.stderr, "*** Error:", ex, val

    def _send_command(self, line):
        self.write(line)
        self.write("\n")

    def send(self):
        """Sends the current message."""
        self.write("\n\n")

    def server(self, servername, port=53):
        """server servername [ port ]
              Sends all dynamic update requests to the name server servername.
              When no server statement is provided, nsupdate will send updates
              to  the  master  server of the correct zone.  """
        self._send_command("server %s %d" % (servername, port))

    def local(self, address, port=None):
        """local address [ port ]
              Sends all dynamic update requests using the local address."""
        self._send_command("local %s %d" % (address, port))

    def zone(self, zonename):
        """zone zonename
              Specifies that all updates are to be made to the zone zonename.
              If no zone statement is provided, nsupdate will attempt  deter-
              mine  the correct zone to update based on the rest of the input."""
        self._zone = zonename
        self._send_command("zone %s" % self._zone)

    def key(self, name, secret):
        """key name secret
              Specifies that all updates are to be TSIG signed using the  key-
              name  keysecret  pair. """
        return self._send_command("key %s %s" % (name, secret))

    def prereq(self, ptype, *args):
        return self._send_command("prereq %s %s" % (ptype, " ".join(map(str, args))))

    def update(self, op, *args):
        return self._send_command("update %s %s" % (op, " ".join(map(str, args))))

    def show(self):
        return self.readline() # XXX

    def ttl(self, newttl=None):
        if newttl is None:
            return self._ttl
        else:
            self._ttl = int(newttl)

    def add(self, domainname, dnstype, data, ttl=None, dnsclass=None):
        """add domain-name ttl [ class ]  type data...
              Adds  a  new  resource  record with the specified ttl, class and
              data.
        """
        return self.update("add", domainname, ttl or self._ttl, dnsclass or self._dnsclass, dnstype, data)

    def delete(self, domainname, dnsclass="", dnstype="", data=""):
        """delete domain-name [ ttl ]  [ class ]  [ type  [ data... ]  ]
              Deletes  any  resource  records  named domain-name.  If type and
              data  is  provided,  only  matching  resource  records  will  be
              removed.   The  internet  class  is assumed if class is not sup-
              plied. The ttl is ignored, and is only allowed  for  compatibil-
              ity.  """
        return self.update("delete", domainname, dnsclass, dnstype, data)

    # helpful methods
    def add_A(self, dname, address):
        return self.add(dname, "A", address)

    def delete_A(self, dname):
        return self.delete(dname, "A")

    def add_CNAME(self, dname, cname):
        return self.add(dname, "CNAME", cname)

    def delete_CNAME(self, dname):
        return self.delete(dname, "CNAME")


def get_dnsupdate(logfile=None,  env=None, callback=None):
    pm = proctools.get_procmanager()
    proc = pm.spawnprocess(_DNSUpdate, NSUPDATE, logfile, env, callback, merge=0)
    return proc

def _dead_updater_cb(sts):
    print >>sys.stderr, sts

if __name__ == "__main__":
    du = get_dnsupdate(callback=_dead_updater_cb)
    du.server("localhost", 53)
    du.send()
    #pm = proctools.get_procmanager()
    #print du.readerr(37)
    #print du.readline()
    #du.close()
    #del du

