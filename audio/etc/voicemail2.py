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
Voice mail system with email notification.
Call this from vgetty by useing the following voice.conf configuration.

[ part of voice.conf]
program vgetty
voice_shell /usr/bin/python2.4
call_program /etc/pycopia/voicemail2.py

Be sure to configure your ezmail.conf and voicemail.conf file appropriately.

"""

import sys, os, time
import tempfile

from pycopia import proctools
from pycopia import logfile
from pycopia import ezmail
from pycopia import basicconfig
from pycopia.audio import Vgetty


def answering_machine(logfile=None, dtmf_handler=None):
    global CF
    greeting = os.path.join(CF.VOICEDIR, CF.MESSAGEDIR, CF.GREETING)

    cp = Vgetty.BasicCallProgram(logfile=logfile)
    cp.inname = os.path.join(CF.VOICEDIR, CF.SPOOLDIR, "v-%s.rmd" % (int(time.time()),))
    cp.set_dtmf_handler(dtmf_handler)
    cp.play(greeting)
    cp.beep()
    try:
        cp.record(cp.inname)
    except VgettyError, err:
        print >>sys.stderr, "%s: %s" % (time.ctime(), err)
        cp.beep(6000, 3)
        cp.close()
    else:
        print >>sys.stderr, "%s:%s|%s|%s|%s" % (time.ctime(), cp._device, cp.inname, 
                    cp.caller_id, cp.caller_name)
        cp.close()
        try:
            mailmessage(cp)
        except:
            ex, val, tb = sys.exc_info()
            print >>sys.stderr, "Error during mailmessage: (%s: %s)" % (ex, val)
    return 0


def mailmessage(cp):
    parts = []
    # main message text and subject line
    body = CF.mail.body(line=CF.lines.get(cp._device), caller_id=cp.caller_id, caller_name=cp.caller_name)
    parts.append(body)
    subj = CF.mail.Subject(line=CF.lines.get(cp._device), caller_id=cp.caller_id, caller_name=cp.caller_name)
    # ogg file attachment
    oggfile = tempfile.NamedTemporaryFile(suffix=".ogg", prefix="voicemail", dir="/var/tmp")
    Vgetty.rmd2ogg(cp.inname, oggfile.name)
    oggfile.seek(0)
    ogg = ezmail.MIMEApplication.MIMEApplication(oggfile.read(), "ogg")
    ogg["Content-Disposition"] = "attachment; filename=%s" % (os.path.basename(cp.inname.replace("rmd", "ogg")), )
    oggfile.close()
    parts.append(ogg)
    # mail it!
    ezmail.mail(parts, subject=subj, To=CF.mail.To)


CF = None
def main(argv):
    global CF
    CF = basicconfig.get_config("/etc/pycopia/voicemail.conf")
    if CF.get("LOGFILE"):
        lf = logfile.open(CF.LOGFILE)
    else:
        lf = None

    rv = 1
    try:
        rv = answering_machine(lf)
    finally:
        if lf:
            lf.close()
    return rv

sys.exit(main(sys.argv))

