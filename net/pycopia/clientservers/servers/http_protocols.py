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
Collection of HTTP test protocols, server side.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


from pycopia import protocols

class BasicHTTPServerProto(protocols.Protocol):
    EOL = "\r\n"

    GETHEADERS = 1
    GOTPOST = 2
    POSTHEADERS = 3
    BODY = 4

    def initialize(self, fsm):
        fsm.set_default_transition(self._error, fsm.RESET)
        # GET
        fsm.add_regex(r"GET\s+(\S+)\s+HTTP/([0-9.]+)\r", fsm.RESET,
                self._get, self.GETHEADERS)
        fsm.add_regex(r"([a-zA-Z-]+):\s{0,1}(.*)\r", self.GETHEADERS,
                self._collect_header, self.GETHEADERS, ignore_case=True)
        fsm.add("\r\n", self.GETHEADERS, self._getend, fsm.RESET)
        # POST
        fsm.add_regex(r"POST\s+(\S+)\s+HTTP/([0-9.]+)\r", fsm.RESET,
                self._post, self.POSTHEADERS)
        fsm.add_regex(r"([a-zA-Z-]+):\s{0,1}(.*)\r", self.POSTHEADERS,
                self._collect_header, self.POSTHEADERS, ignore_case=True)
        fsm.add("\r\n", self.POSTHEADERS, self._startbody, fsm.RESET)
        #fsm.add_any(self.BODY, self._addbody, self.BODY)

    def _error(self, text):
        self.log("protocol error:", repr(text))
        print("HTTP/1.0 500 Error", repr(text),
                sep="\r\n\r\n", end="\r\n", file=self.iostream)
        raise protocols.ProtocolError(text)

    def _get(self, match):
        self.reset()
        self.path = match.group(1)
        self.httpver="HTTP/{}".format(match.group(2))

    def reset(self):
        self.headers = []
        self.body = None
        self._length = 0

    def _collect_header(self, match):
        hname = match.group(1)
        value = match.group(2)
        self.headers.append((hname, value))
        if hname.lower() == "content-length":
            self._length = int(value)

    def _getend(self, match):
        msg = "Got {0}\n".format(self.path)
        self.iostream.write(
        """{httpver} 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n{msg}""".format(
                        httpver=self.httpver, length=len(msg), msg=msg))
        raise protocols.ProtocolExit("All done")

    def _post(self, match):
        self.reset()
        self.path = match.group(1)
        self.httpver="HTTP/{}".format(match.group(2))

    def _startbody(self, match):
        if self._length:
            self.body = self.iostream.read(self._length)
        else:
            self.body = self.iostream.read(4096)
        msg = "Accepted: {}\n".format(self.body)
        self.iostream.write(
        """{httpver} 202 Accepted\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n{msg}""".format(
                        httpver=self.httpver, length=len(msg), msg=msg))

