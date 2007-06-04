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

'''SMTP/ESMTP client class.

This should follow RFC 821 (SMTP), RFC 1869 (ESMTP), RFC 2554 (SMTP
Authentication) and RFC 2487 (Secure SMTP over TLS).

Notes:

Please remember, when doing ESMTP, that the names of the SMTP service
extensions are NOT the same thing as the option keywords for the RCPT
and MAIL commands!

Example:

  >>> import smtplib
  >>> s=smtplib.SMTP("localhost")
  >>> print s.help()
  This is Sendmail version 8.8.4
  Topics:
      HELO    EHLO    MAIL    RCPT    DATA
      RSET    NOOP    QUIT    HELP    VRFY
      EXPN    VERB    ETRN    DSN
  For more info use "HELP <topic>".
  To report bugs in the implementation send email to
      sendmail-bugs@sendmail.org.
  For local information send email to Postmaster at your site.
  End of HELP info
  >>> s.putcmd("vrfy","someone@here")
  >>> s.getreply()
  (250, "Somebody OverHere <somebody@here.my.org>")
  >>> s.quit()
'''

# Author: The Dragon De Monsyne <dragondm@integral.org>
# ESMTP support, test code and doc fixes added by
#     Eric S. Raymond <esr@thyrsus.com>
# Better RFC 821 compliance (MAIL and RCPT, and CRLF in data)
#     by Carey Evans <c.evans@clear.net.nz>, for picky mail servers.
# RFC 2554 (authentication) support by Gerhard Haering <gerhard@bigfoot.de>.
#
# This was modified from the Python 1.5 library HTTP lib.
#
# Extensive modifications by Keith Dart <kdart@kdart.com>. 

import re
import rfc822
import types
import base64
import hmac
from errno import EINTR, ECONNREFUSED
from cStringIO import StringIO

from pycopia import socket
from pycopia import scheduler


SMTP_PORT = 25
CRLF="\r\n"

OLDSTYLE_AUTH = re.compile(r"auth=(.*)", re.I)

def encode_base64(s, eol=None):
    return "".join(base64.encodestring(s).split("\n"))

# Exception classes used by this module.
class SMTPException(Exception):
    """Base class for all exceptions raised by this module."""

class SMTPServerDisconnected(SMTPException):
    """Not connected to any SMTP server.

    This exception is raised when the server unexpectedly disconnects,
    or when an attempt is made to use the SMTP instance before
    connecting it to a server.
    """

class SMTPResponseException(SMTPException):
    """Base class for all exceptions that include an SMTP error code.

    These exceptions are generated in some instances when the SMTP
    server returns an error code.  The error code is stored in the
    `smtp_code' attribute of the error, and the `smtp_error' attribute
    is set to the error message.
    """

    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

class SMTPSenderRefused(SMTPResponseException):
    """Sender address refused.

    In addition to the attributes set by on all SMTPResponseException
    exceptions, this sets `sender' to the string that the SMTP refused.
    """
    def __init__(self, code, msg, sender):
        self.smtp_code = code
        self.smtp_error = msg
        self.sender = sender
        self.args = (code, msg, sender)

class SMTPRecipientsRefused(SMTPException):
    """All recipient addresses refused.

    The errors for each recipient are accessible through the attribute
    'recipients', which is a dictionary of exactly the same sort as
    SMTP.sendmail() returns.
    """
    def __init__(self, recipients):
        self.recipients = recipients
        self.args = ( recipients,)


class SMTPDataError(SMTPResponseException):
    """The SMTP server didn't accept the data."""

class SMTPConnectError(SMTPResponseException):
    """Error during connection establishment."""

class SMTPHeloError(SMTPResponseException):
    """The server refused our HELO reply."""

class SMTPAuthenticationError(SMTPResponseException):
    """Authentication error.

    Most probably the server didn't accept the username/password
    combination provided.
    """

