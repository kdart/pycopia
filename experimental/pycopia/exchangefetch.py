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
Get the MS Exchange meeting forms from an IMAP server. Create iCal calendar
events for them.

The config file should contain::

    user = None
    password = None
    server = "paw-main"
    folder = "Web Forms"


"""

import imaplib
from email import *

import termtools
import timelib # time
import basicconfig

CONFIGFILE = "$HOME/.exchangefetchrc"

def handle_message(text):
    email = message_from_string(text)
    et = email.get_type()
    if et.startswith("multipart"):
        body = email.get_payload()[0].get_payload().strip()
    elif et.startswith("text"):
        body = email.get_payload().strip()
    else:
        return
    if body and body.startswith("When:"):
        event = EmailEvent(body)
        event.summary = email["Subject"]
        if not event.repeat:
            print event.iCal()
            print


class EmailEvent(object):
    def __init__(self, text=None):
        self.starttime = None
        self.endtime = None
        self.timezone = None
        self.repeat = None
        self.summary = ""
        self.where = None
        self.body = None
        if text:
            self.parse(text)


    def parse(self, text):
        state = 0
        body = []
        for line in text.splitlines():
            if not line:
                continue
            if line.startswith("When:") and state == 0:
                self._parse_when(line)
                continue
            if line.startswith("Where:") and state == 0:
                self.where = line.split(":", 1)[1].strip()
                continue
            if line == "*~*~*~*~*~*~*~*~*~*":
                state = 1
                continue
            if state == 1:
                body.append(line)
        self.body = "\n".join(body)

    def _parse_when(self, line):
        timeline = line.split(":", 1)[1].strip()
        if timeline.startswith("Occurs"):
            self._parse_repeater(timeline)
            return
        hyphen = timeline.find("-")
        oparen = timeline.find("(")
        eparen = timeline.find(")")
        assert hyphen >= 0
        self.starttime = timelib.strptime_mutable(timeline[:hyphen], "%A, %B %d, %Y %I:%M %p")
        self.endtime = self.starttime.copy()
        endtime = timelib.strptime_mutable(timeline[hyphen+1:oparen].strip(), "%I:%M %p")
        self.endtime.hour=endtime.hour; self.endtime.minute=endtime.minute
        self.timezone = timeline[oparen+1:eparen]

    def _parse_repeater(self, timeline):
        self.repeat = True # XXX
#When: Occurs every week on Tue effective Mar 8, 2005 from 2:00 PM-3:00 PM (GMT-08:00) Pacific Time (US & Canada), Tijuana

    def iCal(self):
        s = ["START:VEVENT"]
        s.append("DTSTART;TZID=/softwarestudio.org/Olson_20011030_5/America/Los_Angeles:%s" % (self._icaltime(self.starttime),))
        s.append("DTEND;TZID=/softwarestudio.org/Olson_20011030_5/America/Los_Angeles:%s" % (self._icaltime(self.endtime),))
        s.append("SUMMARY:%s" % (self.summary,))
        s.append("DESCRIPTION:Where: %s.\n %s" % (self.where, self.body.replace("\n", "\n ")))
        s.append("END:VEVENT")
        return "\r\n".join(s)

    def _icaltime(self, t):
        return t.strftime("%Y%m%dT%H%M%S")



def get_messages(filt="NEW"):
    cf = basicconfig.get_config(CONFIGFILE)
    if not cf.user:
        user = termtools.getuser()
    else:
        user = cf.user

    if not cf.password:
        password = termtools.getpass()
    else:
        password = cf.password

    M = imaplib.IMAP4(cf.server)
    resp, data = M.login(user, password)
    if resp != "OK":
        print "Unable to log in."
        return

    M.select(cf.folder)
    resp, data = M.search(None, filt)
    if resp == "OK":
        for num in data[0].split():
            resp, data = M.fetch(num, "(RFC822)")
            handle_message(data[0][1])
    M.close()
    M.logout()


def main(argv):
    if len(argv) > 1:
        filt = argv[1]
    else:
        filt = "NEW"
    get_messages(filt)


if __name__ == "__main__":
    import sys
    main(sys.argv)

