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
Asynchronous HTTP server.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from pycopia import socket
from pycopia import asyncserver
from pycopia.clientservers.servers import http_protocols



def simple_http_server(argv):
    port = argv[1] if len(argv) > 1 else 8080
    sock = socket.tcp_listener(("", int(port)))
    srv = asyncserver.AsyncServerHandler(
            sock, asyncserver.AsyncWorkerHandler, http_protocols.BasicHTTPServerProto)
    try:
        asyncserver.poller.loop()
    finally:
        asyncserver.poller.unregister_all()



if __name__ == "__main__":
    from pycopia import autodebug
    import sys
    simple_http_server(sys.argv)