class SSLFakeSocket(object):
    """A fake socket object that really wraps a SSLObject.

    It only supports what is needed in smtplib.
    """
    def __init__(self, realsock, sslobj):
        self.realsock = realsock
        self.sslobj = sslobj

    def send(self, str):
        self.sslobj.write(str)
        return len(str)

    sendall = send

    def close(self):
        self.realsock.close()

class SSLFakeFile(object):
    """A fake file like object that really wraps a SSLObject.

    It only supports what is needed in smtplib.
    """
    def __init__( self, sslobj):
        self.sslobj = sslobj

    def readline(self):
        str = ""
        chr = None
        while chr != "\n":
            chr = self.sslobj.read(1)
            str += chr
        return str

    def close(self):
        pass

def quoteaddr(addr):
    """Quote a subset of the email addresses defined by RFC 821.

    Should be able to handle anything rfc822.parseaddr can handle.
    """
    m = (None, None)
    try:
        m=rfc822.parseaddr(addr)[1]
    except AttributeError:
        pass
    if m == (None, None): # Indicates parse failure or AttributeError
        #something weird here.. punt -ddm
        return "<%s>" % addr
    else:
        return "<%s>" % m

def quotedata(data):
    """Quote data for email.

    Double leading '.', and change Unix newline '\\n', or Mac '\\r' into
    Internet CRLF end-of-line.
    """
    return re.sub(r'(?m)^\.', '..',
        re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data))


