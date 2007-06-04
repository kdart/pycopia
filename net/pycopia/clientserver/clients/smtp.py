#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Clients used to test various SMTP related exploits.

"""

from pycopia import clientserver


class SMTPClient(clientserver.TCPClient):
    port = 25
    altport = 9025
    EOL = "\r\n"
    def initialize(self):
        fsm = self.fsm
        fsm.set_default_transition(self._bye, fsm.RESET)
        fsm.add_expression("220 (.*)", fsm.RESET, self._greet, 1)
        fsm.add_expression("250 (.*)", 1, self._mail, 2)
        fsm.add_expression("503 (.*)", 2, self._quit, 6)
        fsm.add_expression("553 (.*)", 2, self._quit, 6)
        fsm.add_expression("250 (.*)", 2, self._rcpt, 3)
        fsm.add_expression("250 (.*)", 3, self._data, 4)
        fsm.add_expression("503 (.*)", 3, self._quit, 6)
        fsm.add_expression("354 (.*)", 4, self._send, 5)
        fsm.add_expression("250 (.*)", 5, self._quit, 6)
        fsm.add_expression("221 (.*)", 6, self._goodbye, fsm.RESET)


    def _bye(self, mo, fsm):
        self.fsm.close()
        raise ClientExit, 1

    def _goodbye(self, mo, fsm):
        raise ClientExit, 0

    def _greet(self, mo, fsm):
        fsm.writeeol("HELO somewhere.com")

    def _mail(self, mo, fsm):
        fsm.writeeol("MAIL FROM: <yourstruly@somewhere.com>")

    def _rcpt(self, mo, fsm):
        fsm.writeeol("RCPT TO: <postmaster>")

    def _quit(self, mo, fsm):
        fsm.writeeol("QUIT")

    def _data(self, mo, fsm):
        fsm.writeeol("DATA")

    def _send(self, mo, fsm):
        fsm.writeeol("""From: "Yours Truly" <yourstruly@somewhere.com>
To: <postmaster@somewhere.com>

Message body.
""".replace("\n", "\r\n"))
        fsm.writeeol('.')


# (msg:"SMTP RCPT TO decode attempt"; flow:to_server,established; content:"rcpt
# to|3A|"; nocase; content:"decode"; distance:0; nocase; pcre:"/^rcpt
# to\:\s*decode/smi"; reference:arachnids,121; reference:bugtraq,2308;
# reference:cve,1999-0203; classtype:attempted-admin; sid:664; rev:15;)
class Client664(SMTPClient):
    def _rcpt(self, mo, fsm):
        fsm.writeeol("RCPT TO: decode")


# (msg:"SMTP sendmail 5.6.5 exploit"; flow:to_server,established; content:"MAIL
# FROM|3A| |7C|/usr/ucb/tail"; nocase; reference:arachnids,122;
# reference:bugtraq,2308; reference:cve,1999-0203; classtype:attempted-user;
# sid:665; rev:8;)
class Client665(SMTPClient):
    def _mail(self, mo, fsm):
        fsm.writeeol("MAIL FROM: |/bin/sh")


