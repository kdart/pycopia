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

from pycopia.asyncinterface import HandlerMethods, get_default_handler
from pycopia.aid import NULL

class ExitNow(Exception):
    pass


class Poll(object):
    """
Poll()
An object wrapper for the poll() system call. Use the register() method to add
instances of the Dispatcher class or subclass. Call the poll() method to start
polling, with a timeout. Default is no timeout.

    """
    def __init__(self):
        self.smap = {}
        self.pollster = select.poll()

    def __str__(self):
        return "Poll is polling descriptors: %r" % (self.smap.keys())
    
    def _getflags(self, hobj):
        flags = 0
        if hobj.readable():
            flags = POLLIN
        if hobj.writable():
            flags = flags | POLLOUT
        if hobj.priority():
            flags = flags | POLLPRI
        return flags

    def _reregister(self):
        for fd, hobj in self.smap.items():
            flags = self._getflags(hobj)
            if flags:
                self.pollster.register(fd, flags)
            else:
                try:
                    self.pollster.unregister(fd)
                except KeyError:
                    pass

    def register(self, obj):
        try:
            handlers = obj.get_handlers() # might not have this...
            if handlers:
                for hobj in handlers:
                    self.register_handler(hobj)
                return
        except AttributeError:
            pass
        if hasattr(obj, "fileno"):
            hobj = get_default_handler(obj)
            if hobj:
                self.register_handler(hobj)
                return
        raise ValueError, "Poll.register: must be a file-like object or object with get_handlers() method."

    def register_handler(self, hobj):
        set_asyncio(hobj.fd)
        self.smap[hobj.fd] = hobj

    def unregister(self, obj):
        if hasattr(obj, "get_handlers"):
            for hobj in obj.get_handlers():
                self.unregister_fd(hobj.fd)
        elif hasattr(obj, "fileno"):
            self.unregister_fd(obj.fileno())
    
    def unregister_fd(self, fd):
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
                if why[0] == EBADF:
                    self._reregister() # remove objects that might have went away
                    continue
                elif why[0] == EINTR:
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
                    raise ExitNow, "Error while polling: %s" % (fd,)
                if (flags  & POLLHUP):
                    self.unregister_fd(fd)
                    hobj.hangup_handler()
                    continue
                if (flags  & POLLIN):
                    hobj.read_handler()
                if (flags & POLLOUT):
                    hobj.write_handler()
                if (flags & POLLPRI):
                    hobj.pri_handler()
            except ExitNow, val:
                pass
                #raise ExitNow, val
            except:
                ex, val, tb = sys.exc_info()
                hobj.error_handler(ex, val, tb)
        self._reregister()

    # note that if you use this, unregister the default SIGIO handler
    def loop(self, timeout=10, callback=NULL):
        while self.smap:
            self.poll(timeout)
            callback()

    def unregister_all(self):
        for x in self.smap.keys():
            self.unregister_fd(x)
    clear = unregister_all


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
    flags |= os.O_ASYNC
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


# a singleton instance of Poll. Usually, only this poller is used in a program
# using this module.
try:
    poller
except NameError:
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


