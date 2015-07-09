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
Basic Python voice answering machine. Call this from vgetty using the
following config:

[ part of voice.conf]
program vgetty
voice_shell /usr/bin/python2.4
call_program /etc/pycopia/voicemail.py

"""

import sys, os, time

from pycopia import logfile
from pycopia.audio import Vgetty
from pycopia.basicconfig import ConfigHolder


def main(argv):
    cf = ConfigHolder()
    cf.VOICEDIR = "/var/spool/voice"
    cf.MESSAGEDIR = "messages"
    cf.SPOOLDIR = "incoming"
    cf.GREETING = "greeting.rmd"
    cf.LOGFILE = "/var/log/voicemail/voicemail.log"

    lf = logfile.open(cf.LOGFILE)

    try:
        rv = Vgetty.answering_machine(cf, lf)
    finally:
        lf.close()
    return rv

sys.exit(main(sys.argv))

