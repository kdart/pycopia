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
A simple SMTP server. 


TODO:
This is all single-thread-syncronous for now... should make it async.

"""

import sys
import re
from errno import EINTR, EAGAIN

from pycopia import socket
from pycopia import scheduler

from pycopia.inet.rfc2822 import formatdate
from pycopia.smtp_envelope import Envelope

class ConversationOverException(Exception):
    pass

class DataFinish(StopIteration):
    pass

class TimeoutError(StopIteration):
    pass

CRLF = "\r\n"

# states: command=1, data=2
class SMTPServer(object):
    """SMTPDServer(port=25, logfile=None, parser=None)
An SMTP server object that listens on the specified port. If a 'logfile'
file-like object is supplied the SMTP conversation will be written to it.
If a parser object is supplied then any message body recieved will be
automatically parsed, and any errors returned to the client.  """
    def __init__ (self, port=9025, logfile=None, parser=None):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.file = None
        self.conn = None
        self.envelopes = []
        self.hostname = socket.gethostname()
        self._client = None
        self._callback = None
        self._reset()
        while 1:
            try:
                self.socket.bind(("", self.port))
                break
            except socket.error, msg:
                print >>sys.stderr, "couldn't bind port",self.port," - ",msg,"retrying..."
            scheduler.sleep(5)
        self.socket.listen(50)
        self.conversation = None
        self.logfile = logfile
        self.parser = parser

    def __del__(self):
        self.close()

    def _reset(self):
        self._state = 1
        self.current = None

    def poll(self, timeout=0, conversation=None):
        """poll(timeout=0, conversation=None)
Polls the server, waiting *timeout* seconds (or forever if zero). Returns
one message Envelope object if available.
"""
        self.accept(timeout)
        self.smtp_conversation(conversation)
        if self.envelopes:
            return self.envelopes.pop()
        else:
            return None

    def run(self, callback=None, timeout=0, conversation=None):
        """run(cb=None, timeout=0, conversation=None)
Runs the SMTP server (single thread). If a list object is passed in as the
'conversation' then the SMTP conversation will be stored in it.  If a
callback function is supplied then it will be called for each message
Envelope recieved (with the Envelope object as a parameter)."""
        self._callback = callback
        while 1:
            self.accept(timeout)
            self.smtp_conversation(conversation)

    def get_envelopes(self):
        """get_envelopes()
Returns the stored list of Envelope objects, clearing the list."""
        elist = self.envelopes
        self.envelopes = []
        return elist

    def get_conversation(self):
        """get_conversation()
Fetches the conversation list-object from this server."""
        conversation = self.conversation
        self.conversation = None
        return conversation

    matchaddr = re.compile (".*<(.*)>.*")
    def get_address (self, line):
        match = self.matchaddr.match(line)
        if not match:
            return None
        return match.group(1)

    def accept(self, timeout=60):
        tries = timeout/6
        count = 0
        self.socket.setblocking(0)
        while 1:
            try:
                conn, self.otheraddr = self.socket.accept()
            except socket.error, why:
                if why[0] == EINTR:
                    continue
                if why[0] == EAGAIN:
                    if timeout > 0 and count > tries:
                        self.socket.setblocking(1)
                        raise TimeoutError, "did not accept() in time."
                    count += 1
                    scheduler.sleep(6)
                    continue
                else:
                    raise
            else:
                break
        self.socket.setblocking(1)
        conn.setblocking(1)
        self.file = conn.makefile()
        self.conn = conn
        return self.file

    def close(self):
        """close()
