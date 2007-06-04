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

import sys

from pycopia import scheduler
from pycopia import proctools

class Pinger(proctools.ProcessPipe):
    """
This class is an interface to, and opens a pipe to, the pyntping program.
This program actually does a bit more than ping, but pinging is the most
common use.  The pyntping program is a C program that should be installed
in your path, owned by root, with SUID bit set. This is necessary because
only root can open RAW sockets for ICMP operations.

Methods are listed below. Most methods take a single host, or multiple
hosts when called. If a single host is given, a single value will be
returned. If more than one is given, a list of result will be returned.

The following attributes may also be adjusted:
        retries 
        timeout
        delay
        size
        hops

    """

    # ICMP methods
    def echo(self, *hosts):
        cmdstr = ""
        return self.__do_command(cmdstr, hosts)

    # return a sublist of only those hosts that are reachable
    def reachablelist(self, *hosts):
        cmdstr = ""
        rv = self.__do_command(cmdstr, hosts)
        return filter(lambda x: x[1] >= 0, rv)

    # return a boolean value if a host is reachable.
    # If list given, return a list of (host, reachable) tuples.
    def reachable(self, *hosts):
        cmdstr = ""
        rv = self.__do_command(cmdstr, hosts)
        return map(lambda x: (x[0], x[1] >= 0), rv)

    def ping(self, *hosts):
        cmdstr = ""
        return self.__do_command(cmdstr, hosts)

    def mask(self, *hosts):
        cmdstr = "-mask "
        return self.__do_command(cmdstr, hosts)

    def timestamp(self, *hosts):
        cmdstr = "-tstamp "
        return self.__do_command(cmdstr, hosts)

    def ttl(self, *hosts):
        cmdstr = "-ttl %d " % (self.hops)
        return self.__do_command(cmdstr, hosts)

    def trace(self, *hosts):
        cmdstr = "-trace %d " % (self.hops)
        return self.__do_command(cmdstr, hosts)

    def __do_command(self, cmdstr, hosts):
        for host in hosts:
            if isinstance(host, list):
                s = []
                for hle in host:
                    s.append(str(hle))
                cmdstr += " ".join(s)
            else:
                cmdstr += " %s" % host
        rqst = "-size %d -timeout %d -retries %d -delay %d %s\n" % \
                    (self.size, self.timeout, self.retries, self.delay, cmdstr)
        self._write(rqst)
        # now try and get all of pyntping's output
        resstr = self._read(4096)
        scheduler.sleep(1)
        while self.fstat().st_size != 0:
            next = self._read(4096)
            if next:
                resstr += next
            scheduler.sleep(1)
        # we should have got a tuple of tuples
        result =  eval(resstr)
        return result

#### end Ping

## some factory/utility functions
def get_pinger(retries=3, timeout=5, delay=0, size=64, hops=30, logfile=None):
    """Returns a Pinger process that you can call various ICMP methods
    on."""
    pm = proctools.get_procmanager()
    pinger = pm.spawnprocess(Pinger, "pyntping -b", logfile=logfile, env=None, callback=None, 
                persistent=False, merge=True, pwent=None, async=False, devnull=False)
    pinger.retries = retries
    pinger.timeout = timeout
    pinger.delay = delay
    pinger.size = size
    pinger.hops = hops
    return pinger

def reachable_hosts(hostlist):
    """
reachable_hosts(hostlist)
where <hostlist> is a list of host strings.
    """
    pinger = get_pinger()
    res = pinger.reachable(hostlist)
    return map(lambda x: x[0], res)

def scan_net(net):
    """
scan_net(network)
where <network> is an IPv4 object or list with host and broadcast elements at ends.
    """
    pinger = get_pinger()
    res = pinger.reachablelist(net[1:-1])
    return map(lambda x: x[0], res)

def traceroute(hostip, maxhops=30):
    """
traceroute(hostip, maxhops=30)
return a list of (ipaddr, time) tuples tracing a path to the given hostip.
    """
    tracelist = []
    pinger = get_pinger()
    for ttl in xrange(maxhops): 
        pinger.hops = ttl+1
        nexthop = pinger.ttl(hostip)[0]
        if nexthop[0] != hostip:
            tracelist.append(nexthop)
        else:
            tracelist.append(nexthop)
            return tracelist
    return tracelist

def ping(host, retries=3, timeout=5, delay=1, size=64, hops=30):
    pinger = get_pinger(retries, timeout, delay, size, hops)
    sum = 0
    Nxmit = 0
    Nrecv = 0
    _min = sys.maxint
    _max = 0
    print "Pinging %s with %d bytes of data." % (host, size)
    try:
        while 1: # escape with SIGINT (^C)
            Nxmit = Nxmit + 1
            host, rttime = pinger.ping(host)[0]
            if rttime >= 0:
                sum += rttime
                Nrecv = Nrecv + 1
                _min = min(_min, rttime)
                _max = max(_max, rttime)
                print "%-16s  %d ms" % (host, rttime)
            scheduler.sleep(pinger.delay)
    except KeyboardInterrupt:
        print "%d packets transmitted, %d packets received, %d%% packet loss" % (Nxmit, Nrecv, 100-(Nxmit/Nrecv*100))
        print "round-trip min/avg/max = %d/%d/%d ms" % (_min, sum/Nrecv, _max)

def reachable(*hosts):
    pinger = get_pinger()
    return pinger.reachable(*hosts)

