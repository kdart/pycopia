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
    """Generic asynchronous server handler.
    Register an instance of this, with a worker class and a protocol, with the
    poller.
    """

    def __init__(self, sock, workerclass, protocol):
        self._sock = sock
        _host, self.server_port = sock.getsockname()
        self.server_name = socket.getfqdn(_host)
        self._workerclass = workerclass
        self.protocol = protocol
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
        h = self._workerclass(conn, addr, self.protocol)
        poller.register(h)
        return h


class AsyncWorkerHandler(asyncio.PollerInterface):
    def __init__(self, sock, addr, proto):
        self.address = addr
        self._sock = sock
        self.protocol = proto
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
        self.protocol.reset()

    def read_handler(self):
        with self._sock.makefile("w+b", 0) as fo:
            try:
                self.protocol.step(fo, self.address)
            except protocols.ProtocolExit:
                self.close()
            except protocols.ProtocolError:
                self.close()
                raise

    def pri_handler(self):
        log("unhandled priority message")

    def exception_handler(self, ex, val, tb):
        traceback.print_exception(ex, val, tb)
        self.close()


def log(*args):
    """Print to stderr"""
    print(*args, file=sys.stderr)

