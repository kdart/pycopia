#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) Keith Dart <keith@kdart.com>
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


import os

import unittest

from pycopia.audio import alsacontrol
from pycopia.audio import alsaplayer
from pycopia.audio import Vgetty


class AudioTests(unittest.TestCase):

    def test_alsacontrol(self):
        """Test alsa controller."""
        pass

    def test_alsaplayer(self):
        """Test alsa player."""
        pass

    def test_vgetty(self):
        #signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        os.environ["VOICE_INPUT"] = "0"
        os.environ["VOICE_OUTPUT"] = "1"
        os.environ["VOICE_PID"] = str(os.getpid())
        os.environ["VOICE_PROGRAM"] = "Vgetty.py"
        cp = Vgetty.CallProgram() # XXX

    def test_alsaplayer(argv):
        ap = alsaplayer.alsaplayer()
        print ap # XXX

    def test_alsacontrol(self):
        ap = alsacontrol.get_session()
        print ap # XXX


if __name__ == '__main__':
    unittest.main()
