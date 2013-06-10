#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 1999-2012  Keith Dart <keith@dart.us.com>
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

"""Object oriented asynchronous IO.
"""

from __future__ import print_function

import sys, os
import select, signal, fcntl, struct
# the only signal module function that is exposed here. The rest are wrapped by
# Poll.
pause = signal.pause

EPOLLERR = select.EPOLLERR
EPOLLHUP = select.EPOLLHUP
EPOLLIN = select.EPOLLIN
EPOLLOUT = select.EPOLLOUT
EPOLLPRI = select.EPOLLPRI
# These are not implemented here
#EPOLLET = select.EPOLLET
#EPOLLONESHOT = select.EPOLLONESHOT

POLLNVAL = select.POLLNVAL

from errno import EINTR

from pycopia.aid import NULL


class AsyncIOException(Exception):
    pass

class UnregisterNow(AsyncIOException):
    def __init__(self, obj):
        self.obj = obj

class UnregisterFDNow(AsyncIOException):
    def __init__(self, fd):
        self.filedescriptor = fd

# fix up the os module to include more Linux/BSD constants.
os.ACCMODE = 3
# flag for ASYNC I/O support. Note cygwin/win32 does not support it.
try:
    O_ASYNC = getattr(os, "O_ASYNC")
except AttributeError:
    O_ASYNC = os.O_ASYNC = {
        "linux2":0o20000,
        "linux3":0o20000,
        "freebsd4":0x0040,
        "freebsd5":0x0040,  # ?
        "darwin":0x0040,
        "sunos5":0, # not supported
        }.get(sys.platform, 0)

# ioctl codes
FIONREAD = TIOCINQ = SIOCINQ = 0x541B
TIOCOUTQ = SIOCOUTQ = 0x5411

