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
Defines an interactive command line that wraps an SMTP session.

"""

import sys, os
import getopt

from pycopia import CLI
from pycopia import UI
from pycopia.inet import SMTP
from pycopia.aid import IF

PROMPT = "smtp> "

class EmailClientCLI(CLI.BaseCommands):
    def message(self, argv):
        """message
    Create a new message object, or edit the existing one. Enters message editing
    mode."""
        pass

    def initialize(self):
        self._client = None
        self._logfile = None

    def finalize(self):
        if self._client:
            self._client.quit()
            self._client = None

    def except_hook(self, ex, val, tb):
        self._print(ex, val)
        if ex is SMTP.SMTPException:
            try:
                self._client.quit()
            except:
                pass
            self._client = None
            self._setprompt(None)

    def _print_msg(self, rp):
        self._print("%s %s" % rp) # a reply tuple (code, msg)

    def _setprompt(self, host=None):
        if host:
            self._environ["PS1"] = "smtp [%s]> " % (host,)
        else:
            self._environ["PS1"] = PROMPT

    def connect(self, argv):
        """connect [-s|--bindto <bindto>] <host> [<port>]
    Where <host> is the mailhost to connect to, <port> is the TCP port to use
    (defaults to 25), and <bindto> is the local IP address to source from."""
        bindto = None
        port = 25
        try:
            optlist, args = getopt.getopt(argv[1:], "s:hp:", 
                            ["bindto=", "help", "port="])
        except getopt.GetoptError:
                self._print(self.connect.__doc__)
                return
        for opt, val in optlist:
            if opt == "-s" or opt == "--bindto":
                bindto = val
            elif opt == "-h" or opt == "--help":
                self._print(self.connect.__doc__)
                return
            elif opt == "-p" or opt == "--port":
                try:
                    port = int(val)
                except ValueError:
                    self._print(self.connect.__doc__)
                    return
        if len(args) < 1:
            self._print(self.connect.__doc__)
            return
        host = args[0]
        if len(args) > 1:
            port = int(args[1])
        if self._client:
            self._print("warning: closing existing connection.")
            self.quit()

        self._client = SMTP.get_mailer(logfile=self._logfile)

        try:
            code, msg = self._client.connect(host, port, bindto)
            self._print("%s %s" % (code, msg))
            self._setprompt(argv[1])
        except:
            self._client = None
            self._print("connect failed!")
            ex, val, tb = sys.exc_info()
            self._print(str(val))

    def quit(self, argv=None):
        """quit
    Quits the SMTP session."""
        if self._client is None:
            raise CommandQuit
        try:
            self._print_msg(self._client.quit())
        except SMTP.SMTPServerDisconnected:
            pass
        self._client = None
        self._setprompt(None)

    def helo(self, argv):
        """helo [<hostname>]"""
        if len(argv) > 1:
            name = argv[1]
        else:
            name = None
        self._print_msg(self._client.helo(name))

    def ehlo(self, argv):
        """ehlo [<hostname>]"""
        if len(argv) > 1:
            name = argv[1]
        else:
            name = None
        self._print_msg(self._client.ehlo(name))

    # name clashes with built-in help
    def smtphelp(self, argv):
        """smtphelp
    Print the help text from the server."""
        self._print_msg(self._client.help())

    def rset(self, argv):
        """rset
    Resets the SMTP server to default state."""
        self._print_msg(self._client.rset())

    def noop(self, argv):
        """noop
    Sends a NOOP SMTP command. Does nothing."""
        self._print_msg(self._client.noop())

    def mail(self, argv):
        """mail <from> [<options>]
    Begin a mail transfer session. Specify the FROM: (return) address."""
        frm = argv[1] ; options = argv[2:]
        self._print_msg(self._client.mail(frm, options))

    def rcpt(self, argv):
        """rcpt <to> [<options>]
    Specify a envelope TO: address."""
        to = argv[1] ; options = argv[2:]
        self._print_msg(self._client.rcpt(to, options))

    def data(self, argv):
        """data
    Specify message data to send. Enters input mode to enter data. End with ^D."""
        msg = self._ui.get_text("Enter data, end with ^D.")
        self._print_msg(self._client.data(msg))

    def vrfy(self, argv):
        """vrfy <name>
    Verify the given name  can be delivered (VRFY command)."""
        self._print_msg(self._client.vrfy(argv[1]))
    verify = vrfy # alias

    def expn(self, argv):
        """expn <address>
    Expand an address (if server permits it)."""
        self._print_msg(self._client.expn(argv[1]))

    # extra non-protocol methods
    def logfile(self, argv):
        """logfile <name>
    Sets the SMTP client log file. protocol messages are sent here. If the name
    is called "close" then any current log file is closed. The special name
    "stdout" may also be used. """
        if len(argv) <= 1:
            if self._logfile:
                self._print("Current logfile is %r." % (self._logfile.name,))
            if self._client:
                lf = self._client.logfile.name
                self._print("Current SMTP logfile is %r." % (lf,))
            return
        fname = argv[1]
        if fname == "close":
            self._logfile = None
            if self._client:
                fo = self._client.logfile
                if fo is not None:
                    self._client.set_logfile(None)
                    if fo is not sys.stdout:
                        fo.close()
            return
        elif fname == "stdout":
            fo = sys.stdout
        else:
            fo = open(fname, "w")
        self._logfile = fo
        if self._client:
            self._client.set_logfile(fo)

    def send(self, argv):
        """send <data>
    Sends arbitrary data to server."""
        self._client.send(" ".join(argv[1:]))

    def putcmd(self, argv):
        """putcmd <command> [args]
    Send any command to the server, with optional arguments."""
        self._client.putcmd(argv[1], " ".join(argv[2:]))
        self._print_msg(self._client.getreply())

    def has_extn(self, argv):
        """has_extn <name>
    Check that the connected server has the named extension."""
        if self._client.has_extn(argv[1]):
            self._print("client has extension.")
        else:
            self._print("client does NOT have extension.")


def smtpcli(argv):
    """smtpcli [-h|--help] [-l|--logfile <logfilename>] [-s|--bindto <portname>] [host] [port]

