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
rtc.py provides access the the real time clock. 


from the Linux Documentation:

All PCs (even Alpha machines) have a Real Time Clock built into them.
Usually they are built into the chipset of the computer, but some may
actually have a Motorola MC146818 (or clone) on the board. This is the
clock that keeps the date and time while your computer is turned off.

However it can also be used to generate signals from a slow 2Hz to a
relatively fast 8192Hz, in increments of powers of two. These signals
are reported by interrupt number 8. (Oh! So *that* is what IRQ 8 is
for...) It can also function as a 24hr alarm, raising IRQ 8 when the
alarm goes off. The alarm can also be programmed to only check any
subset of the three programmable values, meaning that it could be set to
ring on the 30th second of the 30th minute of every hour, for example.
The clock can also be set to generate an interrupt upon every clock
update, thus generating a 1Hz signal.

For more information, see /usr/src/linux/Documentation/rtc.txt

"""

import os, fcntl, struct


RTC_IS_OPEN = 0x01    # means /dev/rtc is in use
RTC_TIMER_ON = 0x02   # missed irq timer active

# status bits
RTC_IRQF = 0x80 # any of the following 3 is active
RTC_PF = 0x40
RTC_AF = 0x20
RTC_UF = 0x10

_UL = struct.pack("L", 0L)
_UL_len = len(_UL)

class rtc_time(object):
    FMT = "9i"
    epoch = 1900
    def __init__(self, _rtc_time):
        if _rtc_time is None:
            self.tm_sec, self.tm_min, self.tm_hour, self.tm_mday, self.tm_mon, \
            self.tm_year, self.tm_wday, self.tm_yday, self.tm_isdst \
                = 0, 0, 0, 0, 0, 0, 0, 0, 0
        else:
            self.tm_sec, self.tm_min, self.tm_hour, self.tm_mday, self.tm_mon, \
            self.tm_year, self.tm_wday, self.tm_yday, self.tm_isdst \
                = struct.unpack(self.FMT, _rtc_time)

    def __repr__(self):
        return struct.pack(self.FMT, self.tm_sec, self.tm_min, self.tm_hour,
            self.tm_mday, self.tm_mon, self.tm_year, self.tm_wday,
            self.tm_yday, self.tm_isdst)

    def __str__(self):
        return "%02d:%02d:%02d %02d/%02d/%d" % (self.tm_hour, self.tm_min, self.tm_sec, 
        self.tm_mon+1, self.tm_mday, self.tm_year + self.epoch)
        # these are not supplied by the driver
        #self.tm_wday, self.tm_yday, self.tm_isdst)

    def __int__(self):
        return self.tm_sec + self.tm_min*60 + self.tm_hour*3600 + \
                self.tm_mday + self.tm_mon + self.tm_year # XXX

    def __iadd__(self, secs):
        self.add_seconds(int(secs))

    def __sub__(self, other):
        new = rtc_time(None)
        new.tm_sec = self.tm_sec - other.tm_sec
        new.tm_min = self.tm_min - other.tm_min
        new.tm_hour = self.tm_hour - other.tm_hour
        new.tm_mday = self.tm_mday - other.tm_mday
        new.tm_mon = self.tm_mon - other.tm_mon
        new.tm_year = self.tm_year - other.tm_year
        new.tm_wday = None # XXX
        new.tm_yday = self.tm_yday - other.tm_yday
        new.tm_isdst = self.tm_isdst
        return new

    def add_seconds(self, secs):
        carry, self.tm_sec = divmod(self.tm_sec+secs, 60)
        if carry: # minutes
            carry, self.tm_min = divmod(self.tm_min+carry, 60)
            if carry: # hours
                carry, self.tm_hour = divmod(self.tm_hour+carry, 24)
                if carry: # days
                    raise ValueError, "fixme: too many seconds added"

    def add_minutes(self, mins):
        self.add_seconds(mins*60)

    def add_hours(self, hours):
        self.add_seconds(mins*60*60)

    def add_time(self, timediff):
        """add_time(timediff) Adds specificed amount of time to the current
        time held in this object. The format of difftime is a string,
        "HH:MM:SS"."""
        [h, m, s] = map(int, timediff.split(":"))
        self.add_seconds(h*3600+m*60+s)


class rtc_wkalrm(object):
    FMT = "BB%ds" % (struct.calcsize(rtc_time.FMT))
    def __init__(self, wkalrm):
        if wkalrm is None:
            self.enabled, self.pending = 0, 0
            self.time = rtc_time(None)
        else:
            self.enabled, self.pending, _tm = struct.unpack(self.FMT, wkalrm)
            self.time = rtc_time(_tm)

    def __repr__(self):
        return struct.pack(self.FMT, self.enabled, self.pending, repr(self.time))

    def __str__(self):
        return "wakealarm: enabled %d, pending %d\n%s" % (self.enabled, self.pending, self.time)



class RTC(object):
    """RTC() represent the Real Time Clock device on a PC. Some methods require
