#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2009  Keith Dart <keith@kdart.com>
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

"""

from pycopia.OS.Linux import Input
from pycopia.OS.Linux import event


class Keyboard(Input.EventDevice):
    DEVNAME = 'Keyboard'

    def register_callback(self, cb):
        self._callback = cb

    def poll(self):
        """Blocking poller. Use this for simple apps. For more complex apps
        using asyncio then register this object with the asyncio poller."""
        while 1:
            ev = self.read()
            if ev.evtype == event.EV_KEY:
                self._callback(ev)

    read_handler = poll


if __name__ == "__main__":
    pm = Keyboard()
    pm.find()
    print pm
    print "devname:", pm.name
    print "driverversion: 0x%x" % (pm.get_driverversion(),)
    print "deviceid:", pm.get_deviceid()
    print "features:", pm.get_features()

    def print_key(event):
        print event

    pm.register_callback(print_key)
    try:
        while 1:
            pm.poll()
    except KeyboardInterrupt:
        pass
    pm.close()

