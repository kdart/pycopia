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
Report objects that sends a text email.

"""

import sys, os
from cStringIO import StringIO

from pycopia import reports
NO_MESSAGE = reports.NO_MESSAGE

from pycopia import ezmail

class EmailReport(reports.NullReport):
    """Create an a report that is emailed, rather than written to a file. 
    EmailReport(
        [formatter="text/plain"],  # formatter type
        [recipients=None],         # list of recipients, or None. If none the
                                   # message is mailed to self (From address).
        [From=None],               # Address for From field. If None the current user is used.
        )

    """
    def __init__(self, formatter="text/plain", recipients=None, From=None):
        self._logfile = None
        self._message = ezmail.MultipartMessage()
        self._message.From(From)
        self._message.To(recipients)
        self._formatter, ext = reports.get_formatter(formatter)

    filename = property(lambda s: None)
    filenames = property(lambda s: [])
    mimetype = property(lambda s: s._formatter.MIMETYPE)

    def initialize(self, config=None):
        self._fo = StringIO()
        self.write(self._formatter.initialize())

    def logfile(self, lf):
        self._logfile = str(lf)

    def write(self, text):
        self._fo.write(text)

    def writeline(self, text):
        self._fo.write(text)
        self._fo.write("\n")

    def finalize(self):
        """finalizing this Report sends off the email."""
        self.write(self._formatter.finalize())
        report = ezmail.MIMEText.MIMEText(self._fo.getvalue(), 
                        self._formatter.MIMETYPE.split("/")[1])
        report["Content-Disposition"] = "inline"
        self._message.attach(report)
        if self._logfile:
            try:
                lfd = open(self._logfile).read()
            except:
                pass # non-fatal
                print >>sys.stderr, "could not read or attach log file: %r" % (self._logfile,)
            else:
                logmsg = ezmail.MIMEText.MIMEText(lfd)
                logmsg["Content-Disposition"] = 'attachment; filename=%s' % (os.path.basename(self._logfile), )
                self._message.attach(logmsg)
        ezmail.mail(self._message)

    def add_title(self, title):
        self._message.add_header("Subject", title)
        self.write(self._formatter.title(title))

    def add_heading(self, text, level=1):
        self.write(self._formatter.heading(text, level))

    def add_message(self, msgtype, msg, level=1):
        self.write(self._formatter.message(msgtype, msg, level))

    def add_summary(self, entries):
        lines = map(self._formatter.summaryline, entries)
        self.write("\n".join(lines))
        self.write("\n")

    def passed(self, msg=NO_MESSAGE, level=1):
        self.add_message("PASSED", msg, level)

    def failed(self, msg=NO_MESSAGE, level=1):
        self.add_message("FAILED", msg, level)

    def expectedfail(self, msg=NO_MESSAGE, level=1):
        self.add_message("EXPECTED_FAIL", msg, level)

    def incomplete(self, msg=NO_MESSAGE, level=1):
        self.add_message("INCOMPLETE", msg, level)

    def abort(self, msg=NO_MESSAGE, level=1):
        self.add_message("ABORTED", msg, level)

    def info(self, msg, level=1):
        self.add_message("INFO", msg, level)

    def diagnostic(self, msg, level=1):
        self.add_message("DIAGNOSTIC", msg, level)

    def add_text(self, text):
        self.write(self._formatter.text(text))

    def add_url(self, text, url):
        self.write(self._formatter.url(text, url))

    def newpage(self):
        self.write(self._formatter.newpage())

    def newsection(self):
        self.write(self._formatter.section())



if __name__ == "__main__":
    rpt = EmailReport("text/plain", recipients=["kdart@kdart.com"])
    rpt.initialize()
    rpt.add_title("Email report self test.")
    rpt.info("Some non-useful info. 8-)")
    rpt.finalize()


