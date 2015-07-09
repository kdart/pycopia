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
Report objects that sends a text email.

"""

import os
from cStringIO import StringIO

import chardet

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
    def __init__(self, formatter="text/plain", recipients=None, From=None, attach_logfile=False):
        self._logfile = None
        self._message = ezmail.MultipartMessage()
        self._message.From(From)
        self._message.To(recipients)
        self._attach_logfile = attach_logfile
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
        if self._attach_logfile and self._logfile:
            try:
                lfd = open(self._logfile, "rb").read()
            except:
                pass # non-fatal
            else:
                logmsg = ezmail.MIMEText.MIMEText(lfd, charset=chardet.detect(lfd))
                logmsg["Content-Disposition"] = 'attachment; filename=%s' % (
                        os.path.basename(self._logfile), )
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


