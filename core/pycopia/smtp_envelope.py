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
SMTP envelope object that encapsulates a SMTP protocol message envelope.

"""

from cStringIO import StringIO

def get_differences (msg1, msg2):
    diffs = []

    for header in ['subject', 'from', 'to']:
        h1 = msg1[header]
        h2 = msg2[header]
        if not h1 or not h2 or h1 != h2:
            diffs.append (("Header '%s' differs" % repr(header), h1, h2))

    body1 = msg1.message.get_payload()
    body2 = msg2.message.get_payload()
    if body1 != body2:
        diffs.append (("Bodies differ", body1, body2))

    return diffs


class Envelope(object):
    """Envelope([mail_from], [recpt_list]) An envelope holds an SMTP
    conversation from the MAIL FROM command to the end of a DATA part.  It may
    be re-sent by calling the 'send()' method with an SMTP connection object.
    The message body can be parsed by passing in an 'ezmail' parser object to
    the 'parse_data()' method."""

    def __init__ (self, mail_from=None, rcpt_to=None):
        self.mail_from = mail_from
        self.rcpt_to = rcpt_to or []
        self.data = None
        self.message = None

    def __repr__ (self):
        return "Envelope(%r, %r)" % (self.mail_from, self.rcpt_to)

    def __str__(self):
        s = ["MAIL FROM: %s" % (self.mail_from,)]
        for rcpt in self.rcpt_to:
            s.append("RCPT TO: %s" % (rcpt))
        s.append("\n")
        if self.message:
            s.append(str(self.message))
        elif self.data:
            s.append(self.data.getvalue())
        else:
            s.append("<no data!>")
        return "\n".join(s)

    def has_data(self):
        """has_data() is true if there is data or message."""
        if self.data:
            return self.data.tell()
        elif self.message:
            return len(self.message)
        else:
            return 0

    def write(self, text):
        """write(text)
Writes text to the message body."""
        if self.data is None:
            self.data = StringIO()
        self.data.write(text)

    def writeln(self, text):
        """writeln(text)
Writes text to the message body, adding a newline."""
        self.write(text)
        self.write("\n")

    def set_from(self, frm):
        """set_from(from_address)
Sets the MAIL FROM address for this Envelope."""
        self.mail_from = frm

    def add_rcpt(self, rcpt):
        """add_rcpt(recipient)
Adds a new recipient to the RCPT list."""
        self.rcpt_to.append(rcpt)

    def parse_data(self, parser):
        """parse_data(parser)
Instructs the Envelope to convert its raw 'data' attribute to a 'message'
attribute using the supplied parser object. A 'message' attribute is an
'email' package Message type object."""
        if self.data is not None:
            self.data.seek(0,0)
            # parser should be email.Parser.Parser object, or subclass thereof.
            self.message = parser.parse(self.data)
            self.data.close()
            if self.message:
                self.data = None

    def send(self, smtp, mail_options=[], rcpt_options=[]):
        """send(smtp_client, mail_options=[], rcpt_options=[])
Mails this envelope using the supplied SMTP client object."""
        if self.message:
            return smtp.sendmail(self.mail_from, self.rcpt_to, self.message.as_string(), mail_options, rcpt_options)
        elif self.data:
            return smtp.sendmail(self.mail_from, self.rcpt_to, self.data.getvalue(), mail_options, rcpt_options)
        else:
            body = "From: %s\nTo: %s\n\nEnvelope message." % (self.mail_from, ", ".join(self.rcpt_to))
            return smtp.sendmail(self.mail_from, self.rcpt_to, body, mail_options, rcpt_options)



