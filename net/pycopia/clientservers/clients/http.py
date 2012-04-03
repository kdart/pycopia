#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Low-level HTTP protocol ticklers.

"""
from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

import os

from pycopia import protocols
from pycopia import clientserver



class BasicHTTPRequest(protocols.Protocol):
    EOL = "\r\n"

    def initialize(self, fsm):
        self.status = None
        self.headers = []
        self.bodychunks = []
        self.origin = "{}.local".format(os.uname()[1]) # TODO something better
        fsm.set_default_transition(self._enterdefault, fsm.RESET)
        fsm.add_regex(r"HTTP/1.1 200 (\S*)\r\n", fsm.RESET, self._status200, 1)
        fsm.add_regex(r"HTTP/1.1 (\d+) (\S*)\r\n", fsm.RESET, self._statusother, 1)
        fsm.add_regex(r"([A-Za-z-]+): (.+)\r\n", 1, self._header, 1)
        fsm.add(fsm.ANY, 1, self._bodybreak, 2)
        fsm.add(fsm.ANY, 2, self._body, 2)
        #fsm.add(fsm.ANY, 3, self._body, 3)

    def start(self):
        self.iostream.write("GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(self.origin))

    def _status200(self, mo):
        self.status = ("200", mo.groups()[0])

    def _statusother(self, mo):
        self.status = mo.groups() # TODO some 

    def _header(self, mo):
        self.headers.append(mo.groups())
        # TODO add content-length handler

    def _bodybreak(self, mo):
        pass

    def _body(self, mo):
        self.bodychunks.append(mo.string) # collect body

    def _enterdefault(self, mo):
        pass

#    def _error(self, mo):
#        raise protocols.ProtocolError("HTTP Client: bad response: {0}".format(mo.string))


class ChunkedHTTPRequest(protocols.Protocol):
    pass


def _test(argv):
        proto = BasicHTTPRequest()
        tc = clientserver.TCPClient("localhost", proto, port=80, logfile=sys.stderr)
        tc.run()
        print ("===== status =========")
        print (proto.status)
        print ("===== headers =========")
        print (proto.headers)
        print ("===== body =========")
        print (proto.bodychunks)

if __name__ == "__main__":
    import sys
    _test(sys.argv)

