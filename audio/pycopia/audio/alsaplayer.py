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
Start and control an alsaplayer deamon instance.
"""

from pycopia import proctools
import os

try:
    PLAYER = proctools.which("alsaplayer")
except ValueError:
    raise ImportError, "alsaplayer program not found!"

DEVICE = os.environ.get("ALSAPLAYERDEVICE", "default")

def get_alsaplayer(session=0, name="alsaplayer", device=DEVICE, extraopts="", logfile=None):
    """Return a process object for the alsaplayer."""
    opts = "-i daemon -q -n %s -s '%s' -d %s --nosave" % (session, name, device)
    CMD = "%s %s %s" % (PLAYER, opts, extraopts)
    aplayer = proctools.spawnpipe(CMD, logfile=logfile)
    return aplayer


