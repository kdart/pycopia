#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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

