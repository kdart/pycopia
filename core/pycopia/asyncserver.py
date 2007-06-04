#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
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
Basic async server using the asyncio and socket modules.

"""

import sys

from pycopia import socket, asyncio


class TCPSocketServer(socket.AsyncSocket):

    def set_worker(self, klass):
        self.workerclass = klass
        self._workers = {}

    def handle_accept(self):
        sock, addr = self.accept()
        worker = self.workerclass(sock, addr)
        asyncio.poller.register(worker)

        #self._workers[addr] = worker

    def handle_read(self):
        print "XXX server read:"
        print self.recv(4096)

    def callback(self):
        pass
        #print "XXX looped",
        #print asyncio.poller.smap.keys()

    def run(self):
        asyncio.poller.loop(5, callback=self.callback)
        #asyncio.poller.loop()

#       import signal
#       try:
#           while 1:
#               signal.pause()
#               self.accept()
#       except KeyboardInterrupt:
#           return



class SocketWorker(object):
    def __init__(self, sock, addr=None):
        self.address = addr
        self._sock = sock
        self._state = socket.CONNECTED
        self.recv = self._sock.recv
        self.sendto = self._sock.sendto
        self.recvfrom = self._sock.recvfrom
        self._buf = ""
        self._pribuf = ""
        self.initialize()

    def close(self):
        self._sock = None
        self.send = self.recv = self.sendto = self.recvfrom = None

    def fileno(self):
        return self._sock.fileno()

#   def get_handlers(self):
#       return (asyncio.HandlerMethods(self._sock.fileno(), 
#                readable=self.readable, read_handler=self.handle_read,
#                writable=self.writable, write_handler=self.handle_write_event,
#                hangup_handler=self.finalize),)
#
    def initialize(self):
        print >>sys.stderr, "*** SocketWorker: unhandled initialize event"

    def finalize(self):
        print >>sys.stderr, "*** SocketWorker: unhandled finalize event"
        asyncio.poller.unregister(self)
        self.close()

    # delegation to socket object
#   def __getattr__(self, name):
#       return getattr(self._sock, name)

    def readable(self):
        #return (self._state == socket.CONNECTED)
        return True

    def writable(self):
        return (self._state == socket.CONNECTED) and bool(self._buf)

    def priority(self):
        return (self._state == socket.CONNECTED) and bool(self._pribuf)

    def handle_read(self):
        print >>sys.stderr, "SocketWorker: unhandled read"

    def handle_accept(self):
        print >>sys.stderr, "SocketWorker: unhandled accept"

    def handle_connect(self):
        print >>sys.stderr, "SocketWorker: unhandled connect"
    
    def handle_hangup(self):
        print >>sys.stderr, "SocketWorker: unhandled hangup"

    def handle_priority(self):
        print >>sys.stderr, "SocketWorker: unhandled priority"

    def handle_error(self, ex, val, tb):
        print >>sys.stderr, "SocketWorker: unhandled error: %s (%s)"  % (ex, val)
        
    def handle_read_event(self):
        self.handle_read()

    def handle_write_event(self):
        self._send()

    def handle_priority_event(self):
        print >>sys.stderr, "SocketWorker: unhandled priority event"

    def handle_hangup_event(self):
        """Callback that gets called when file desriptor closes for some
        reason."""
        print >>sys.stderr, "*** SocketWorker: in hangup event"
        self._state = socket.CLOSED
        self.close()

    def _send(self, flags=0):
        while 1:
            try:
                sent = self._sock.send(self._buf[:4096], self._sendflags)
            except SocketError, why:
                if why[0] == EINTR:
                    continue
                else:
                    raise
            else:
                self._buf = self._buf[sent:]
                break
        return sent

    # fake the send and let the asyncio handler deal with it
    def send(self, data, flags=0):
        self._buf += data
        self._sendflags = flags
        return len(data)


# simple server examples
class DiscardWorker(SocketWorker):
    def handle_read(self):
        d = self.recv(4096)

class EchoWorker(SocketWorker):
    def handle_read(self):
        d = self.recv(4096)
        self.send(d)

class TestWorker(SocketWorker):
    def handle_read(self):
        d = self.recv(4096)
        self.send(d)



### client parts ######
#
class TCPClientSocket(socket.AsyncSocket):

    def set_callback(self, cb):
        self._callback = cb

    def handle_read(self):
        d = self.recv(4096)
        self._callback(d)


class TCPClient(object):
    def __init__(self, host='', port=8123, bindto=None, logfile=None):
        self.logfile = logfile
        self.host = host
        self.port = port
        self.bindto = bindto
        self._sock = None

    def connect(self):
        if self.logfile:
            self.logfile.write('attempting to connect to: %s %d\n' % (self.host, self.port))
        s = socket.connect_tcp(self.host, self.port, TCPClientSocket)
        if self.bindto:
            s.bind((self.bindto, socket.IPPORT_USERRESERVED))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.set_callback(self.read_handler)
        self._sock = s
        if self.logfile:
            self.logfile.write('connected\n')
        asyncio.poller.register(s)
    
    def close(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    def read_handler(self, data):
        pass

    def send(self, data):
        return self._sock.send(data)


# factory functions

def get_tcp_server(port, addr="", workerclass=TestWorker):
    s = socket.tcp_listener((addr, port), 5, TCPSocketServer)
    s.set_worker(workerclass)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    asyncio.stop_sigio()
    asyncio.poller.register(s)
    return s

def get_tcp_client(dest, port, bindto=None, clientclass=TCPClient, logfile=None):
    c = clientclass(dest, port, bindto, logfile=logfile)
    c.connect()
    return c


def _test(argv):
    if len(argv) > 1:
        if "-s" in argv:
            s = get_tcp_server(8123, "", TestWorker)
            s.run()
        elif "-c" in argv:
            class TestClient(TCPClient):
                def read_handler(self, data):
                    print data

            c = get_tcp_client("localhost", 8123, clientclass=TestClient, logfile=sys.stderr)
            print "Send something to server."
            while 1:
                try:
                    t = raw_input("> ")
                    c.send(t)
                    #resp = c.readline()
                    #print resp
                except (KeyboardInterrupt, EOFError):
                    break
            c.close()



if __name__ == "__main__":
    _test(sys.argv)