class SMTP(object):
    """This class manages a connection to an SMTP or ESMTP server.
    SMTP Objects:
        SMTP objects have the following attributes:
            helo_resp
                This is the message given by the server in response to the
                most recent HELO command.

            ehlo_resp
                This is the message given by the server in response to the
                most recent EHLO command. This is usually multiline.

            does_esmtp
                This is a True value _after you do an EHLO command_, if the
                server supports ESMTP.

            esmtp_features
                This is a dictionary, which, if the server supports ESMTP,
                will _after you do an EHLO command_, contain the names of the
                SMTP service extensions this server supports, and their
                parameters (if any).

                Note, all extension names are mapped to lower case in the
                dictionary.

        See each method's docstrings for details.  In general, there is a
        method of the same name to perform each SMTP command.  There is also a
        method called 'sendmail' that will do an entire mail transaction.
        """
    file = None
    helo_resp = None
    ehlo_resp = None
    does_esmtp = 0

    def __init__(self, host='', port=25, bindto=None, logfile=None):
        """Initialize a new instance.

        If specified, `host' is the name of the remote host to which to
        connect.  If specified, `port' specifies the port to which to connect.
        By default, smtplib.SMTP_PORT is used.  An SMTPConnectError is raised
        if the specified `host' doesn't respond correctly.  """
        self.host = host
        self.port = port
        self._bindto = bindto
        self.logfile = logfile
        self.esmtp_features = {}
        if host:
            (code, msg) = self.connect(host, port, bindto)
            if code != 220:
                raise SMTPConnectError(code, msg)

    def __repr__(self):
        return "%s(%s, %d)" % (self.__class__.__name__, self.host, self.port)

    def set_logfile(self, logfile):
        self.logfile = logfile

    def connect(self, host='localhost', port=0, bindto=None, retries=3):
        """Connect to a host on a given port.

        If the hostname ends with a colon (`:') followed by a number, and
        there is no port specified, that suffix will be stripped off and the
        number interpreted as the port number to use.

        Note: This method is automatically invoked by __init__, if a host is
        specified during instantiation.

        """
        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if i >= 0:
                host, port = host[:i], host[i+1:]
                try: port = int(port)
                except ValueError:
                    raise socket.error, "nonnumeric port"
        if not port: 
            port = SMTP_PORT
        if self.logfile:
            self.logfile.write('attempting SMTP.connect: %s %d\n' % (host, port))
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if self.logfile:
                    self.logfile.write('SMTP.connect: %s %d\n' % (host, port))
                if bindto:
                    self.sock.bind((bindto, socket.IPPORT_USERRESERVED))
                    self._bindto = bindto
                self._connect(sa, retries)
            except socket.error, msg:
                if self.logfile:
                    self.logfile.write('SMTP.connect fail: %s %d\n' % (host, port))
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        (code, msg) = self.getreply()
        if self.logfile:
            self.logfile.write('SMTP.connect: %s %d\n' % (host, port))
        return (code, msg)

    def _connect(self, addr, retries):
        retry = 0
        while retry < retries:
            try:
                self.sock.connect(addr)
            except socket.error, msg:
                if msg[0] == ECONNREFUSED: # might be busy
                    scheduler.sleep(2)
                    continue
                else:
                    raise
            else:
                return
            retry += 1

    def send(self, s):
        """Send string to the server."""
        if self.logfile:
            self.logfile.write('send: %r\n' % (s,))
        if self.sock:
            try:
                self.sock.sendall(s)
            except socket.error:
                self.close()
                raise SMTPServerDisconnected('Server not connected')
        else:
            raise SMTPServerDisconnected('please invoke connect() first')

    def putcmd(self, cmd, args=""):
        """Send a command to the server."""
        if args == "":
            str = '%s%s' % (cmd, CRLF)
        else:
            str = '%s %s%s' % (cmd, args, CRLF)
        self.send(str)

    def getreply(self):
        """Get a reply from the server.

        Returns a tuple consisting of:

          - server response code (e.g. '250', or such, if all goes well)
            Note: returns -1 if it can't read response code.

          - server response string corresponding to response code (multiline
            responses are converted to a single, multiline string).

        Raises SMTPServerDisconnected if end-of-file is reached.
        """
        resp=[]
        if self.file is None:
            self.file = self.sock.makefile('rb')
        while 1:
            try:
                line = self.file.readline()
            except IOError, err:
                if err[0] == EINTR:
                    continue
                else:
                    raise
            if line == '':
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed")
            if self.logfile:
                self.logfile.write('reply: %r\n' % (line,))
            resp.append(line[4:].strip())
            code=line[:3]
            # Check that the error code is syntactically correct.
            # Don't attempt to read a continuation line if it is broken.
            try:
                errcode = int(code)
            except ValueError:
                errcode = -1
                break
            # Check if multiline response.
            if line[3:4]!="-":
                break
        errmsg = "\n".join(resp)
        if self.logfile:
            self.logfile.write('reply: retcode (%s); Msg: %s\n' % (errcode,errmsg))
        return errcode, errmsg

    def docmd(self, cmd, args=""):
        """Send a command, and return its response code."""
        self.putcmd(cmd,args)
        return self.getreply()

    # std smtp commands
    def helo(self, name=''):
        """SMTP 'helo' command.
        Hostname to send for this command defaults to the FQDN of the local
        host.
        """
        name = name or self._bindto
        if name:
            self.putcmd("helo", name)
        else:
            self.putcmd("helo", socket.getfqdn())
        (code,msg)=self.getreply()
        self.helo_resp=msg
        return (code,msg)

    def ehlo(self, name=''):
        """ SMTP 'ehlo' command.
        Hostname to send for this command defaults to the FQDN of the local
        host.
        """
        self.esmtp_features = {}
        name = name or self._bindto
        if name:
            self.putcmd("ehlo", name)
        else:
            self.putcmd("ehlo", socket.getfqdn())
        (code,msg)=self.getreply()
        # According to RFC1869 some (badly written)
        # MTA's will disconnect on an ehlo. Toss an exception if
        # that happens -ddm
        if code == -1 and len(msg) == 0:
            self.close()
            raise SMTPServerDisconnected("Server not connected")
        self.ehlo_resp=msg
        if code != 250:
            return (code,msg)
        self.does_esmtp=1
        #parse the ehlo response -ddm
        resp=self.ehlo_resp.split('\n')
        del resp[0]
        for each in resp:
            # To be able to communicate with as many SMTP servers as possible,
            # we have to take the old-style auth advertisement into account,
            # because:
            # 1) Else our SMTP feature parser gets confused.
            # 2) There are some servers that only advertise the auth methods we
            #    support using the old style.
            auth_match = OLDSTYLE_AUTH.match(each)
            if auth_match:
                # This doesn't remove duplicates, but that's no problem
                self.esmtp_features["auth"] = self.esmtp_features.get("auth", "") \
                        + " " + auth_match.groups(0)[0]
                continue

            # RFC 1869 requires a space between ehlo keyword and parameters.
            # It's actually stricter, in that only spaces are allowed between
            # parameters, but were not going to check for that here.  Note
            # that the space isn't present if there are no parameters.
            m=re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*)',each)
            if m:
                feature=m.group("feature").lower()
                params=m.string[m.end("feature"):].strip()
                if feature == "auth":
                    self.esmtp_features[feature] = self.esmtp_features.get(feature, "") \
                            + " " + params
                else:
                    self.esmtp_features[feature]=params
        return (code,msg)

    def has_extn(self, opt):
        """Does the server support a given SMTP service extension?"""
        return self.esmtp_features.has_key(opt.lower())

    def help(self, args=''):
        """SMTP 'help' command.
        Returns help text from server."""
        self.putcmd("help", args)
        return self.getreply()

    def rset(self):
        """SMTP 'rset' command -- resets session."""
        return self.docmd("rset")

    def noop(self):
        """SMTP 'noop' command -- doesn't do anything :>"""
        return self.docmd("noop")

    def mail(self,sender,options=[]):
        """SMTP 'mail' command -- begins mail xfer session."""
        optionlist = ''
        if options and self.does_esmtp:
            optionlist = ' ' + ' '.join(options)
        self.putcmd("mail", "FROM:%s%s" % (quoteaddr(sender) ,optionlist))
        return self.getreply()

    def rcpt(self,recip,options=[]):
        """SMTP 'rcpt' command -- indicates 1 recipient for this mail."""
        optionlist = ''
        if options and self.does_esmtp:
            optionlist = ' ' + ' '.join(options)
        self.putcmd("rcpt","TO:%s%s" % (quoteaddr(recip),optionlist))
        return self.getreply()

    def data(self,msg):
        """SMTP 'DATA' command -- sends message data to server.

        Automatically quotes lines beginning with a period per rfc821.
        Raises SMTPDataError if there is an unexpected reply to the
        DATA command; the return value from this method is the final
        response code received when the all data is sent.
        """
        self.putcmd("data")
        (code,repl)=self.getreply()
        if self.logfile:
            self.logfile.write("data: %s %s\n" % (code,repl))
        if code != 354:
            raise SMTPDataError(code,repl)
        else:
            q = quotedata(msg)
            if q[-2:] != CRLF:
                q = q + CRLF
            q = q + "." + CRLF
            self.send(q)
            (code,msg)=self.getreply()
            if self.logfile:
                self.logfile.write("data: %s %r\n" % (code,msg))
            return (code,msg)

    def verify(self, address):
        """SMTP 'verify' command -- checks for address validity."""
        self.putcmd("vrfy", quoteaddr(address))
        return self.getreply()
    # a.k.a.
    vrfy=verify

    def expn(self, address):
        """SMTP 'verify' command -- checks for address validity."""
        self.putcmd("expn", quoteaddr(address))
        return self.getreply()

    # some useful methods

    def login(self, user, password):
        """Log in on an SMTP server that requires authentication.

        The arguments are:
            - user:     The user name to authenticate with.
            - password: The password for the authentication.

        If there has been no previous EHLO or HELO command this session, this
        method tries ESMTP EHLO first.

        This method will return normally if the authentication was successful.

        This method may raise the following exceptions:

         SMTPHeloError            The server didn't reply properly to
                                  the helo greeting.
         SMTPAuthenticationError  The server didn't accept the username/
                                  password combination.
         SMTPException            No suitable authentication method was
                                  found.
        """

        def encode_cram_md5(challenge, user, password):
            challenge = base64.decodestring(challenge)
            response = user + " " + hmac.HMAC(password, challenge).hexdigest()
            return encode_base64(response, eol="")

        def encode_plain(user, password):
            return encode_base64("%s\0%s\0%s" % (user, user, password), eol="")


        AUTH_PLAIN = "PLAIN"
        AUTH_CRAM_MD5 = "CRAM-MD5"
        AUTH_LOGIN = "LOGIN"

        if self.helo_resp is None and self.ehlo_resp is None:
            if not (200 <= self.ehlo()[0] <= 299):
                (code, resp) = self.helo()
                if not (200 <= code <= 299):
                    raise SMTPHeloError(code, resp)

        if not self.has_extn("auth"):
            raise SMTPException("SMTP AUTH extension not supported by server.")

        # Authentication methods the server supports:
        authlist = self.esmtp_features["auth"].split()

        # List of authentication methods we support: from preferred to
        # less preferred methods. Except for the purpose of testing the weaker
        # ones, we prefer stronger methods like CRAM-MD5:
        preferred_auths = [AUTH_CRAM_MD5, AUTH_PLAIN, AUTH_LOGIN]

        # Determine the authentication method we'll use
        authmethod = None
        for method in preferred_auths:
            if method in authlist:
                authmethod = method
                break

        if authmethod == AUTH_CRAM_MD5:
            (code, resp) = self.docmd("AUTH", AUTH_CRAM_MD5)
            if code == 503:
                # 503 == 'Error: already authenticated'
                return (code, resp)
            (code, resp) = self.docmd(encode_cram_md5(resp, user, password))
        elif authmethod == AUTH_PLAIN:
            (code, resp) = self.docmd("AUTH",
                AUTH_PLAIN + " " + encode_plain(user, password))
        elif authmethod == AUTH_LOGIN:
            (code, resp) = self.docmd("AUTH",
                "%s %s" % (AUTH_LOGIN, encode_base64(user, eol="")))
            if code != 334:
                raise SMTPAuthenticationError(code, resp)
            (code, resp) = self.docmd(encode_base64(password, eol=""))
        elif authmethod == None:
            raise SMTPException("No suitable authentication method found.")
        if code not in [235, 503]:
            # 235 == 'Authentication successful'
            # 503 == 'Error: already authenticated'
            raise SMTPAuthenticationError(code, resp)
        return (code, resp)

    def starttls(self, keyfile = None, certfile = None):
        """Puts the connection to the SMTP server into TLS mode.

        If the server supports TLS, this will encrypt the rest of the SMTP
        session. If you provide the keyfile and certfile parameters,
        the identity of the SMTP server and client can be checked. This,
        however, depends on whether the socket module really checks the
        certificates.
        """
        (resp, reply) = self.docmd("STARTTLS")
        if resp == 220:
            sslobj = socket.ssl(self.sock, keyfile, certfile)
            self.sock = SSLFakeSocket(self.sock, sslobj)
            self.file = SSLFakeFile(sslobj)
        return (resp, reply)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[],
                 rcpt_options=[]):
        """This command performs an entire mail transaction.

        The arguments are:
            - from_addr    : The address sending this mail.
            - to_addrs     : A list of addresses to send this mail to.  A bare
                             string will be treated as a list with 1 address.
            - msg          : The message to send.
            - mail_options : List of ESMTP options (such as 8bitmime) for the
                             mail command.
            - rcpt_options : List of ESMTP options (such as DSN commands) for
                             all the rcpt commands.

        If there has been no previous EHLO or HELO command this session, this
        method tries ESMTP EHLO first.  If the server does ESMTP, message size
        and each of the specified options will be passed to it.  If EHLO
        fails, HELO will be tried and ESMTP options suppressed.

        This method will return normally if the mail is accepted for at least
        one recipient.  It returns a dictionary, with one entry for each
        recipient that was refused.  Each entry contains a tuple of the SMTP
        error code and the accompanying error message sent by the server.

        This method may raise the following exceptions:

         SMTPHeloError          The server didn't reply properly to
                                the helo greeting.
         SMTPRecipientsRefused  The server rejected ALL recipients
                                (no mail was sent).
         SMTPSenderRefused      The server didn't accept the from_addr.
         SMTPDataError          The server replied with an unexpected
                                error code (other than a refusal of
                                a recipient).

        Note: the connection will be open even after an exception is raised.

        Example:

         >>> import smtplib
         >>> s=smtplib.SMTP("localhost")
         >>> tolist=["one@one.org","two@two.org","three@three.org","four@four.org"]
         >>> msg = '''\\
         ... From: Me@my.org
         ... Subject: testin'...
         ...
         ... This is a test '''
         >>> s.sendmail("me@my.org",tolist,msg)
         { "three@three.org" : ( 550 ,"User unknown" ) }
         >>> s.quit()

        In the above example, the message was accepted for delivery to three
        of the four addresses, and one was rejected, with the error code
        550.  If all addresses are accepted, then the method will return an
        empty dictionary.

        """
        if self.helo_resp is None and self.ehlo_resp is None:
            if not (200 <= self.ehlo()[0] <= 299):
                (code,resp) = self.helo()
                if not (200 <= code <= 299):
                    raise SMTPHeloError(code, resp)
        esmtp_opts = []
        if self.does_esmtp:
            # Hmmm? what's this? -ddm
            # self.esmtp_features['7bit']=""
            if self.has_extn('size'):
                esmtp_opts.append("size=" + `len(msg)`)
            for option in mail_options:
                esmtp_opts.append(option)

        (code,resp) = self.mail(from_addr, esmtp_opts)
        if code != 250:
            self.rset()
            raise SMTPSenderRefused(code, resp, from_addr)
        senderrs={}
        if isinstance(to_addrs, types.StringTypes):
            to_addrs = [to_addrs]
        for each in to_addrs:
            (code,resp)=self.rcpt(each, rcpt_options)
            if (code != 250) and (code != 251):
                senderrs[each]=(code,resp)
        if len(senderrs)==len(to_addrs):
            # the server refused all our recipients
            self.rset()
            raise SMTPRecipientsRefused(senderrs)
        (code,resp) = self.data(msg)
        if code != 250:
            self.rset()
            raise SMTPDataError(code, resp)
        #if we got here then somebody got our mail
        return senderrs

    def close(self):
        """Close the connection to the SMTP server."""
        if self.file:
            self.file.close()
        self.file = None
        if self.sock:
            self.sock.close()
        self.sock = None

    def quit(self):
        """Terminate the SMTP session."""
        rv = self.docmd("QUIT")
        self.close()
        return rv

class Envelope(object):
    """Envelope([mail_from], [recpt_list])
An envelope holds an SMTP conversation from the MAIL FROM command to the end of
a DATA part.  It may be re-sent by calling the 'send()' method with an SMTP
connection object.  The message body can be parsed by passing in an 'email'
parser object to the 'parse()' method."""

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
'email' package Message tree."""
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


def get_mailer(host="", port=SMTP_PORT, logfile=None):
    return SMTP(str(host), int(port), logfile=logfile)


def test(argv):
    def prompt(prompt):
        return raw_input(prompt+": ")

    fromaddr = prompt("From")
    toaddrs  = prompt("To")
    mailhost  = prompt("mailhost")
    print "Enter message, end with ^D:"
    msg = 'From: %s\nTo: %s\nSubject: test message\n\n' % (fromaddr, toaddrs)
    while 1:
        line = raw_input("> ")
        if not line:
            break
        msg = msg + line
    server = SMTP()
    server.connect(mailhost, 25)
    server.sendmail(fromaddr, toaddrs.split(","), msg)
    server.quit()


# Test the sendmail method, which tests most of the others.
# Note: This always sends to localhost.
if __name__ == '__main__':
    import sys
    import timing 
    test(sys.argv)


