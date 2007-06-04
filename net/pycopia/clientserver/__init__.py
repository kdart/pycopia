#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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
Generic server builder for creating custom protocols.

"""

import sys
from cStringIO import StringIO

from pycopia import socket
from pycopia import expect # the Expect object can be used to build any FSM.


class ServerExit(EnvironmentError):
    pass

class ClientExit(EnvironmentError):
    pass



class ProcessModel(object):
    """Determines process model to use for workers."""
    def __call__(self, func):
        raise NotImplementedError


class ForkingModel(ProcessModel):
    """This is the default process model."""
    def __init__(self, pwent=None):
        from pycopia import proctools
        self._procmanager = proctools.get_procmanager()
        self.pwent = pwent

    def __call__(self, func, args=None, kwargs=None):
        self._procmanager.submethod(func, 
                         args=args or (), kwargs=kwargs or {}, pwent=pwent)


class ThreadProcessModel(ProcessModel):
    """This process model uses threads. TODO This is not complete."""
    def __init__(self):
        import threading
        self.Thread = threading.Thread

    def __call__(self, func, args=None, kwargs=None):
        t = self.Thread(target=func, args=args or (), kwargs=kwargs or {})
        t.start()


class Protocol(object):
    def __init__(self):
        self.states = expect.StateMachine()
        self.exp = None
        self.initialize()

    def initialize(self):
        """Fill this in with state transitions."""
        pass

    def set_expect(self, exp):
        assert issubclass(exp, expect.Expect)
        self.exp = exp

    def run(self, exp):
        states = self.states
        states.reset()
        try:
            while 1:
                next = exp.read_until()
                if next:
                    states.step(next)
                else:
                    break
        finally:
            self.exp = None

    def handle_read(self):
        next = self.exp.read_until()
        states.step(next)

# XXX

class DefaultProtocol(Protocol):

    def initialize(self):
        states = self.states
        states.set_default_transition(self._error, states.RESET)

    def _error(self, mo):
        print >>sys.stderr, "Error: symbol: %s, from: %s" % (mo.string, 
                                                      self.states.current_state)


# worker classes for servers:

class BaseWorker(object):
    def __init__(self, sock, addr, protocol):
        self._sock = sock
        self.address = addr
        self.protocol = protocol
        # convenient method references:
        self.sendall = sock.sendall
        self.send = sock.send
        self.recv = sock.recv

    def __call__(self):
        raise NotImplementedError("override in subclass")

    def initialize(self):
        pass

    def finalize(self):
        pass


class StreamWorker(BaseWorker):
    EOL="\n"
    # Worker objects must be callable so the subprocess method can invoke it.
    def __call__(self):
        fo = self._sock.makefile("w+", 1)
        exp = expect.Expect(fo, prompt=self.EOL)
        self.initialize()
        self.run(exp)
        self.finalize()
        fo.flush() 
        fo.close()
        self._sock.close()

    def run(self, exp):
        try:
            self.protocol.run(exp)
        except ServerExit:
            return True
        except ProtocolError:
            return False


# datagram workers:

class DatagramWorker(BaseWorker):
    def __call__(self, data):
        self.protocol.reset()
        self.initialize()
        self.run(data)
        self.finalize()

    def sendto(self, data, flags=0):
        return self._sock.sendto(data, flags, self.address)

    def step(self):
        next = self._sock.recv(4096)
        if next:
            self.protocol.step(next)
            return True
        return False

    def run(self, data):
        self.protocol.step(data)
        try:
            while 1:
                if not self.step():
                    break
        except ServerExit:
            return True
        except ProtocolError:
            return False


### real worker classes you can specify:
class TCPWorker(StreamWorker):
    port = None

class UDPWorker(DatagramWorker):
    port = None

class UnixStreamWorker(StreamWorker):
    PATH = "/tmp/_UnixStream"

class UnixDatagramWorker(DatagramWorker):
    PATH = "/tmp/_UnixDatagram"

### server objects:

class Server(object):
    """Base class for all servers."""

    def fileno(self):
        return self._sock.fileno()


class TCPServer(Server):
    def __init__(self, workerclass, protocol, port=None, host="", 
                  processmodel=None, debug=False):
        if port is None:
            port = workerclass.port
        self._procmanager = processmodel or ForkingModel()
        self.workerclass = workerclass
        self.engine = protocol
        self.debug = debug
        self._sock = socket.tcp_listener((host, port), 5)
        if debug:
            global debugger
            from pycopia import debugger

    def accept(self):
        conn, addr = self._sock.accept()
        worker = self.workerclass(conn, addr, self.engine)
        if self.debug:
            try:
                worker()
            except:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
        else:
            self._procmanager(worker)
        conn.close()

    def run(self):
        try:
            while 1:
                self.accept()
        except KeyboardInterrupt:
            return


class UDPServer(Server):
    def __init__(self, workerclass, port=None, host="", debug=False):
        if port is None:
            port = workerclass.port
        self._sock = socket.udp_listener((host, port))
        self.workerclass = workerclass
        self.debug = debug
        if debug:
            global debugger
            from pycopia import debugger

    def __del__(self):
        self._sock.close()

    def accept(self):
        data, addr = self._sock.recvfrom(4096)
        worker = self.workerclass(self._sock, addr)
        if self.debug:
            try:
                worker(data)
            except:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
        else:
            worker(data)

    def run(self):
        try:
            while 1:
                self.accept()
        except ServerExit, val:
            return val

class UnixStreamServer(Server):
    def __init__(self, workerclass, path=None, processmodel=None, debug=False):
        if path is None:
            path = workerclass.PATH
        self._sock = socket.unix_listener(path)
        self.workerclass = workerclass
        self._procmanager = processmodel or ForkingModel()
        self.debug = debug
        if debug:
            global debugger
            from pycopia import debugger

    def accept(self):
        conn, addr = self._sock.accept()
        worker = self.workerclass(conn, addr)
        if self.debug:
            try:
                worker()
            except:
                ex, val, tb = sys.exc_info()
                debugger.post_mortem(tb, ex, val)
        else:
            self._procmanager(worker)
        conn.close()

    def run(self):
        try:
            while 1:
                self.accept()
        except KeyboardInterrupt:
            return

class UnixDatagramServer(Server):
    PATH = "/tmp/_UnixDatagram"
    def __init__(self, workerclass, path=None, debug=False):
        if path is None:
            path = self.PATH
        self._sock = socket.udp_listener((host, port))
        self.workerclass = workerclass
        self.debug = debug
        if debug:
            global debugger
            from pycopia import debugger

    def __del__(self):
        self._sock.close()

### Client side base classes ###

class BaseClient(object):
    def __del__(self):
        self.close()

    def close(self):
        if self._sock:
            self.finalize()
            self._sock.close()
            self._sock = None
    
    # override this to set up your protocol
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)

    def finalize(self):
        pass

    def _error(self, s, fsm):
        print >>sys.stderr, "bad transition symbol and state: %s, %s" % (s, fsm.current_state)

    def step(self):
        next = self.getnext()
        if next:
            self.fsm.step(next)
            return True
        return False

    def run(self):
        try:
            while 1:
                if not self.step():
                    break
        except ClientExit, val:
            return val

class StreamClient(BaseClient):
    EOL = "\n"
    def __init__(self, sock, logfile=None):
        self._sock = sock
        self.fsm = expect.Expect(self._sock, prompt=self.EOL, logfile=logfile)
        self.initialize()

    def getnext(self):
        return self.fsm.read_until()

    def send(self, data):
        self._sock.sendall(data)

    def recv(self, N, flags=0):
        return self._sock.recv(N, flags)

class DatagramClient(BaseClient):
    def __init__(self, sock, logfile=None):
        global fsm
        from pycopia import fsm
        self._sock = sock
        self.fsm = fsm.FSM()
        self._logfile = logfile
        self.initialize()

    def getnext(self):
        data = self._sock.recv(4096)
        if self._logfile:
            self.logfile.write(data)
        return data

    def send(self, data):
        if self._logfile:
            self.logfile.write(data)
        self._sock.send(data)

    def recv(self, amt=4096):
        data = self._sock.recv(amt)
        if self._logfile:
            self.logfile.write(data)
        return data


class TCPClient(StreamClient):
    port = None
    def __init__(self, host, port=None, logfile=None):
        if port is None:
            port = self.port
        sock = socket.connect_tcp(host, port)
        super(TCPClient, self).__init__(sock, logfile)


class UnixStreamClient(StreamClient):
    PATH = "/tmp/_UnixStream"
    def __init__(self, path, logfile=None):
        if path is None:
            path = self.PATH
        sock = socket.connect_unix(path)
        super(UnixStreamClient, self).__init__(sock, logfile)


class UDPClient(DatagramClient):
    port = None
    def __init__(self, host, port=None, logfile=None):
        if port is None:
            port = self.port
        sock = socket.connect_udp(host, port)
        super(UDPClient, self).__init__(sock, logfile)

class UnixDatagramClient(DatagramClient):
    PATH = "/tmp/_UnixDatagram"
    def __init__(self, path=None, logfile=None):
        if path is None:
            path = self.PATH
        sock = socket.connect_unix_datagram(path)
        super(UnixDatagramClient, self).__init__(sock, logfile)



### a simple echo server and client for testing purposes ####
class EchoWorker(TCPWorker):
    port = 8123
    def run(self):
        s = self._sock
        s.send("%s\n" % (self.address,))
        try:
            while 1:
                data = s.recv(1024)
                if not data: 
                    break
                s.send(data)
        finally:
            s.close()

class UDPEchoWorker(UDPWorker):
    port = 8123
    def run(self, data):
        self._sock.sendto(data, self.address)
        try:
            while 1:
                data = self._sock.recv(4096)
                if not data:
                    break
                self._sock.sendto(data, self.address)
        except KeyboardInterrupt:
            pass


# sample client
class EchoClient(TCPClient):
    port = 8123
    def run(self):
        try:
            try:
                print self._sock.recv(1024)
                while 1:
                    line = raw_input("> ")
                    self._sock.send(line)
                    data = self._sock.recv(2048)
                    if not data:
                        break
                    else:
                        print data
            except KeyboardInterrupt:
                pass
        finally:
            self._sock.close()

class UDPEchoClient(UDPClient):
    port = 8123
    def run(self):
        try:
            try:
                while 1:
                    line = raw_input("> ")
                    self._sock.send(line)
                    data = self._sock.recv(2048)
                    if not data:
                        break
                    else:
                        print data
            except KeyboardInterrupt:
                pass
        finally:
            self._sock.close()


# simple hello-bye protocol for unit testing.
class TestServer(TCPWorker):
    port = 8134

    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition(fsm.ANY, fsm.RESET, self._start, 1)
        fsm.add_transition("GREETINGS", 1, None, 2)
        fsm.add_transition("BYE", 2, self._bye, fsm.RESET)
        fsm.step(fsm.ANY) # kickstart the protocol

    def _start(self, s, fsm):
        print "Sending HELLO"
        fsm.writeln("HELLO")

    def _bye(self, s, fsm):
        print "Sending BYE"
        fsm.writeln("BYE")
        raise ServerExit


class TestClient(TCPClient):
    port = 8134

    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._error, fsm.RESET)
        fsm.add_transition("HELLO", fsm.RESET, self._greet, 1)
        fsm.add_transition("BYE", 1, self._bye, fsm.RESET)

    def _greet(self, s, fsm):
        print "Sending GREETINGS"
        fsm.writeln("GREETINGS")
        print "Sending BYE"
        fsm.writeln("BYE") # cheat here just to keep things moving 

    def _bye(self, s, fsm):
        print "in BYE"
        raise ClientExit, 0

# helper to import a named object
def _get_module(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

# Generic object getters. Use the module.class path name as the name string.
def get_client(name, dest, port=None, logfile=None):
    """Give the pathname of a Client subclass, and destination address. This
    will return a client connected to destination."""
    if type(name) is str:
        parts = name.split(".")
        mod = _get_module(".".join(parts[:-1]))
        clientclass = getattr(mod, parts[-1])
    elif type(name) is type:
        clientclass = name
    else:
        raise ValueError, "invalid object for 'name' parameter: %s" % (name,)
    assert issubclass(clientclass, BaseClient), "need BaseClient type"
    return clientclass(dest, port=port, logfile=logfile)

def get_server(name, debug=False):
    """Give the pathname of a worker class. This will return the
    appropriate type of server for it.
    """
    if type(name) is str:
        parts = name.split(".")
        mod = _get_module(".".join(parts[:-1]))
        workerclass = getattr(mod, parts[-1])
    elif type(name) is type:
        workerclass = name
    else:
        raise ValueError, "invalid object for 'name' parameter: %s" % (name,)
    assert issubclass(workerclass, BaseWorker), "need BaseWorker type"
    if issubclass(workerclass, TCPWorker):
        srv = TCPServer(workerclass, workerclass.port, debug=debug)
    elif issubclass(workerclass, UDPWorker):
        srv = UDPServer(workerclass, workerclass.port, debug=debug)
    elif issubclass(workerclass, UnixStreamWorker):
        srv = UnixStreamServer(workerclass, workerclass.PATH, debug=debug)
    elif issubclass(workerclass, UnixDatagramWorker):
        srv = UnixDatagramServer(workerclass, workerclass.PATH, debug=debug)
    else:
        raise ValueError, "get_server: Could not get server"
    return srv