Closes the server (stops listening)."""
        if self.socket:
            self.socket.close()
            self.socket = None
        if self.file:
            self.file.close()
            self.file = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def conn_close(self):
        self.conn.close()
        self.file.close()
        self.conn = None
        self.file = None
        self._client = None
        self._reset()

    def readline(self):
        while 1:
            try:
                line = self.file.readline()
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        if not line:
            return None, None
        if self.conversation is not None:
            self.conversation.append(("RECV", line))
        if self.logfile:
            self.logfile.write("RECV: %s" % (line,))
        line = line.strip()
        parts = line.split(None, 1)
        command = parts[0]
        args = ''
        if len(parts) > 1:
            args = parts[1]
        return command, args

    def send_line(self, line):
        if self.conversation is not None:
            self.conversation.append(("SENT", line))
        if self.logfile:
            self.logfile.write(("SENT: %s\n" % (line,)))
        try:
            self.conn.send(line + CRLF)
        except IOError:
            raise ConversationOverException

    def smtp_conversation(self, conversation=None):
        self.conversation = conversation # should be a list object
        self.send_line("220 IAF.smtpd4testing (hello from %r) ESMTP" % (self.otheraddr,))
        while 1:
            try:
                command, args = self.readline()
            except IOError:
                self.conn_close()
                break
            if not command:
                self.conn_close()
                break
            method = getattr(self, 'smtp_' + command.upper(), None)
            if not method:
                self.send_line('500 Error: command "%s" not implemented' % command)
                print >>sys.stderr, "no handler for command '%s'" % command
                continue
            try:
                method(args)
            except ConversationOverException:
                self.conn_close()
                break
            except DataFinish:
                if self._callback and self.envelopes:
                    self._callback(self.envelopes.pop())

    def smtp_HELO(self, args):
        self._client = args
        self.send_line ("250 IAF.smtpd4testing")

    def smtp_EHLO(self, args):
        self._client = args
        self.send_line("250-IAF")
        self.send_line("250 SIZE 10485760")

    def smtp_MAIL(self, args):
        if not self._client:
            self.send_line('503 Error: out of sequence command - no HELO')
            return
        fromaddr = self.get_address(args)
        self.current = Envelope(fromaddr)
        self.current.write("Received: from %s (%s) by %s with SMTP ; %s\r\n" % \
                (self._client, self.otheraddr[0], self.hostname, formatdate()))
        self.envelopes.append(self.current)
        self.send_line("250 sender <%r> ok" % fromaddr)

    def smtp_RCPT(self, args):
        if self.current is None or not self.current.mail_from:
            self.send_line('503 Error: out of sequence command')
            return
        rcpt = self.get_address(args)
        if not rcpt:
            self.send_line("501 need recipient")
            return
        self.current.add_rcpt(rcpt)
        self.send_line("250 recipient <%r> ok" % rcpt)

    def smtp_QUIT(self, args):
        if args:
            self.send_line('501 Syntax: QUIT')
            return
        self.send_line("221 %s closing channel" % (self.hostname,))
        raise ConversationOverException

    def smtp_DATA(self, args):
        if self.current is None or not self.current.mail_from:
            self.send_line('503 Error: out of sequence command')
            return
        if not self.current.rcpt_to:
            self.send_line('554 Error: need RCPT command')
            return
        self.send_line ("354 feed me")
        self._state = 2
        while 1:
            line = self.file.readline()
            if self.logfile:
                self.logfile.write(line)
            if line == '.\r\n':
                try:
                    if self.parser:
                        self.current.parse_data(self.parser)
                    self._reset()
                    self.send_line("250 OK")
                except: # parser error
                    ex, val, tb = sys.exc_info()
                    print >>sys.stderr, ex, val
                    self._reset()
                    self.send_line("451 %s (%s)" % (ex, val))
                    break
                raise DataFinish
            self.current.writeln(line.rstrip(CRLF))

    def smtp_RSET(self, args):
        if args:
            self.send_line('501 Syntax: RSET')
            return
        self._reset()
        self.send_line('250 OK')

    def smtp_NOOP(self, arg):
        self.send_line('250 OK')

    def smtp_VRFY(self, arg):
        self.send_line("502 not implemented")

    def smtp_EXPN(self, arg):
        self.send_line("502 not implemented")

    def smtp_HELP(self, arg):
        self.send_line("502 not implemented")


# a cache of listeners
_listeners = {}


# a singleton
class SMTPListener(object):
    def __init__(self, serverhost=None, port=9025, logfile=None, parser=None, forward25=YES):
        # failsafe... check for multiple invocations
        global _listeners
        try:
            _listeners[port]
            raise RuntimeError, "Use the factory function get_smtpd() instead."
        except KeyError:
            pass
        self._serverhost = serverhost
        self._port = port
        self._logfile = logfile
        self._parser = parser
        self._server = None # use start()
        self.forward25 = forward25

    def __del__(self):
        self.stop()

    def kill(self):
        self.stop()
        kill_smtpd(self._port)

    def start(self):
        if not self._server:
            # forward the SMTP port to us
            self._server = SMTPServer(self._port, self._logfile, self._parser)

    def stop(self):
        if self._server:
            self._server.close()
            self._server = None

    def status(self):
        return bool(self._server)

    def get_message(self, timeout=60):
        """returns an Envelope object from the server."""
        if self._server:
            # get envelope (with message) and stash its conversation and client
            # address in it.
            envelope = self._server.poll(timeout, [])
            if envelope is not None:
                envelope.conversation = self._server.get_conversation()
                envelope.otheraddress = self._server.otheraddr
                return envelope
            else:
                envelope = Envelope() # return empty one then, to provide consistent interface.
                envelope.otheraddress = None
                envelope.conversation = self._server.get_conversation()
                return envelope

    def run(self, callback=None, timeout=0, conversation=None):
        self.start()
        if self._server:
            self._server.run(callback, timeout, conversation)


# factory function returns a SMTP listener instance
def get_smtpd(serverhost=None, port=9025, logfile=None, parser=None):
    """get_smtpd(port=9025, logfile=None, parser=None)
Factory function to return an SMTP server object, listening on the specified
port.  The serverhost is where the SMTP port (25) will be listening."""
    global _listeners
    try:
        return _listeners[port]
    except KeyError:
        smtpd = SMTPListener(serverhost, port, logfile, parser)
        _listeners[port] = smtpd
        return smtpd

def kill_smtpd(port=9025):
    """Stops the SMTPDListener."""
    global _listeners
    try:
        del _listeners[port]
    except KeyError:
        pass


if __name__ == "__main__":
    def _print_env(env):
        print env

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 9025
    server = SMTPServer(port)
    try:
        try:
            server.run(_print_env)
        except KeyboardInterrupt:
            pass
    finally:
        server.close()


