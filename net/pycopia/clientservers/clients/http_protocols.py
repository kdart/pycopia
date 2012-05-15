#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab:fenc=utf-8
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
HTTP Test protocols, server side.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from pycopia import protocols

class BasicHTTPRequest(protocols.Protocol):
    EOL = "\r\n"

    def initialize(self, fsm):
        fsm.set_default_transition(self._enterdefault, fsm.RESET)
        fsm.add_regex(r"HTTP/1.1 200 (\S*)\r\n", fsm.RESET, self._status200, 1)
        fsm.add_regex(r"HTTP/1.1 (\d+) (\S*)\r\n", fsm.RESET, self._statusother, 1)
        fsm.add_regex(r"([A-Za-z-]+): (.+)\r\n", 1, self._header, 1)
        fsm.add("\r\n", 1, None, 2) # body break
        fsm.add(fsm.ANY, 2, self._body, 2)

    def start(self):
        self.status = None
        self.headers = []
        self.bodychunks = []
        self.iostream.write(
                "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(self.iostream.host))

    def _status200(self, mo):
        self.status = ("200", mo.groups()[0])

    def _statusother(self, mo):
        self.status = mo.groups() # TODO something...

    def _header(self, mo):
        hname, hvalue = mo.groups()
        self.headers.append((hname, hvalue))
        if hname.lower() == "content-length":
            self._content_length = int(hvalue)

    def _body(self, text):
        self.bodychunks.append(text) # collect body

    def _enterdefault(self, text):
        print("Unknown text:", text, file=sys.stderr)


class ChunkedHTTPRequest(protocols.Protocol):
    pass # TODO


class BasicHTTPPOST(protocols.Protocol):
    EOL = "\r\n"

    def initialize(self, fsm):
        fsm.set_default_transition(self._enterdefault, fsm.RESET)
        fsm.add_regex(r"HTTP/1.1 200 (\S*)\r\n", fsm.RESET, self._status200, 1)
        fsm.add_regex(r"HTTP/1.1 (\d+) (\S*)\r\n", fsm.RESET, self._statusother, 1)
        fsm.add_regex(r"([A-Za-z-]+): (.+)\r\n", 1, self._header, 1)
        fsm.add("\r\n", 1, None, 2) # body break
        fsm.add(fsm.ANY, 2, self._body, 2)

    def start(self):
        self.status = None
        self.headers = []
        self.bodychunks = []
        data = "data=Post+data"
        self.iostream.write(
                """POST /post HTTP/1.1\r
Host: {}\r
Connection: close\r
Content-Type: application/x-www-form-urlencoded\r
Content-Length: {}\r
\r
{}""".format(self.iostream.host, len(data), data))

    def _status200(self, mo):
        self.status = ("200", mo.groups()[0])

    def _statusother(self, mo):
        self.status = mo.groups()

    def _header(self, mo):
        hname, hvalue = mo.groups()
        self.headers.append((hname, hvalue))
        if hname.lower() == "content-length":
            self._content_length = int(hvalue)

    def _body(self, text):
        self.bodychunks.append(text) # collect body

    def _enterdefault(self, text):
        self.log("Unknown text:", text, "state:", self.state)


