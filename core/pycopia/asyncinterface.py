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
Interface definition that defines the interace to asycio module objects.

"""

import os, fcntl

from pycopia.aid import NULL


def _default_error_handler(ex, val, tb):
    print >>sys.stderr, "*** unhandled error: %s (%s)" % (ex, val)

# there will be one HandlerMethods holder per file descriptor
# This exists so that objects can have multiple file descriptors and handler
# methods (primarily coprocesses with pipes).
class HandlerMethods(object):
    __slots__ = [
        "fd", "readable", "read_handler", 
        "writable", "write_handler", 
        "priority", "pri_handler", 
        "hangup_handler", "error_handler", ]

    def __init__(self, fd, readable=NULL, read_handler=NULL, \
                           writable=NULL, write_handler=NULL, \
                           priority=NULL, pri_handler=NULL, \
                           hangup_handler=NULL, \
                           error_handler=_default_error_handler):
        self.fd = fd
        self.readable = readable
        self.read_handler = read_handler
        self.writable = writable
        self.write_handler = write_handler
        self.priority = priority
        self.pri_handler = pri_handler
        self.hangup_handler = hangup_handler
        self.error_handler = error_handler
    
    def fileno(self):
        return self.fd


# a mixin class that defines the asyncio object interface.
# your class should define _read and _write to do the actual read and write to
# the file-like object.
class AsyncInterface(object):
    def __init__(self):
        self._readbuf = ""
        self._writebuf = ""
        self._pribuf = ""

    def fileno(self):
        return None

    def get_handlers(self):
        """Returns a list of asyncio.HandlerMethods objects. One for each file
        descriptor that the object handles. This takes priority over fileno() method."""
        return [get_default_handler(self)]

    # data ready indicators
    def readable(self):
        """Returns a boolean indicating whether or not the object wants to read
        data. """
        return True

    def writable(self):
        """Return a boolean indicating whether or not this object has data
        ready for writing."""
        return bool(self._writebuf)

    def priority(self):
        """Return a boolean indicating whether or not this object wants to read
        priority (OOB) data.  """
        return False

    def handle_read_event(self):
        """Callback gets called when file descriptor has data for reading."""
        pass

    def handle_write_event(self):
        """Callback that gets called when file descriptor is available for
        writing."""
        writ = self._write(data)
        self._writebuf = self._writebuf[writ:]

    def handle_priority_event(self):
        """Callback that gets called when priority (OOB) data is ready for
        reading."""
        pass

    def handle_hangup_event(self):
        """Callback that gets called when file desriptor closes for some
        reason."""
        pass

    def read(self, N=2147483646):
        """Call this to read some data."""
        return self._read(N)

    def write(self, data):
        self._writebuf += str(data)

    def handle_error(self, ex, val, tb):
        """callback gets called with exception, exception instance, and a
        traceback when an error occurs."""
        pass


def get_default_handler(obj):
    try:
        fd = obj.fileno()
        hobj = HandlerMethods(fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        if flags & os.O_RDWR:
            hobj.readable = obj.readable
            hobj.read_handler = obj.handle_read_event
            hobj.writable = obj.writable
            hobj.write_handler = obj.handle_write_event
        elif flags & os.O_WRONLY:
            hobj.writable = obj.writable
            hobj.write_handler = obj.handle_write_event
        elif not (flags & os.ACCMODE): # read only
            hobj.readable = obj.readable
            hobj.read_handler = obj.handle_read_event
    except AttributeError:
        return None
    try:
        hobj.priority = obj.priority
    except AttributeError:
        hobj.priority = NULL
    try:
        hobj.pri_handler = obj.handle_priority_event
    except AttributeError:
        hobj.pri_handler = NULL
    try:
        hobj.hangup_handler = obj.handle_hangup_event
    except AttributeError:
        hobj.hangup_handler = NULL
    try:
        hobj.error_handler = obj.handle_error
    except AttributeError:
        hobj.error_handler = NULL
    return hobj



def _test(argv):
    pass 

if __name__ == "__main__":
    import sys
    _test(sys.argv)

