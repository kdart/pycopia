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

