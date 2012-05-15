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
Low-level HTTP protocol testers, client side.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys

from pycopia import clientserver
from . import http_protocols



# mostly for testing
def basic_request(argv):
    host = argv[1] if len(argv) > 1 else "localhost"
    port = argv[2] if len(argv) > 2 else 80
    proto = http_protocols.BasicHTTPRequest()
    tc = clientserver.TCPClient(host, proto, port=int(port), logfile=sys.stderr)
    tc.run()
    print ("===== status =========")
    print (proto.status)
    print ("===== headers =========")
    print (proto.headers)
    print ("===== body =========")
    print (proto.bodychunks)


def basic_post(argv):
    host = argv[1] if len(argv) > 1 else "localhost"
    port = argv[2] if len(argv) > 2 else 80
    proto = http_protocols.BasicHTTPPOST()
    tc = clientserver.TCPClient(host, proto, port=int(port), logfile=sys.stderr)
    tc.run()
    print ("===== status =========")
    print (proto.status)
    print ("===== headers =========")
    print (proto.headers)
    print ("===== body =========")
    print (proto.bodychunks)

if __name__ == "__main__":
    #basic_request(sys.argv)
    basic_post(sys.argv)

