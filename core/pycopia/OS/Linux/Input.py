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
Interface to /dev/input/eventX devices. This module provides base classes and
constant values for accessing the Linux input interface. This includes
keyboard, mouse, joystick, and a general event interface.

"""

import sys, os, struct, time, fcntl

from pycopia.aid import Queue

INT = "i"
INT2 = "ii"
INT5 = "iiiii"
SHORT = "h"
USHORT = "H"
SHORT4 = "hhhh"

# Initialize the ioctl constants
from pycopia.OS.Linux.IOCTL import _IOC, _IO, _IOW, _IOR, _IOC_READ
# taken from /usr/include/linux/input.h

EVIOCGVERSION   = _IOR(69, 0x01, INT)           # get driver version */
EVIOCGID        = _IOR(69, 0x02, SHORT4)        # get device ID */
EVIOCGREP       = _IOR(69, 0x03, INT2)          # get repeat settings */
EVIOCSREP       = _IOW(69, 0x03, INT2)          # set repeat settings */
EVIOCGKEYCODE   = _IOR(69, 0x04, INT2)          # get keycode */
EVIOCSKEYCODE   = _IOW(69, 0x04, INT2)          # set keycode */
EVIOCGKEY       = _IOR(69, 0x05, INT2)          # get key value */
EVIOCGNAME      = _IOC(_IOC_READ, 69, 0x06, 255)# get device name */
EVIOCRMFF       = _IOW(69, 0x81, INT)           # Erase a force effect */
EVIOCSGAIN      = _IOW(69, 0x82, USHORT)        # Set overall gain */
EVIOCSAUTOCENTER= _IOW(69, 0x83, USHORT)        # Enable or disable auto-centering */
EVIOCGEFFECTS   = _IOR(69, 0x84, INT)           # Report number of effects playable at the same time */
# XXX
#EVIOCGBIT(ev,len)= _IOC(_IOC_READ, 69, 0x20 + ev, len) # get event bits */
#EVIOCGABS(abs) = _IOR(69, 0x40 + abs, "iiiii")     # get abs value/limits */
#EVIOCSFF       = _IOC(_IOC_WRITE, 69, 0x80, sizeof(struct ff_effect))  # send a force effect to a force feedback device */

# these take parameters.
def EVIOCGBIT(ev, len):
    return _IOC(_IOC_READ, 69, 0x20 + ev, len)  # get event bits */

def EVIOCGABS(abs):
    return _IOR(69, 0x40 + abs, INT5)       # get abs value/limits */

def EVIOCGSW(len):
    return _IOC(_IOC_READ, 69, 0x1b, len)   # get all switch states */

def EVIOCGLED(len):
    return _IOC(_IOC_READ, 69, 0x19, len)   #  get all LEDs */

#struct input_event {
#        struct timeval time; = {long seconds, long microseconds}
#        unsigned short type;
#        unsigned short code;
#        unsigned int value;
#};

EVFMT = "llHHi"
EVsize = struct.calcsize(EVFMT)

class Event(object):
    """This structure is the collection of data for the general event
    interface. You can create one to write to an event device. If you read from
    the event device using the EventDevice object you will get one of these.
    """
    def __init__(self, time=0.0, evtype=0, code=0, value=0):
        self.time = time # timestamp of the event in Unix time.
        self.evtype = evtype # even type (one of EV_* constants)
        self.code = code     # a code related to the event type
        self.value = value   # custom data - meaning depends on type above

    def __str__(self):
        return "Event:\n   time: %f\n evtype: 0x%x\n   code: 0x%x\n  value: 0x%x\n" % \
                    (self.time, self.evtype, self.code, self.value)

    def encode(self):
        tv_sec, tv_usec = divmod(self.time, 1.0)
        return struct.pack(EVFMT, long(tv_sec), long(tv_usec*1000000.0), self.evtype, self.code, self.value)

    def decode(self, ev):
        tv_sec, tv_usec, self.evtype, self.code, self.value = struct.unpack(EVFMT, ev)
        self.time = float(tv_sec) + float(tv_usec)/1000000.0

    def set(self, evtype, code, value):
        self.time = time.time()
        self.evtype = int(evtype)
        self.code = int(code)
        self.value = int(value)


class EventFile(object):
    """Read from a file containing raw recorded events."""
    def __init__(self, fname, mode="r"):
        self._fo = open(fname, mode)
        self._eventq = Queue()

    def read(self, amt=None): # amt not used, provided for compatibility.
        """Read a single Event object from stream."""
        if not self._eventq:
            if not self._fill():
                return None
        return self._eventq.pop()

    def readall(self):
        ev = self.read()
        while ev:
            yield ev
            ev = self.read()

    def _fill(self):
        raw = self._fo.read(EVsize * 32)
        if raw:
            for i in xrange(len(raw)/EVsize):
                ev = Event()
                ev.decode(raw[i*EVsize:(i+1)*EVsize])
                self._eventq.push(ev)
            return True
        else:
            return False


# base class for event devices. Subclass this for your specific device.
class EventDevice(object):
    DEVNAME = None # must match name string of device 
    def __init__(self, fname=None):
        self._fd = None
        self.name = ""
        self._eventq = Queue()
        self.idbus = self.idvendor = self.idproduct = self.idversion = None
        if fname:
            self._open(fname)

    def __str__(self):
        if self.idbus is None:
            self.get_deviceid()
        return "%s: bus=0x%x, vendor=0x%x, product=0x%x, version=0x%x" % \
            (self.name, self.idbus, self.idvendor, self.idproduct, self.idversion)

    def _fill(self):
        global EVsize
        try:
            raw = os.read(self._fd, EVsize * 32)
        except EOFError:
            self.close()
        else:
            if raw:
                for i in range(len(raw)/EVsize):
                    ev = Event()
                    ev.decode(raw[i*EVsize:(i+1)*EVsize])
                    self._eventq.push(ev)

    def open(self, start=0):
        assert self.DEVNAME is not None
        for d in range(start, 16):
            try:
                self._open("/dev/input/event%d" % (d,))
            except IOError:
                pass
            else:
                if self.name.startswith(self.DEVNAME):
                    break
                else:
                    self.close()

    def _open(self, filename):
        self._fd = os.open(filename, os.O_RDWR)
        name = fcntl.ioctl(self._fd, EVIOCGNAME, chr(0) * 256)
        self.name = name.replace(chr(0), '')

    def fileno(self):
        return self._fd

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            self.name = ""

    def read(self):
        if not self._eventq:
            self._fill()
        return self._eventq.pop()

    def readall(self):
        ev = self.read()
        while ev:
            yield ev
            ev = self.read()

    def write(self, evtype, code, value):
        ev = Event(0.0, evtype, code, value)
        return os.write(self._fd, ev.encode())

    def get_driverversion(self):
        ver = fcntl.ioctl(self._fd, EVIOCGVERSION, '\x00\x00\x00\x00')
        return struct.unpack(INT, ver)[0]

    def get_deviceid(self):
        ver = fcntl.ioctl(self._fd, EVIOCGID, '\x00\x00\x00\x00\x00\x00\x00\x00')
        self.idbus, self.idvendor, self.idproduct, self.idversion = struct.unpack(SHORT4, ver)
        return self.idbus, self.idvendor, self.idproduct, self.idversion

    def readable(self):
        return bool(self._fd)

    def writable(self):
        return False

    def priority(self):
        return False

    def handle_read_event(self):
        self._fill()

    def handle_write_event(self):
        pass

    def handle_priority_event(self):
        pass

    def handle_hangup_event(self):
        pass



