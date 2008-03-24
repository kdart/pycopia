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

import sys, os
import select, signal, fcntl
# the only signal module function that is exposed here. The rest are wrapped by
# Poll.
pause = signal.pause
POLLERR = select.POLLERR
POLLNVAL = select.POLLNVAL
POLLHUP = select.POLLHUP
POLLIN = select.POLLIN
POLLOUT = select.POLLOUT
POLLPRI = select.POLLPRI

from errno import EINTR, EBADF

from pycopia.aid import NULL

class ExitNow(Exception):
    pass

# fix up the os module to include more Linux/BSD constants.
os.ACCMODE = 03
# flag for ASYNC I/O support. Note cygwin/win32 does not support it.
O_ASYNC = os.O_ASYNC = {
    "linux1":020000, # ?
    "linux2":020000, 
    "freebsd4":0x0040, 
    "freebsd5":0x0040,  # ?
    "darwin":0x0040,
    "sunos5":0, # not supported
    }.get(sys.platform, 0)


class Poll(object):
    """
    """
    def __init__(self):
        self.smap = {}
        self.pollster = select.poll()

    def __str__(self):
        return "Polling descriptors: %r" % (self.smap.keys())

    def register(self, obj):
        flags = self._getflags(obj)
        if flags:
            fd = obj.fileno()
            self.smap[fd] = obj
            self.pollster.register(fd, flags)

    def unregister(self, obj):
        fd = obj.fileno()
        try:
            del self.smap[fd]
        except KeyError:
            return
        try:
            self.pollster.unregister(fd)
        except KeyError:
            pass

    def poll(self, timeout=-1):
        timeout = int(timeout*1000) # the poll method time unit is milliseconds
        while 1:
            try:
                rl = self.pollster.poll(timeout)
            except select.error, why:
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
                if (flags  & POLLERR) or (flags & POLLNVAL):
                    self.unregister_fd(fd)
                    hobj.hangup_handler()
                    continue
                if (flags & POLLHUP):
                    self.unregister_fd(fd)
                    hobj.hangup_handler()
                    continue
                if (flags & POLLIN):
                    hobj.read_handler()
                if (flags & POLLOUT):
                    hobj.write_handler()
                if (flags & POLLPRI):
                    hobj.pri_handler()
            except:
                ex, val, tb = sys.exc_info()
                hobj.error_handler(ex, val, tb)

    # note that if you use this, unregister the default SIGIO handler
    def loop(self, timeout=10, callback=NULL):
        while self.smap:
            self.poll(timeout)
            callback()

    def unregister_all(self):
        for obj in self.smap.values():
            self.unregister(obj)

    clear = unregister_all

    def _getflags(self, hobj):
        flags = 0
        if hobj.readable():
            flags = POLLIN
        if hobj.writable():
            flags |= POLLOUT
        if hobj.priority():
            flags |= POLLPRI
        return flags

    def _removebad(self):
        for fd, hobj in self.smap.items():
            try:
                os.fstat(fd)
            except OSError:
                del self.smap[fd]
                try:
                    self.pollster.unregister(fd)
                except KeyError:
                    pass



# Mixin for objects that only want to define a few methods for a class
# that the Poll object needs.
class PollerInterface(object):

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

    def error_handler(self, ex, val, tb):
        print >>sys.stderr, "Poller error: %s (%s)" % (ex, val)


# Default setup is to poll our files when we get a SIGIO. This is done since
# Python does not expose the siginfo structure. In the future, we could write a
# new signal module that does expose the siginfo structure.

# this handler manages a chain of registered callback functions. 
class SIGIOHandler(object):
    def __init__(self):
        self.handlers = {}
        self.on()
    
    def on(self):
        signal.signal(signal.SIGIO, self)

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

def get_manager():
    global manager
    return manager

def set_asyncio(obj):
    if type(obj) is int:
        fd = obj
    elif hasattr(obj, "fileno"):
        fd = obj.fileno()
    else:
        raise ValueError, "set_asyncio: needs integer file descriptor, or object with fileno() method."
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags |= O_ASYNC
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
    fcntl.fcntl(fd, fcntl.F_SETOWN, os.getpid())

def register_asyncio(obj):
    set_asyncio(obj)
    poller.register(obj)
register = register_asyncio

################################################################
# DirectoryNotifier encapslates the code required for watching directory entry
# contents. Subclass this and override the entry_added() and entry_removed()
# methods. then, instantiate it with a directory name, and register it with the
# sighandler instance.  NOTE: this only works with Python 2.2 or greater on
# Linux. 
# Example:
#   dn = DirectoryNotifier(os.environ["HOME"])
#   manager.register(dn)

class DirectoryNotifier(object):
    def __init__(self, dirname):
        if not os.path.isdir(dirname):
            raise RuntimeError, "you can only watch a directory."
        self.dirname = dirname
        self.fd = os.open(dirname, 0)
        self.currentcontents = os.listdir(dirname)
        self.oldsig = fcntl.fcntl(self.fd, fcntl.F_GETSIG)
        fcntl.fcntl(self.fd, fcntl.F_SETSIG, 0)
        fcntl.fcntl(self.fd, fcntl.F_NOTIFY, fcntl.DN_DELETE|fcntl.DN_CREATE|fcntl.DN_MULTISHOT)
        self.initialize() # easy initializer for subclasses
    
    def fileno(self):
        return self.fd

    def __del__(self):
#       fcntl.fcntl(self.fd, fcntl.F_SETSIG, self.oldsig)
        os.close(self.fd)
    
    def __str__(self):
        return "%s watching %s" % (self.__class__.__name__, self.dirname)

    def __call__(self):
        newcontents = os.listdir(self.dirname)
        if len(newcontents) > len(self.currentcontents):
            new = filter(lambda item: item not in self.currentcontents, newcontents)
            self.entry_added(new)
        elif len(newcontents) < len(self.currentcontents):
            rem = filter(lambda item: item not in newcontents, self.currentcontents)
            self.entry_removed(rem)
        else:
            self.no_change()
        self.currentcontents = newcontents

    # override these in a subclass
    def initialize(self):
        pass

    def entry_added(self, added):
        print added, "added to", self.dirname

    def entry_removed(self, removed):
        print removed, "removed from", self.dirname

    def no_change(self):
        pass


poller = Poll()

def get_poller():
    global poller
    return poller

# a singleton instance of the SIGIOHandler. Usually, users of this module only
# have to register a DirectoryNotifier object here. Other objects (Dispatcher
# objects) are registered with the poller (which is already set up to be called
# when SIGIO occurs). But you may add your own hooks to it.
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