root privileges. """
    def __init__(self):
        self.rtc_fd = os.open("/dev/rtc", os.O_RDONLY)
        flags = fcntl.fcntl(self.rtc_fd, fcntl.F_GETFD)
        fcntl.fcntl(self.rtc_fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)

    def fileno(self):
        return self.rtc_fd

    def __del__(self):
        self.close()

    def close(self):
        if self.rtc_fd is not None:
            os.close(self.rtc_fd)
            self.rtc_fd = None

    def procinfo(self):
        """procinfo() Returns a dictionary with name-value pairs taken from
/proc/driver/rtc."""
        rv = {}
        raw = open("/proc/driver/rtc").read()
        lines = raw.split("\n")
        for line in lines:
            if not line:
                continue
            [name, val] = line.split(":", 1)
            rv[name.strip()] = val.strip()
        return rv

    def reset_epoch(self):
        """The default epoch is usually correct, but if it is not this method
will reset it to the value read from the device."""
        d = self.procinfo()
        self.epoch = int(d["rtc_epoch"])

    def time_tuple(self):
        """time_tuple() Returns a tuple suitable for the functions in the time module."""
        d = self.procinfo()
        tm = self.time_read()
        wday = None # XXX
        jday = None
        dstflag = -1
        return tm.tm_year+tm.epoch, tm.tm_mon, tm.tm_mday, \
            tm.tm_hour, tm.tm_min, tm.tm_sec, wday, jday, dstflag

    # the amt is a dummy variable to make it compatible with other read methods.
    def read(self, amt=None): 
        """read() returns a 2-tuple. (number of interrupts since last read,
interrupt status). May block."""
        raw = struct.unpack("L", os.read(self.rtc_fd, _UL_len))[0]
        status = raw & 0xf0
        count = raw >> 8
        return count, status

    def alarm_interrupt_on(self):
        return fcntl.ioctl(self.rtc_fd, RTC_AIE_ON)

    def alarm_interrupt_off(self):
        return fcntl.ioctl(self.rtc_fd, RTC_AIE_OFF)

    def update_interrupt_on(self):
        """Turn on update interrupts (one per second)"""
        return fcntl.ioctl(self.rtc_fd, RTC_UIE_ON)

    def update_interrupt_off(self):
        """Turn off update interrupts (one per second)"""
        return fcntl.ioctl(self.rtc_fd, RTC_UIE_OFF)

    def periodic_interrupt_on(self):
        return fcntl.ioctl(self.rtc_fd, RTC_PIE_ON)

    def periodic_interrupt_off(self):
        return fcntl.ioctl(self.rtc_fd, RTC_PIE_OFF)

    def watchdog_interrupt_on(self):
        return fcntl.ioctl(self.rtc_fd, RTC_WIE_ON)

    def watchdog_interrupt_off(self):
        return fcntl.ioctl(self.rtc_fd, RTC_WIE_OFF)

    def alarm_set(self, _rtc_time):
        return rtc_time(fcntl.ioctl(self.rtc_fd, RTC_ALM_SET, repr(_rtc_time)))

    def alarm_read(self):
        """alarm_read() Returns and rtc_time object. Note that only the hour,
        minute, and second fields are used. """
        _rtc_time = rtc_time(None)
        rv = rtc_time(fcntl.ioctl(self.rtc_fd, RTC_ALM_READ, repr(_rtc_time)))
        # the rtc does not have a date part for the alarm
        return rv

    def time_set(self, _rtc_time):
        return rtc_time(fcntl.ioctl(self.rtc_fd, RTC_SET_TIME, repr(_rtc_time)))

    def time_read(self):
        """time_read() Returns an rtc_time object. Note that the RTC driver
