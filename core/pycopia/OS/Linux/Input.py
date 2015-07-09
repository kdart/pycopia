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

SIZEOF_INT2 = struct.calcsize(INT2)

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
EVIOCGPHYS      = _IOC(_IOC_READ, 69, 0x07, 255)# get physical location */
EVIOCGUNIQ      = _IOC(_IOC_READ, 69, 0x08, 255)# get unique identifier */
EVIOCRMFF       = _IOW(69, 0x81, INT)           # Erase a force effect */
EVIOCSGAIN      = _IOW(69, 0x82, USHORT)        # Set overall gain */
EVIOCSAUTOCENTER= _IOW(69, 0x83, USHORT)        # Enable or disable auto-centering */
EVIOCGEFFECTS   = _IOR(69, 0x84, INT)           # Report number of effects playable at the same time */
EVIOCGRAB       = _IOW(69, 0x90, INT)          # Grab/Release device */

# these take parameters.
def EVIOCGBIT(evtype, len=255):
    return _IOC(_IOC_READ, 69, 0x20 + evtype, len)  # get event bits */

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

EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_SND = 0x12
EV_REP = 0x14
EV_FF = 0x15
EV_PWR = 0x16
EV_FF_STATUS = 0x17
EV_MAX = 0x1f

class Features(object):
    """Contains a set of base features. May be actual set as returned by a
    feature request, or a desired set to find.
    """
    NAMES = {
        EV_SYN: "Sync",
        EV_KEY: "Keys or Buttons",
        EV_REL: "Relative Axes",
        EV_ABS: "Absolute Axes",
        EV_MSC: "Miscellaneous",
        EV_SW: "Switches",
        EV_LED: "Leds",
        EV_SND: "Sound",
        EV_REP: "Repeat",
        EV_FF: "Force Feedback",
        EV_PWR: "Power Management",
        EV_FF_STATUS: "Force Feedback Status",
    }

    def __init__(self, bits=0):
        self._bits = bits

    def has_keys(self):
        return (self._bits >> EV_KEY) & 1

    def has_leds(self):
        return (self._bits >> EV_LED) & 1

    def has_sound(self):
        return (self._bits >> EV_SND) & 1

    def has_relative_axes(self):
        return (self._bits >> EV_REL) & 1

    def has_absolute_axes(self):
        return (self._bits >> EV_ABS) & 1

    def has_misc(self):
        return (self._bits >> EV_MSC) & 1

    def has_switches(self):
        return (self._bits >> EV_SW) & 1

    def has_repeat(self):
        return (self._bits >> EV_REP) & 1

    def has_forcefeedback(self):
        return (self._bits >> EV_FF) & 1

    def has_forcefeedback_status(self):
        return (self._bits >> EV_FF_STATUS) & 1

    def has_power(self):
        return (self._bits >> EV_PWR) & 1

    def _make_set(self):
        featureset = set()
        bits = self._bits
        for bit in (EV_KEY, EV_REL, EV_ABS, EV_MSC, EV_SW, EV_LED, EV_SND, EV_REP, EV_FF, EV_PWR, EV_FF_STATUS):
            if (bits >> bit) & 1:
                featureset.add(bit)
        return featureset

    def match(self, other):
        pass #XXX

    def __str__(self):
        s = []
        bits = self._bits
        for bit, name in self.NAMES.items():
            if (bits >> bit) & 1:
                s.append(name)
        return ", ".join(s)


class Event(object):
    """This structure is the collection of data for the general event
    interface. You can create one to write to an event device. If you read from
    the event device using a subclass of the EventDevice object you will get one of these.
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
            self.open(fname)
        self.initialize()

    def __str__(self):
        if self.idbus is None:
            self.get_deviceid()
        return "%s: bus=0x%x, vendor=0x%x, product=0x%x, version=0x%x\n   %s" % \
            (self.name, self.idbus, self.idvendor, self.idproduct, self.idversion, self.get_features())

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

    def find(self, start=0, name=None):
        name = name or self.DEVNAME
        assert name is not None, "EventDevice: no name to find"
        for d in range(start, 16):
            filename = "/dev/input/event%d" % (d,)
            if os.path.exists(filename):
                try:
                    self.open(filename)
                except (OSError, IOError): # probably no permissions
                    pass
                else:
                    if name in self.name:
                        return
        self.close()
        raise IOError("Input device %r not found." % (name,))

    def open(self, filename):
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

    def get_features(self):
        caps = fcntl.ioctl(self._fd, EVIOCGBIT(0), '\x00\x00\x00\x00')
        caps = struct.unpack(INT, caps)[0]
        return Features(caps)

    def readable(self):
        return bool(self._fd)

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        self._fill()

    def write_handler(self):
        pass

    def pri_handler(self):
        pass

    def hangup_handler(self):
        pass

    def initialize(self):
        pass


def get_device_names(start=0):
    """Returns a list of tuples containing (index, devicename).
    """
    names = []
    for d in range(start, 16):
        filename = "/dev/input/event%d" % (d,)
        if os.path.exists(filename):
            try:
                    fd = os.open(filename, os.O_RDWR)
                    try:
                        name = fcntl.ioctl(fd, EVIOCGNAME, chr(0) * 256)
                    finally:
                        os.close(fd)
                    name = name.replace(chr(0), '')
            except (OSError, IOError): # probably no permissions
                continue
            else:
                names.append((d, name))
    return names


def get_devices(start=0):
    devs = []
    for d in range(start, 16):
        filename = "/dev/input/event%d" % (d,)
        if os.path.exists(filename):
            devs.append(EventDevice(filename))
    return devs


if __name__ == "__main__":
    for dev in get_devices():
        print dev
