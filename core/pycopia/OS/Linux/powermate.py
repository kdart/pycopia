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
from pycopia.OS.Linux import event
from pycopia.aid import NULL


class PowerMate(Input.EventDevice):
    DEVNAME = 'Griffin PowerMate'
    EVENT_DISPATCH = {(event.EV_MSC, event.MSC_PULSELED):None, 
        (event.EV_REL, event.REL_DIAL):None, 
        (event.EV_KEY, event.BTN_0):None}

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
            ((pulse_asleep & 1) << 19) | \
            ((pulse_awake & 1) << 20)
        self.write(event.EV_MSC, event.MSC_PULSELED, value)
        ev = self.read() # read change notice back and return it.
        assert ev.evtype == event.EV_MSC
        return ev

    def register_motion(self, cb=None):
        """Register a callback to be called when the knob is turned. The
        callback receives two parameters, the timestamp of the event and
        a delta value."""
        self.EVENT_DISPATCH[(event.EV_REL, event.REL_DIAL)] = cb

    def register_button(self, cb=None):
        """Register a callback to be called when the knob is pressed.
        The callback receives two paramaters, the even timestamp and a
        value of 1 for a press, and 0 for a release."""
        self.EVENT_DISPATCH[(event.EV_KEY, event.BTN_0)] = cb

    def poll(self):
        """Blocking poller. Use this for simple apps. For more complex apps
        using asyncio then register this object with the asyncio poller."""
        while 1:
            ev = self.read()
            cb = self.EVENT_DISPATCH.get((ev.evtype, ev.code), NULL)
            cb(ev.time, ev.value)

    read_handler = poll


if __name__ == "__main__":
    import time
    pm = PowerMate()
    pm.find()
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

