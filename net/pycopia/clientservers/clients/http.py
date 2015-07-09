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

