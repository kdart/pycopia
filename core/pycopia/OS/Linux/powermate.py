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
A Python interface to the Griffin Technology PowerMate USB knob.  This
device is an aluminum dial which can measure clockwise and anticlockwise
rotation. The dial also acts as a pushbutton. The base contains an LED
which can be instructed to pulse or to switch to a particular intensity.

See http://www.griffintechnology.com/products/powermate/ for more info.

Note that you must have the Linux kernel driver for this enabled in your
kernel config (at least 2.4.22). It is listed in the USB devices section
of the config menu. The Linux hotplug scripts should load the driver if
it is a module, but it does not load the evdev module. You might have to
"modprobe evdev" first (or better yet, put that in one of your rc files.
In Gentoo Linux, place a line with "evdev" in the
/etc/modules.autoload.d/kernel-2.4 file.

"""

from pycopia.OS.Linux import Input


class PowerMate(Input.EventDevice):
    DEVNAME = 'Griffin PowerMate'
    EVENT_DISPATCH = {(Input.EV_MSC, Input.MSC_PULSELED):None, 
        (Input.EV_REL, Input.REL_DIAL):None, 
        (Input.EV_KEY, Input.BTN_0):None}

    def set_LED(self, brightness, pulse_speed=0, pulse_table=0, 
                pulse_asleep=0, pulse_awake=1):
        """set the LED attributes. You can adjust the brightness, or make it
        pulse. The brightness and pulse_speed values are floats between 0 and
        1.0. The pulse_table is a built-in pattern table taking values of 0, 1,
        or 2.  The pulse_asleep and pulse_awake are flags the tell the knob in
        which mode they should light in."""
        value = (int(brightness*255.0) & 0xff) | \
            ((int(pulse_speed*510.0) & 0x1ff) << 8) | \
            ((pulse_table % 3) << 17) | \
            ((not not pulse_asleep) << 19) | \
            ((not not pulse_awake) << 20)
        self.write(Input.EV_MSC, Input.MSC_PULSELED, value)
        ev = self.read() # read change notice back and return it.
        assert ev.evtype == Input.EV_MSC
        return ev

    def register_motion(self, cb=None):
        """Register a callback to be called when the knob is turned. The
        callback receives two parameters, the timestamp of the event and
        a delta value."""
        self.EVENT_DISPATCH[(Input.EV_REL, Input.REL_DIAL)] = cb

    def register_button(self, cb=None):
        """Register a callback to be called when the knob is pressed.
        The callback receives two paramaters, the even timestamp and a
        value of 1 for a press, and 0 for a release."""
        self.EVENT_DISPATCH[(Input.EV_KEY, Input.BTN_0)] = cb

    def poll(self):
        """Blocking poller. Use this for simple apps. For more complex apps
        using asyncio then register this object with the asyncio poller."""
        while 1:
            ev = self.read()
            cb = self.EVENT_DISPATCH.get((ev.evtype, ev.code))
            if cb:
                cb(ev.time, ev.value)

    handle_read_event = poll


if __name__ == "__main__":
    import time
    pm = PowerMate()
    pm.open()
    print pm
    print "devname:", pm.name
    print "driverversion: 0x%x" % (pm.get_driverversion(),)
    print "deviceid:", pm.get_deviceid()
    ev = pm.set_LED(0.5, 0.5, 0, 1, 1)
    print ev

    absolute = 0
    def print_button(ts, value):
        if value:
            print "button pressed"
        else:
            print "button released"

    def track_movement(ts, delta):
        global absolute
        absolute += delta
        print "delta: %d, absolute position: %d" % (delta, absolute)

    pm.register_button(print_button)
    pm.register_motion(track_movement)
    try:
        while 1:
            pm.poll()
    except KeyboardInterrupt:
        pass
    pm.close()

