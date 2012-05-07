#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Common support for remote control objects.

Also, all Pyro interfaces go through here to encapsulate all the Pyro
quirks.

"""
from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

import sys, os
import select

from pycopia import asyncio
# Must be before Pyro4 import
from pycopia.QA import logging

# This is the only place where Pyro4 should ever be imported.
import Pyro4
from Pyro4.errors import *

from pycopia import debugger

# Pyro config is still weird.
def set_p4_config():
    from pycopia import basicconfig
    p4conf = basicconfig.get_config("pyro4.conf")
    pcf = Pyro4.config
    for name in pcf.__slots__:
        setattr(pcf, name, p4conf.get(name, getattr(pcf, name)))
set_p4_config()
del set_p4_config


class PyroAsyncAdapter(asyncio.PollerInterface):
    """Adapt a Pyro4 deamon to the pycopia asyn poller interface."""

    def __init__(self, pyrodaemon):
        self._pyd = pyrodaemon
        self._poller = select.epoll()
        self.smap = {}
        self.update()

    def update(self):
        smap = self.smap
        nsmap = {}
        for s in self._pyd.sockets:
            fd = s.fileno()
            if fd not in smap:
                self._poller.register(fd, select.EPOLLIN)
            nsmap[fd] = s
        self.smap = nsmap

    def fileno(self):
        return self._poller.fileno()

    def readable(self):
        return bool(self.smap)

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        while 1:
            try:
                rl = self._poller.poll(0)
            except IOError as why:
                if why[0] == EINTR:
                    continue
                else:
                    raise
            else:
                break
        readysocks = []
        for fd, flags in rl:
            sock = self.smap[fd]
            readysocks.append(sock)
        self._pyd.events(readysocks)
        self.update()

    def exception_handler(self, ex, val, tb):
        debugger.post_mortem(tb, ex, val)
        #print("PyroAsyncAdapter error: {} ({})".format(ex, val), file=sys.stderr)


def register_server(serverobject):
    pyrodaemon = Pyro4.Daemon()
    uri = pyrodaemon.register(serverobject)
    ns=Pyro4.locateNS()
    ns.register("{}:{}".format(serverobject.__class__.__name__, os.uname()[1]), uri)
    p = PyroAsyncAdapter(pyrodaemon)
    asyncio.poller.register(p)
    return p

def unregister_server(p):
    asyncio.poller.unregister(p)

def loop(timeout=-1, callback=asyncio.NULL):
    asyncio.poller.loop(timeout, callback)

def get_remote(name):
    ns = Pyro4.locateNS()
    slist = ns.list(regex=name)
    #return Pyro4.Proxy("PYRONAME://%s" % (name,))
    return Pyro4.Proxy(slist.popitem()[1])

def get_proxy(uri):
    return Pyro4.Proxy(uri)

def locate_nameserver():
    return Pyro4.locateNS()

