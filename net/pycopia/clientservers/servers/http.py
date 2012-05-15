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
Low-level HTTP protocol testers, server side.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys

from pycopia import clientserver
from . import http_protocols


def basic_server(argv):
    port = argv[1] if len(argv) > 1 else 8080
    proto = http_protocols.BasicHTTPServerProto()
    srv = clientserver.TCPServer(clientserver.TCPWorker, proto, port=port, debug=False)
    srv.run()

if __name__ == "__main__":
    basic_server(sys.argv)
