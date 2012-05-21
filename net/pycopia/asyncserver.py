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
Asynchronous server core that supports protocol objects.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
import traceback

from pycopia import protocols
from pycopia import socket
from pycopia import asyncio


# Socket protocol handlers

CLOSED = 0
CONNECTED = 1

poller = asyncio.Poll()


class AsyncServerHandler(asyncio.PollerInterface):

    def __init__(self, sock, workerclass, protocol):
        self._sock = sock
        self._workerclass = workerclass
        self._protocol = protocol
        sock.setblocking(0)
        poller.register(self)

    def __del__(self):
        self.close()

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        if self._sock is not None:
            poller.unregister(self)
            s = self._sock
            self._sock = None
            s.close()

    closed = property(lambda self: bool(self._sock))

    def readable(self):
        return True

    def writable(self):
        return False

    def priority(self):
        return True

    def read_handler(self):
        conn, addr = self._sock.accept()
        conn.setblocking(0)
        h = self._workerclass(conn, addr, self._protocol)
        poller.register(h)
        return h


class AsyncWorkerHandler(asyncio.PollerInterface):
    def __init__(self, sock, addr, proto):
        self._sock = sock
        self._protocol = proto
        self._rem_address = addr
        self._state = CONNECTED
        self._writebuf = ""
        self.initialize()

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        if self._sock is not None:
            poller.unregister(self)
            s = self._sock
            self._sock = None
            if self._writebuf:
                s.send(self._writebuf)
                self._writebuf = ""
            s.close()
            self._state = CLOSED

    closed = property(lambda self: self._state == CLOSED)

    def write(self, data):
        self._writebuf += data
        poller.modify(self)
        return len(data)

    def readable(self):
        return self._state == CONNECTED

    def writable(self):
        return self._state == CONNECTED and bool(self._writebuf)

    def priority(self):
        return self._state == CONNECTED

    def hangup_handler(self):
        poller.unregister(self)
        self.close()

    def error_handler(self):
        poller.unregister(self)

    def write_handler(self):
        writ = self._sock.send(self._writebuf)
        self._writebuf = self._writebuf[writ:]
        poller.modify(self)

    def initialize(self):
        self._protocol.reset()

    def read_handler(self):
        with self._sock.makefile("w+b", 0) as fo:
            try:
                self._protocol.step(fo)
            except protocols.ProtocolExit:
                self.close()
            except protocols.ProtocolError:
                self.close()
                raise

    def pri_handler(self):
        log("unhandled pri")

    def exception_handler(self, ex, val, tb):
        traceback.print_exception(ex, val, tb)
        self.close()


def log(*args):
    print(*args, file=sys.stderr)

