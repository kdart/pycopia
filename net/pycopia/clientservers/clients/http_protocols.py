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


