#!/usr/bin/python2.6
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 1999-2011  Keith Dart <keith@dart.us.com>
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
import select, signal, fcntl
# the only signal module function that is exposed here. The rest are wrapped by
# Poll.
pause = signal.pause

EPOLLERR = select.EPOLLERR
EPOLLHUP = select.EPOLLHUP
EPOLLIN = select.EPOLLIN
EPOLLOUT = select.EPOLLOUT
EPOLLPRI = select.EPOLLPRI

POLLNVAL = select.POLLNVAL

from errno import EINTR, EBADF

from pycopia.aid import NULL

class ExitNow(Exception):
    pass

# fix up the os module to include more Linux/BSD constants.
os.ACCMODE = 03
# flag for ASYNC I/O support. Note cygwin/win32 does not support it.
try:
    O_ASYNC = getattr(os, "O_ASYNC")
except AttributeError:
    O_ASYNC = os.O_ASYNC = {
        "linux3":020000, # ?
        "linux2":020000,
        "linux3":020000,
        "freebsd4":0x0040,
        "freebsd5":0x0040,  # ?
        "darwin":0x0040,
        "sunos5":0, # not supported
        }.get(sys.platform, 0)


class Poll(object):
    """Object oriented interface to epoll.

    Register objects that implement the PollerInterface in the singleton instance.
    """
    def __init__(self):
        self.smap = {}
        self.pollster = select.epoll()
        fd = self.pollster.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(fd, fcntl.F_SETFD, flags)

    def __str__(self):
        return "Polling descriptors: %r" % (self.smap.keys(),)

    def __bool__(self):
        return bool(self.smap)

    def __iter__(self):
        return self.smap.values()

    def register(self, obj):
        flags = self._getflags(obj)
        if flags:
            fd = obj.fileno()
            self.pollster.register(fd, flags)
            self.smap[fd] = obj

    def register_fd(self, fd, flags):
        self.pollster.register(fd, flags)
        self.smap[fd] = None

    def modify(self, obj):
        fd = obj.fileno()
        if fd in self.smap:
            flags = self._getflags(obj)
            self.pollster.modify(fd, flags)

    def unregister(self, obj):
        self.unregister_fd(obj.fileno())

    def unregister_fd(self, fd):
        try:
            del self.smap[fd]
        except KeyError:
            return
        self.pollster.unregister(fd)

    def poll(self, timeout=-1.0):
        while 1:
            try:
                rl = self.pollster.poll(timeout)
            except IOError as why:
                if why[0] == EINTR:
                    continue
                elif why[0] == EBADF:
                    self._removebad() # remove objects that might have went away
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
            try:
                if (flags  & EPOLLERR) or (flags & POLLNVAL):
                    hobj.error_handler()
                    continue
                if (flags & EPOLLHUP):
                    hobj.hangup_handler()
                    continue
                if (flags & EPOLLPRI):
                    hobj.pri_handler()
                if (flags & EPOLLIN):
                    hobj.read_handler()
                if (flags & EPOLLOUT):
                    hobj.write_handler()
            except (ExitNow, KeyboardInterrupt, SystemExit):
                raise
            except:
                ex, val, tb = sys.exc_info()
                hobj.exception_handler(ex, val, tb)

    # note that if you use this, unregister the default SIGIO handler
    def loop(self, timeout=-1.0, callback=NULL):
        while self.smap:
            self.poll(timeout)
            callback(self)

    def unregister_all(self):
        for obj in self.smap.values():
            self.unregister(obj)

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

    def _removebad(self):
        for fd, aiobj in self.smap.items():
            try:
                os.fstat(fd)
            except OSError:
                self.pollster.unregister(fd)
                del self.smap[fd]

    # A poller is itself selectable so may be nested in another Poll
    # instance. Therefore, supports the async interface itself.
    def fileno(self):
        return self.pollster.fileno()

    def readable(self):
        return bool(self.smap)

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        self.poll()

    def error_handler(self):
        print("Pollster error", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("Poller error: %s (%s)" % (ex, val), file=sys.stderr)


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
        print("Poller error: %s (%s)" % (ex, val), file=sys.stderr)


# Singleton instance
poller = Poll()



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

def get_manager():
    global manager
    return manager

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
        poller.unregister(self)

    def write_handler(self):
        writ = self._sock.send(self._buf)
        self._buf = self._buf[writ:]
        poller.modify(self)

    ###### overrideable async interface  ####
    def initialize(self):
        pass

    def read_handler(self):
        data = self._sock.recv(4096)
        print("unhandled read:", data, file=sys.stderr)

    def pri_handler(self):
        print("unhandled pri", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("Poller error: %s (%s)" % (ex, val), file=sys.stderr)


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

    def error_handler(self):
        poller.unregister(self)

    ###### overrideable async interface  ####
    def initialize(self):
        pass

    def read_handler(self):
        data = self._sock.recv(4096)
        print("unhandled read:", data, file=sys.stderr)

    def pri_handler(self):
        print("unhandled pri", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("Poller error: %s (%s)" % (ex, val), file=sys.stderr)


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
        print("unhandled read", file=sys.stderr)

    def error_handler(self):
        print("unhandled error", file=sys.stderr)

    def exception_handler(self, ex, val, tb):
        print("Poller error: %s (%s)" % (ex, val), file=sys.stderr)


