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
Simple client and server responder module.

"""

import sys
from pycopia import socket

class GenericServer(object):
    def __init__(self, port, host=""):
        self._sock = socket.tcp_listener((host, port), 1)

    def listen(self):
        conn, addr = self._sock.accept()
        print "Connect:", addr
        while 1:
            data = conn.recv(1024)
            if not data: 
                break
            conn.send(data)
        conn.close()

    def run(self):
        try:
            while 1:
                self.listen()
        except KeyboardInterrupt:
            return


class GenericClient(object):
    def __init__(self, host, port):
        self._sock = socket.connect_tcp(host, port)

    def run(self):
        try:
            try:
                while 1:
                    line = raw_input("> ")
                    self._sock.send(line)
                    data = self._sock.recv(1024)
                    if not data:
                        break
                    else:
                        print data
            except KeyboardInterrupt:
                pass
        finally:
            self._sock.close()




def get_tcp_server(port, addr=""):
    return GenericServer(port, addr)

def get_tcp_client(addr, port):
    return GenericClient(addr, port)


def _test(argv):
    if len(argv) > 1:
        if "-s" in argv:
            s = get_tcp_server(8123, "")
            s.run()
        elif "-c" in argv:
            c = get_tcp_client("localhost", 8123)
            print "Send something to server."
            c.run()

if __name__ == "__main__":
    _test(sys.argv)
