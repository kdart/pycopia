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
