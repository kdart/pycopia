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
Use the powermate to control the volume at any time.

"""

from pycopia.OS import powermate
import _pyosd
import alsa

from time import time

# LED font
FONT="-xxl-ledfixed-medium-r-semicondensed-*-39-120-75-75-c-180-iso8859-1"

def constrain(x, minx=1, maxx=100):
    return max(min(x, maxx), minx)

class PowerVolume(powermate.PowerMate):
    pass

class OSDPercentage(object):
    def __init__(self, font=FONT, colour="#FFFFFF",timeout=3, \
                 offset=0, hoffset=0, shadow=0):
        self._osd = _pyosd.init(1)
        # attributes
        _pyosd.set_font(self._osd, font)
        _pyosd.set_colour(self._osd, colour)
        _pyosd.set_pos(self._osd, 2) # middle
        _pyosd.set_vertical_offset(self._osd, offset)
        _pyosd.set_horizontal_offset(self._osd, hoffset)
        _pyosd.set_shadow_offset(self._osd, shadow)
        _pyosd.set_align(self._osd, 1) # center
        _pyosd.set_timeout(self._osd, timeout)
        # save this as we won't have access to it on del
        self._deinit = _pyosd.deinit

    def __del__(self):
        if self._osd:
            self._deinit(self._osd)

    def display(self, val):
        _pyosd.display_perc(self._osd, 0, val)
    
    def is_displayed(self):
        return _pyosd.is_onscreen(self._osd)


class VolumeControl(object):
    def __init__(self):
        self._osd = OSDPercentage(font=FONT, colour="#6a5acd", timeout=3) # slate blue
        kn = self._knob = PowerVolume()
        kn.open()
        kn.register_motion(self.change_volume)
        kn.register_button(self.handle_button)
        am = self._mixer = alsa.mixer("default")
        self._volume = int(am.getVolume("Master")[0])

    def osd(self, val):
        self._osd.display(val)

    # this button-press operation is to work around segfaults in the alsa library. 8-(
    def handle_button(self, tm, flag):
        if flag:
            vol = self._volume
            self._mixer.setVolumeAbs("Master", vol, vol)

    def change_volume(self, tm, delta):
        self._volume = constrain(self._volume+int(delta), 1, 99)
        if (time() - tm) < 1.0:
            #vol = self._volume
            self.osd(self._volume)
            #self._mixer.setVolumeAbs("Master", vol, vol)
            #self._volume = int(self._mixer.getVolume("Master")[0])

    def poll(self):
        try:
            while 1:
                self._knob.poll()
        except KeyboardInterrupt:
            pass

    def __del__(self):
        self._knob.close()


def main(argv):
    vc = VolumeControl()
    vc.poll()


if __name__ == "__main__":
    import sys
    main(sys.argv)



