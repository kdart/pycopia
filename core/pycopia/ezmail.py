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
A helper module that wraps the standard email package to make simple
things simple. ;-)

"""

import sys, os
from email import *

from pycopia.emailplus import *

from pycopia import socket
from pycopia import timelib


class MailError(Exception):
    pass


_HOSTNAME = None

def _get_hostname():
    global _HOSTNAME
    if _HOSTNAME is None:
        _HOSTNAME = socket.gethostname()
    return _HOSTNAME


def formatdate(timeval=None):
    if timeval is None:
        timeval = timelib.now()
    timeval = timelib.gmtime(timeval)
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][timeval[6]],
            timeval[2],
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][timeval[1]-1],
                                timeval[0], timeval[3], timeval[4], timeval[5])



class SimpleMessage(Message.Message):
    def __init__(self, _text, mimetype="text/plain", charset="us-ascii"):
        Message.Message.__init__(self)
        self['MIME-Version'] = '1.0'
        self.add_header('Content-Type', mimetype)
        self.set_payload(_text, charset)

    def __eq__(self, other):
        if self["From"] != other["From"]:
            return 0
        elif str(self["To"]) != str(other["To"]):
            return 0
        elif self.get_payload() != other.get_payload():
            return 0
        else:
            return 1

    def __ne__(self, other):
        return not self.__eq__(other)

class AutoMessageMixin(object):
    """Use this as a mix-in class to add self-addressing and sending
    functionality to Message objects.  """
    def __init__(self, From=None, To=None):
        self.mail_from = None
        self.rcpt_to = []
        if From:
            self.From(From)
        if To:
            self.To(To)

    def send(self, smtp, mail_options=None, rcpt_options=None):
        """send off this message using the supplied SMTP sender object."""
        mopts = mail_options or []
        rcptopts = rcpt_options or []
        if not self.mail_from or not self.rcpt_to:
            raise RuntimeError, "AutoMessage: cannot send. no From or recipients."
        if self.has_key("Bcc"):
            del self["Bcc"]
        now = timelib.now()
        self["Date"] = formatdate(now)
        self["Message-ID"] = "<%s.%x@%s>" % (
            timelib.localtimestamp(now, fmt="%Y%m%d%H%M%S"), 
            id(self) % 0x7fffffff,
            _get_hostname())
        return smtp.sendmail(self.mail_from, self.rcpt_to, self.as_string(0), mopts, rcptopts)

    def Subject(self, subj):
        self["Subject"] = str(subj)

    def From(self, addr, name=None):
        if addr is None:
            addr, name = self_address()
        self.mail_from = addr
        self["From"] = get_address(addr, name)
        self.set_unixfrom("From <%s> %s" % (addr, formatdate()))

    def To(self, addr, name=None):
        self._add_recipient("To", addr, name)

    def Cc(self, addr, name=None):
        self._add_recipient("Cc", addr, name)

    def Bcc(self, addr, name=None):
        self._add_recipient("Bcc", addr, name)

    def _add_recipient(self, header, addr, name):
        if addr is None:
            addr, name = self_address()
        elif type(addr) is tuple:
            addr, name = addr
        elif type(addr) is list:
            for name in addr:
                self._add_recipient(header, name, None)
            return
        elif type(addr) is not str:
            raise TypeError, "recipients need to be a list or string"
        self.rcpt_to.append(addr)
        long_addr = get_address(addr, name)
        if self.has_key(header):
            new = self[header] + ", " + long_addr
            del self[header]
            self[header] = new
        else:
            self[header] = long_addr


class AutoMessage(SimpleMessage, AutoMessageMixin):
    def __init__(self, text, mimetype="text/plain", charset="us-ascii", 
                    From=None, To=None):
        AutoMessageMixin.__init__(self, From, To)
        SimpleMessage.__init__(self, text, mimetype, charset)


class MultipartMessage(MIMEMultipart.MIMEMultipart, AutoMessageMixin):
    def __init__(self, From=None, To=None):
        MIMEMultipart.MIMEMultipart.__init__(self)
        AutoMessageMixin.__init__(self, From, To)


def get_parser(klass=SimpleMessage, strict=0):
    """get an email parser."""
    parser = Parser.Parser(klass, strict)
    return parser

def parse_file(filename, klass=SimpleMessage, strict=0):
    p = get_parser(klass, strict)
    fo = open(filename)
    try:
        msg = p.parse(fo)
    finally:
        fo.close()
    return msg

def parse_fileobject(fo, klass=SimpleMessage, strict=0):
    p = get_parser(klass, strict)
    msg = p.parse(fo)
    return msg

def new_message(body="", headdict=None, msgclass=SimpleMessage):
    """Factory function that returns a new message object (SimpleMessage by
default). """
    msg = msgclass(body)
    myemail, longname = self_address()
    msg.set_unixfrom("From %s %s" % (myemail, formatdate()))
    if headdict:
        for name, val in headdict.items():
            msg.add_header(name, val)
    return msg

def message_from_string(s, klass=SimpleMessage, strict=0):
    """Parse a string into a SimpleMessage object model.  """
    parser = get_parser(klass, strict)
    return parser.parsestr(s)

def self_address():
    """self_address() 