Provides an interactive session at a protocol level to an SMTP server. 
    """
    bindto = None
    port = 25
    sourcefile = None
    paged = False
    logname = None
    try:
        optlist, args = getopt.getopt(argv[1:], "b:hp:s:l:g", 
                        ["bindto=", "help", "port=", "script=", "logfile="])
    except getopt.GetoptError:
            print smtpcli.__doc__
            return
    for opt, val in optlist:
        if opt == "-b" or opt == "--bindto":
            bindto = val
        if opt == "-l" or opt == "--logfile":
            logname = val
        elif opt == "-s" or opt == "--script":
            sourcefile = val
        elif opt == "-g":
            paged = True
        elif opt == "-h" or opt == "--help":
            print smtpcli.__doc__
            return
        elif opt == "-p" or opt == "--port":
            try:
                port = int(val)
            except ValueError:
                print smtpcli.__doc__
                return

    theme = UI.DefaultTheme(PROMPT)
    parser = CLI.get_cli(EmailClientCLI, paged=paged, theme=theme)
    if len(args) > 0:
        if len(args) > 1:
            port = int(args[1])
        else:
            port = 25
        host = args[0]
    else:
        host = ""
    if logname:
        parser.commands.logfile(["logfile", logname])
    if host:
        parser.commands.connect(["connect"]+IF(bindto, ["-s", bindto], [])+[host, port])
    else:
        parser.commands._print("Be sure to run 'connect' before anything else.\n")

    if sourcefile:
        try:
            parser.parse(sourcefile)
        except CommandQuit:
            pass
    else:
        parser.interact()

if __name__ == "__main__":
    smtpcli(sys.argv)