only fills in the year, month, day, hour, minute, and second fields.
        """
        _rtc_time = rtc_time(None)
        return rtc_time(fcntl.ioctl(self.rtc_fd, RTC_RD_TIME, repr(_rtc_time)))

    def irq_rate_set(self, _rate):
        fcntl.ioctl(self.rtc_fd, RTC_IRQP_SET, _rate)

    def irq_rate_read(self):
        return int(struct.unpack("L", fcntl.ioctl(self.rtc_fd, RTC_IRQP_READ, _UL))[0])

    def epoch_set(self, epoch):
        fcntl.ioctl(self.rtc_fd, RTC_EPOCH_SET, epoch)

    def epoch_read(self):
        return struct.unpack("L", fcntl.ioctl(self.rtc_fd, RTC_EPOCH_READ, _UL))[0]

    def wake_set(self, _wake_time):
        return rtc_wkalrm(fcntl.ioctl(self.rtc_fd, RTC_WKALM_SET, repr(_wake_time)))

    def wake_read(self):
        _wake_time = rtc_wkalrm(None)
        return rtc_wkalrm(fcntl.ioctl(self.rtc_fd, RTC_WKALM_RD, repr(_wake_time)))


class StopWatch(object):
    """StopWatch is a low-resolution timer for timing things, such as execution
time."""
    RESET = 0
    STOPPED = 1
    RUNNING = 2

    def __init__(self):
        self.reset(1)
        self._rtc = RTC()

    def __str__(self):
        if self._state != 2:
            rv = "%s s total elapsed time" % (self._elapsed)
        else:
            self._counter += 1
            rv = "[interval %d] %s s elapsed" % (self._counter, self.lap())
        return rv

    def start(self):
        if self._state == 2:
            raise RuntimeError, "StopWatch: already started"
        self._state = 2
        self._starttime = int(self._rtc.time_read())

    def stop(self):
        if self._state == 1:
            raise RuntimeError, "StopWatch: already stopped"
        self._state = 1
        delta = int(self._rtc.time_read()) - self._starttime
        self._elapsed += delta
        self._delta = delta

    def lap(self):
        if self._state == 2:
            return int(self._rtc.time_read()) - self._starttime

    def get_elapsed(self):
        if self._state == 1:
            return self._elapsed

    def restart(self):
        try:
            self.stop()
        except RuntimeError:
            pass
        self.reset(1)
        self.start()

    def reset(self, countertoo=0):
        self._elapsed = 0
        self._delta = 0
        self._state = 0
        if countertoo:
            self._counter = 0



# initialize the ioctl constants
from pycopia.OS.Linux.IOCTL import _IO, _IOW, _IOR
# taken from /usr/include/linux/rtc.h
p = ord('p')
RTC_AIE_ON  = _IO(p, 0x01)# /* Alarm int. enable on     */
RTC_AIE_OFF = _IO(p, 0x02)# /* ... off          */
RTC_UIE_ON  = _IO(p, 0x03)# /* Update int. enable on    */
RTC_UIE_OFF = _IO(p, 0x04)# /* ... off          */
RTC_PIE_ON  = _IO(p, 0x05)# /* Periodic int. enable on  */
RTC_PIE_OFF = _IO(p, 0x06)# /* ... off          */
RTC_WIE_ON  = _IO(p, 0x0f)#  /* Watchdog int. enable on */
RTC_WIE_OFF = _IO(p, 0x10)#  /* ... off         */

RTC_ALM_SET = _IOW(p, 0x07, rtc_time.FMT)# /* Set alarm time  */
RTC_ALM_READ    = _IOR(p, 0x08, rtc_time.FMT)# /* Read alarm time */
RTC_RD_TIME = _IOR(p, 0x09, rtc_time.FMT)# /* Read RTC time   */
RTC_SET_TIME    = _IOW(p, 0x0a, rtc_time.FMT)# /* Set RTC time    */
RTC_IRQP_READ   = _IOR(p, 0x0b, "L")#    /* Read IRQ rate   */
RTC_IRQP_SET    = _IOW(p, 0x0c, "L" )#   /* Set IRQ rate    */
RTC_EPOCH_READ  = _IOR(p, 0x0d, "L" )#   /* Read epoch      */
RTC_EPOCH_SET   = _IOW(p, 0x0e, "L" )#   /* Set epoch       */

RTC_WKALM_SET   = _IOW(p, 0x0f, rtc_wkalrm.FMT)#/* Set wakeup alarm*/
RTC_WKALM_RD    = _IOR(p, 0x10, rtc_wkalrm.FMT)#/* Get wakeup alarm*/
# no longer needed
del _IO, _IOW, _IOR

if __name__ == "__main__":

    import time
    sw = StopWatch()
    sw.start()
    for d in xrange(5):
        time.sleep(2)
        print sw
    time.sleep(2)
    sw.stop()
    print sw


