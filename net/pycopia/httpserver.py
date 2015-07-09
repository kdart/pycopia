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
    sock = socket.tcp_listener(("", int(port)), 500)
    srv = asyncserver.AsyncServerHandler(
            sock, asyncserver.AsyncWorkerHandler, http_protocols.BasicHTTPServerProto())
    try:
        asyncserver.poller.loop()
    finally:
        asyncserver.poller.unregister_all()



if __name__ == "__main__":
    from pycopia import autodebug
    import sys
    simple_http_server(sys.argv)

