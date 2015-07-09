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
Common support for remote control objects.

Also, all Pyro interfaces go through here to encapsulate all access to Pyro
and provide factory functions common to Pycopia.

It also provides for using a new configuration file, pyro4.conf, which is required.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import select
import socket

from pycopia import asyncio

# Must import stock logging module before Pyro4, even if it's not used
# here.
import logging
import logging.config

logging.config.fileConfig("/etc/pycopia/logging.cfg")

# This is the only place where Pyro4 should ever be imported.
import Pyro4
import Pyro4.socketutil
from Pyro4.errors import *


class NameNotFoundError(NamingError):
    pass


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
        self._pyrod = pyrodaemon
        self._poller = select.epoll()
        self.smap = {}
        self.update()

    def update(self):
        smap = self.smap
        nsmap = {}
        for s in self._pyrod.sockets:
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
                if why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        readysocks = []
        for fd, flags in rl:
            sock = self.smap.get(fd)
            if sock is not None:
                readysocks.append(sock)
        self._pyrod.events(readysocks)
        self.update()

    def exception_handler(self, ex, val, tb):
        from pycopia import debugger
        debugger.post_mortem(tb, ex, val)


def register_server(serverobject, host=None, port=0, unixsocket=None, nathost=None, natport=None):
    """Regiseter the server with Pycopia asyncio event handler."""
    host = host or Pyro4.config.HOST or Pyro4.socketutil.getIpAddress(socket.getfqdn())
    pyrodaemon = Pyro4.Daemon(host=host, port=port,
            unixsocket=unixsocket, nathost=nathost, natport=natport)
    uri = pyrodaemon.register(serverobject)
    ns=Pyro4.locateNS()
    ns.register("{}:{}".format(serverobject.__class__.__name__, socket.getfqdn()), uri)
    p = PyroAsyncAdapter(pyrodaemon)
    asyncio.poller.register(p)
    return p


def get_remote(hostname, servicename=None):
    """Find and return a client (proxy) give the fully qualified host name and optional servicename.
    """
    if servicename:
        patt = "{}:{}".format(servicename, hostname)
    else:
        patt = hostname
    ns = Pyro4.locateNS()
    slist = ns.list(prefix=patt)
    if slist:
        return Pyro4.Proxy(slist.popitem()[1])
    else:
        raise NameNotFoundError("Service name {!r} not found.".format(patt))


def unregister_server(p):
    asyncio.poller.unregister(p)


def loop(timeout=-1, callback=asyncio.NULL):
    asyncio.poller.loop(timeout, callback)


def get_proxy(uri):
    return Pyro4.Proxy(uri)


def locate_nameserver():
    return Pyro4.locateNS()