class Poll(object):
    """Object oriented interface to epoll.

    Register objects that implement the PollerInterface in the singleton instance.
    """
    def __init__(self):
        self.smap = {}
        self._fd_callbacks = {}
        self._idle_callbacks = {}
        self._idle_handle = 0
        self.pollster = select.epoll()
        self.closed = False
        fd = self.pollster.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)

    def __str__(self):
        return "Polling descriptors: %r" % (self.smap.keys(),)

    def __nonzero__(self):
        return bool(self.smap) or bool(self._fd_callbacks)

    __bool__ = __nonzero__

    def __iter__(self):
        return self.smap.values()

    def register(self, obj):
        flags = self._getflags(obj)
        if flags:
            fd = obj.fileno()
            self.pollster.register(fd, flags)
            self.smap[fd] = obj

    def is_registered(self, obj):
        return obj.fileno() in self.smap

    def modify(self, obj):
        fd = obj.fileno()
        if fd in self.smap:
            flags = self._getflags(obj)
            self.pollster.modify(fd, flags)

    def unregister(self, obj):
        fd = obj.fileno()
        try:
            del self.smap[fd]
        except KeyError:
            return
        try:
            self.pollster.unregister(fd)
        except IOError:
            print("unregister of inactive fd:", fd, file=sys.stderr)

    def register_fd(self, fd, flags, callback):
        self.pollster.register(fd, flags)
        self.smap[fd] = None
        self._fd_callbacks[fd] = callback

    def is_registered_fd(self, fd):
        return fd in self._fd_callbacks

    def unregister_fd(self, fd):
        try:
            del self.smap[fd]
        except KeyError:
            pass
        else:
            self.pollster.unregister(fd)
            return True
        try:
            del self._fd_callbacks[fd]
        except KeyError:
            pass
        else:
            self.pollster.unregister(fd)
            return True
        return False

    def register_idle(self, callback):
        self._idle_handle += 1
        self._idle_callbacks[self._idle_handle] = callback
        return self._idle_handle

    def unregister_idle(self, handle):
        try:
            del self._idle_callbacks[handle]
        except KeyError:
            return False
        return True

    def _run_idle(self):
        for callback in self._idle_callbacks.values():
            callback()

    def poll(self, timeout=-1.0):
        while 1:
            try:
                rl = self.pollster.poll(timeout)
            except IOError as why:
                if why.errno == EINTR:
                    self._run_idle()
                    continue
                else:
                    raise
            else:
                break
        for fd, flags in rl:
            try:
                hobj = self.smap[fd]
            except KeyError: # this should never happen, but let's be safe.
                continue
            if hobj is None: # signals simple callback
                self._fd_callbacks[fd]()
                continue
            try:
                if (flags & EPOLLERR):
                    hobj.error_handler()
                    continue
                if (flags & POLLNVAL):
                    self.unregister_fd(fd)
                    continue
                if (flags & EPOLLPRI):
                    hobj.pri_handler()
                if (flags & EPOLLIN):
                    hobj.read_handler()
                if (flags & EPOLLOUT):
                    hobj.write_handler()
                if (flags & EPOLLHUP):
                    hobj.hangup_handler()
            except UnregisterNow as unr:
                self.unregister(unr.obj)
            except UnregisterFDNow as unr:
                self.unregister_fd(unr.filedescriptor)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                ex, val, tb = sys.exc_info()
                hobj.exception_handler(ex, val, tb)

    def loop(self, timeout=5.0, callback=NULL):
        while self.smap:
            self.poll(timeout)
            self._run_idle()
            callback(self)

    def unregister_all(self):
        for obj in self.smap.values():
            self.unregister(obj)
        self._fd_callbacks = {}
        self._idle_callbacks = {}

    clear = unregister_all

    def _getflags(self, aiobj):
        flags = 0
        if aiobj.readable():
            flags = EPOLLIN
        if aiobj.writable():
            flags |= EPOLLOUT
        if aiobj.priority():
            flags |= EPOLLPRI
        return flags

    # A poller is itself selectable so may be nested in another Poll
    # instance. Therefore, supports the async interface itself.
    def fileno(self):
        return self.pollster.fileno()

    def close(self):
        if not self.closed:
            self.pollster.close()
            self.closed = True

    def readable(self):
        return bool(self.smap) or bool(self._fd_callbacks)

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        self.poll()

    def error_handler(self):
        print("Poll error", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("Poll exception: %s (%s)" % (ex, val), file=sys.stderr)


# Mixin for objects that only want to define a few methods for a class
# that the Poll object needs.
class PollerInterface(object):

    def fileno(self):
        return -1

    def readable(self):
        return False

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        pass

    def write_handler(self):
        pass

    def pri_handler(self):
        pass

    def hangup_handler(self):
        pass

    def error_handler(self):
        pass

    def exception_handler(self, ex, val, tb):
        print("Poller exception: %s (%s)" % (ex, val), file=sys.stderr)


# Main poller is a singleton instance, in the module scope.

# Automatic, lazy instantiation of poller object when first referenced.
class _Poll_builder(object):

    def __getattr__(self, name):
        global poller
        if isinstance(poller, _Poll_builder):
            poller = Poll()
        return getattr(poller, name)

poller = _Poll_builder()


# Default setup is to poll our files when we get a SIGIO. This is done since
# Python does not expose the siginfo structure. In the future, we could write a
# new signal module that does expose the siginfo structure.

class SIGIOHandler(object):
    def __init__(self):
        self.handlers = {}
        self.on()

    def on(self):
        signal.signal(signal.SIGIO, self)
        signal.siginterrupt(signal.SIGIO, True)

    def off(self):
        signal.signal(signal.SIGIO, signal.SIG_IGN)

    def get(self, handle):
        cb, args = self.handlers.get(handle, (None, None))
        return cb

    def register(self, callback, *args):
        handle = id(callback)
        self.handlers[handle] = (callback, args)
        return handle

    def unregister(self, handle):
        cb = self.handlers.get(handle, None)
        if cb:
            del self.handlers[handle]

    def __call__(self, sig, frame):
        for h, args in self.handlers.values():
            h(*args)


# Singleton instance of SIGIO handler. It's optional.
manager = None

def start_sigio():
    global manager
    if manager is None:
        manager = SIGIOHandler()
        # add the local poller instance to the signal handler.
        manager.register(lambda: poller.poll(0))
    else:
        manager.on()

def stop_sigio():
    global manager
    if manager is not None:
        manager.off()


def set_asyncio(fd_or_obj):
    """Sets io object to use SIGIO."""
    if type(fd_or_obj) is int:
        fd = fd_or_obj
    else:
        fd = fd_or_obj.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags |= O_ASYNC
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
    fcntl.fcntl(fd, fcntl.F_SETOWN, os.getpid())


def register_asyncio(obj):
    set_asyncio(obj)
    poller.register(obj)

register = register_asyncio


def unregister_asyncio(obj):
    poller.unregister(obj)

unregister = unregister_asyncio


# Socket protocol handlers

CLOSED = 0
CONNECTED = 1

class AsyncServerHandler(PollerInterface):

    def __init__(self, sock, workerclass):
        self._sock = sock
        self._workerclass = workerclass
        sock.setblocking(0)
        poller.register(self)

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        if self._sock is not None:
            poller.unregister(self)
            s = self._sock
            self._sock = None
            s.close()

    closed = property(lambda self: bool(self._sock))

    def readable(self):
        return True

    def writable(self):
        return False

    def priority(self):
        return True

    def read_handler(self):
        conn, addr = self._sock.accept()
        conn.setblocking(0)
        h = self._workerclass(conn, addr)
        poller.register(h)
        return h


class AsyncWorkerHandler(PollerInterface):
    def __init__(self, sock, addr):
        self._sock = sock
        self._rem_address = addr
        self._state = CONNECTED
        self._buf = ""
        self.initialize()

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        if self._sock is not None:
            poller.unregister(self)
            s = self._sock
            self._sock = None
            s.close()
            self._state = CLOSED

    closed = property(lambda self: self._state == CLOSED)

    def write(self, data):
        self._buf += data
        poller.modify(self)
        return len(data)

    def inq(self):
        """How many bytes are still in the kernel's input buffer?"""
        return struct.unpack("I", fcntl.ioctl(self._sock.fileno(), SIOCINQ, '\0\0\0\0'))[0]

    def outq(sock):
        """How many bytes are still in the kernel's output buffer?"""
        return struct.unpack("I", fcntl.ioctl(self._sock.fileno(), SIOCOUTQ, '\0\0\0\0'))[0]

    def readable(self):
        return self._state == CONNECTED

    def writable(self):
        return self._state == CONNECTED and bool(self._buf)

    def priority(self):
        return self._state == CONNECTED

    def hangup_handler(self):
        poller.unregister(self)
        self.close()

    def error_handler(self):
        print("AsyncWorkerHandler error", file=sys.stderr)
        poller.unregister(self)

    def write_handler(self):
        writ = self._sock.send(self._buf)
        self._buf = self._buf[writ:]
        poller.modify(self)

    ###### overrideable async interface  ####
    def initialize(self):
        pass

    def read_handler(self, size=4096):
        data = self._sock.recv(size)
        print("AsyncWorkerHandler: unhandled read:", data, file=sys.stderr)

    def pri_handler(self):
        print("AsyncWorkerHandler: unhandled pri", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("AsyncWorkerHandler error: %s (%s)" % (ex, val), file=sys.stderr)


class AsyncClientHandler(PollerInterface):
    def __init__(self, sock, addr):
        self._sock = sock
        self._rem_address = addr
        self._state = CONNECTED
        self._buf = ""
        self.initialize()
        poller.register(self)

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        if self._sock is not None:
            poller.unregister(self)
            s = self._sock
            self._sock = None
            s.close()
            self._state = CLOSED

    closed = property(lambda self: self._state == CLOSED)

    def write(self, data):
        self._buf += data
        poller.modify(self)
        return len(data)

    def readable(self):
        return self._state == CONNECTED

    def writable(self):
        return self._state == CONNECTED and bool(self._buf)

    def priority(self):
        return self._state == CONNECTED

    def write_handler(self):
        writ = self._sock.send(self._buf)
        self._buf = self._buf[writ:]
        poller.modify(self)

    def hangup_handler(self):
        poller.unregister(self)
        self.close()

    ###### overrideable async interface  ####
    def error_handler(self):
        print("AsyncClient error", file=sys.stderr)
        poller.unregister(self)

    def initialize(self):
        pass

    def read_handler(self):
        data = self._sock.recv(4096)
        print("AsyncClient read:", data, file=sys.stderr)

    def pri_handler(self):
        print("AsyncClient pri", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("AsyncClient exception: %s (%s)" % (ex, val), file=sys.stderr)


class AsyncIOHandler(PollerInterface):

    def __init__(self, fo):
        self._fo = fo
        self._readable = "r" in fo.mode
        self._writable = "w" in fo.mode
        self._buf = ""
        poller.register(self)

    def close(self):
        if self._fo is not None:
            poller.unregister(self)
            #fo = self._fo
            self._fo = None

    def fileno(self):
        return self._fo.fileno()

    def write(self, data):
        self._buf += data
        poller.modify(self)
        return len(data)

    def initialize(self):
        pass

    def readable(self):
        return self._readable

    def writable(self):
        return self._writable and bool(self._buf)

    def write_handler(self):
        writ = self._fo.write(self._buf)
        self._buf = self._buf[writ:]
        poller.modify(self)

    def read_handler(self):
        print("AsyncIOHandler unhandled read", file=sys.stderr)

    def error_handler(self):
        print("AsyncIOHandler unhandled error", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("AsyncIOHandler exception: %s (%s)" % (ex, val), file=sys.stderr)

