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
Collection of HTTP test protocols, server side.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


from pycopia import protocols

class BasicHTTPServerProto(protocols.Protocol):
    """A simple HTTP protocol implementation, server side."""
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
        self.clear()
        self.path = match.group(1)
        self.httpver="HTTP/{}".format(match.group(2))

    def clear(self):
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
        self.clear()
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