Returns address string referring to user running this (yourself)."""
    global CONFIG
    name, longname = getuser()
    domain = CONFIG.get("domain")
    if domain:
        return "%s@%s" % (name, domain), longname
    else:
        return "%s@%s" % (name, _get_hostname()), longname

def getuser():
    """getuser()
Return the userid and long name ("GECOS" field) from the passwd file."""
    import pwd
    uent = pwd.getpwuid(os.getuid())
    return uent[0], uent[4]

def parseaddr(addr):
    addrs = Utils._AddressList(addr).addresslist
    if not addrs:
        return '', ''
    return addrs[0]

def get_address(addr, name=None):
    if addr is None:
        addr, name = self_address()
    if name:
        return '"%s" <%s>' % (name, addr)
    else:
        return str(addr)

def _do_attach(multipart, obj):
    if isinstance(obj, Message.Message):
        multipart.attach(obj)
    else:
        from pycopia import textutils
        body = textutils.text(obj)
        msg = MIMEText.MIMEText(body, _subtype="plain")
        multipart.attach(msg)


def ezmail(obj, To=None, From=None, subject=None, cc=None, bcc=None,
        extra_headers=None):
    """A generic mailer that sends a multipart-mixed message with attachments.
    The 'obj' parameter may be a MIME* message, or another type of object that
    will be converted to text. If it is a list, each element of the list will
    be attached.

    """
    global CONFIG
    if isinstance(obj, (AutoMessage, MultipartMessage)):
        outer = obj
    else:
        if type(obj) is list:
            outer = MultipartMessage()
            for part in obj:
                _do_attach(outer, part)
        else:
            outer = AutoMessage(str(obj).encode("us-ascii"))

    outer.To(To)
    outer.From(From)
    outer.Subject(subject)
    if cc:
        outer.Cc(cc)
    if bcc:
        outer.Bcc(bcc)

    if extra_headers: # a dictionary of header names (keys), and values.
        for name, value in extra_headers.items():
            outer[name] = value

    mailhost = CONFIG.get("mailhost", "localhost")

    if mailhost == "localhost":
        smtp = LocalSender()
        status = outer.send(smtp)
        if not status:
            raise MailError(str(status))
    else:
        from pycopia.inet import SMTP
        smtp = SMTP.SMTP(mailhost, bindto=CONFIG.get("bindto"))
        errs = outer.send(smtp)
        smtp.quit()
        if errs:
            raise MailError(str(status))

    return outer["Message-ID"]


def mail(obj, To=None, From=None, subject=None, cc=None, bcc=None,
        extra_headers=None):
    try:
        return ezmail(obj, To, From, subject, cc, bcc, extra_headers)
    except MailError, err:
        print >>sys.stderr, "Error while sending mail!"
        print >>sys.stderr, err
        return None


def get_config():
    from pycopia import basicconfig
    return basicconfig.get_config("ezmail.conf")


class LocalSender(object):
    def sendmail(self, From, rcpt_to, msg, mopts=None, rcptopts=None):
        from pycopia import proctools
        cmd = "/usr/sbin/sendmail -i"
        if From:
            cmd += " -f %s" % From
        for rcpt in rcpt_to:
            cmd += " %s" % rcpt
        proc = proctools.spawnpipe(cmd)
        proc.write(msg)
        proc.close()
        proc.wait()
        return proc.exitstatus


# global configuration
CONFIG = get_config()


if __name__ == "__main__":
    print mail(["This is a test.\n", "Another part"], None, subject="Testing ezmail")

