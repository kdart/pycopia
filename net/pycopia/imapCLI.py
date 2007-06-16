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
Defines an interactive command line that wraps an IMAP session.

"""

import sys, os
import imaplib

from pycopia import CLI
from pycopia import UI
from pycopia import tty

PROMPT = "imap> "

class ImapCLI(CLI.BaseCommands):

    def initialize(self):
        self._client = None

    def finalize(self):
        if self._client:
            self._client.logout()
            self._client = None
    
    def except_hook(self, ex, val, tb):
        self._print(ex, val)

    def _print_msg(self, rp):
        res, data = rp
        if res == "OK":
            for it in data:
                self._print(it)
        else:
            self._print("%s: %s" % (res, "\n".join(map(str, data))))

    def _setprompt(self, host=None):
        if host:
            self._environ["PS1"] = "imap [%s]> " % (host,)
        else:
            self._environ["PS1"] = PROMPT

    def connect(self, argv):
        """connect [-s <bindto>] <host> [<port>]
    Where <host> is the IMAP server to connect to, <port> is the TCP port to use
    (defaults to 143), and <bindto> is the local IP address to source from."""
        bindto = None
        port = 143

        optlist, longopts, args = self.getopt(argv, "s:hp:")
        for opt, val in optlist:
            if opt == "-s":
                bindto = val
            elif opt == "-h":
                self._print(self.connect.__doc__)
                return
            elif opt == "-p":
                try:
                    port = int(val)
                except ValueError:
                    self._print(self.connect.__doc__)
                    return
        if len(args) < 1:
            host = "localhost"
        else:
            host = args[0]
        if len(args) > 1:
            port = int(args[1])
        if self._client:
            self._print("warning: closing existing connection.")
            self.logout()
        self._client = imaplib.IMAP4(host, port)
        self._setprompt(host)

    def logout(self, argv=None):
        """logout
    Quits the IMAP session."""
        if self._client is None:
            raise CLI.CommandQuit
        self._print_msg(self._client.logout())
        self._client = None
        self._setprompt(None)
    quit = logout

    def noop(self, argv):
        """noop
    Sends a NOOP IMAP command. Does nothing."""
        self._print_msg(self._client.noop())

    def append(self, argv):
        """append [-b mailbox] [-f flags] [-d date_time] message
    Append message to named mailbox."""
        mailbox = None
        flags = None
        date_time = None
        opts, longopt, args = self.getopt(argv, "b:f:d:")
        for opt, val in opts:
            if opt == "-b":
                mailbox = val
            elif opt == "-f":
                flags = val
            elif opt == "-d":
                date_time = val
        if not args:
            print self.append.__doc__
            return
        message = " ".join(args) + "\n" # XXX
        self._print_msg(self._client.append(mailbox, flags, date_time, message))

    def check(self, argv):
        """check
    Checkpoint a mailbox on the server."""
        self._print_msg(self._client.check())

    def authenticate(self, argv):
        """authenticate <authtype>
    Authenticate the connection, using the specified auth type. Must be in capabilities."""
        pass
    
    def login(self, argv):
        """login [<username>]
    Identify client using plaintext password."""
        if len(argv) > 1:
            USER = argv[1]
        else:
            USER = tty.getuser()
        PASS = tty.getpass()
        self._print_msg(self._client.login(USER, PASS))

    def close(self, argv):
        """close
    Close the currently selected mailbox."""
        self._print_msg(self._client.close())
    
    def select(self, argv):
        """select [-r] [<mailbox>]
    Select a mailbox. Default is INBOX. The -r option makes it read-only."""
        readonly = None
        opts, longs, args = self.getopt(argv, "r")
        for opt, val in opts:
            if opt == "-r":
                readonly = True
        if args:
            mbox = args[0]
        else:
            mbox = "INBOX"
        self._print_msg(self._client.select(mbox, readonly))

    def status(self, argv):
        """status <mailbox> [<statusdata>...]
    Request named status conditions for mailbox. 

      The currently defined status data items that can be requested are:

      MESSAGES       The number of messages in the mailbox.

      RECENT         The number of messages with the \Recent flag set.

      UIDNEXT        The next UID value that will be assigned to a new
                     message in the mailbox.  It is guaranteed that this
                     value will not change unless new messages are added
                     to the mailbox; and that it will change when new
                     messages are added even if those new messages are
                     subsequently expunged.

      UIDVALIDITY    The unique identifier validity value of the
                     mailbox.

      UNSEEN         The number of messages which do not have the \Seen
                     flag set.
    """
        mbox = argv[1]
        if len(argv) > 2:
            names = "(%s)" % " ".join(map(lambda s: s.upper(), argv[2:]))
        else:
            names = "(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)"
        self._print_msg(self._client.status(mbox, names))

    def list(self, argv):
        """list <directory> [pattern]
    List mailbox names in directory matching pattern."""
        directory = argv[1]
        if len(argv) > 2:
            pattern = argv[2]
        else:
            pattern = "*"
        self._print_msg(self._client.list(directory, pattern))

    def expunge(self, argv):
        """expunge
    Permanently remove deleted items from selected mailbox."""
        self._print_msg(self._client.expunge())

    def namespace(self, argv):
        """namespace
    Print IMAP namespaces ala rfc2342."""
        self._print_msg(self._client.namespace())
        
    def create(self, argv):
        """create <mailbox>
    Create a new mailbox."""
        mbox = argv[1]
        self._print_msg(self._client.create(mbox))

    def delete(self, argv):
        """delete <mailbox>
    Delete a named mailbox."""
        mbox = argv[1]
        self._print_msg(self._client.delete(mbox))

    def login_cram_md5(self, argv):
        """login_cram_md5 [<user>]
    Force logging in using CRAM_MD5."""
        if len(argv) > 1:
            USER = argv[1]
        else:
            USER = tty.getuser()
        PASS = tty.getpass()
        self._print_msg(self._client.login_cram_md5(USER, PASS))

    def rename(self, argv):
        """rename <oldname> <newname>
    Rename a mailbox from oldname to newname."""
        oldname = argv[1]
        newname = argv[2]
        self._print_msg(self._client.rename(oldname, newname))

    def subscribe(self, argv):
        """subscribe <mailbox>
    Subscribe to a mailbox."""
        mbox = argv[1]
        self._print_msg(self._client.subscribe(mbox))

    def unsubscribe(self, argv):
        """unsubscribe <mailbox>
    Unsubscribe from a mailbox."""
        mbox = argv[1]
        self._print_msg(self._client.unsubscribe(mbox))

# TODO:
# copy(message_set, new_mailbox)
# fetch(message_set, message_parts)
# getacl(mailbox)
# getquota(root)
# getquotaroot(mailbox)
# lsub(directory='""', pattern='*')
# partial(message_num, message_part, start, length)
# proxyauth(user)
# search(charset, *criteria)
# setacl(mailbox, who, what)
# setquota(root, limits)
# sort(sort_criteria, charset, *search_criteria)
# store(message_set, command, flags)
# uid(command, *args)
# xatom(name, *args)

    # extra non-protocol methods
    def capabilities(self, argv):
        """capabilities
    Print the servers capability string."""
        for cap in self._client.capabilities:
            self._print("   ", cap)

    def state(self, argv):
        """state
    Print the servers current state."""
        self._print(self._client.state)

    def debuglevel(self, argv):
        """debuglevel <n>
    Sets the IMAP client debug level (causes message to print to stdout)."""
        self._client.debug = int(argv[1])

    def raw(self, argv):
        """raw <data>
    Sends arbitrary data to server."""
        self._client.send(" ".join(argv[1:]))



def imapcli(argv):
    """imapcli [-h|--help] [host] [port]

Provides an interactive session at a protocol level to an IMAP server. 
    """
    import getopt
    port = imaplib.IMAP4_PORT
    sourcefile = None
    paged = False
    try:
        optlist, args = getopt.getopt(argv[1:], "hp:s:g", 
                        ["help", "port", "script="])
    except getopt.GetoptError:
            print imapcli.__doc__
            return
    for opt, val in optlist:
        if opt == "-s" or opt == "--script":
            sourcefile = val
        elif opt == "-h" or opt == "--help":
            print imapcli.__doc__
            return
        elif opt == "-g":
            paged = True
        elif opt == "-p" or opt == "--port":
            try:
                port = int(val)
            except ValueError:
                print imapcli.__doc__
                return

    theme = UI.DefaultTheme(PROMPT)
    parser = CLI.get_cli(ImapCLI, paged=paged, theme=theme)
    if len(args) > 0:
        if len(args) > 1:
            port = int(args[1])
        host = args[0]
    else:
        host = ""
    if host:
        parser.commands.connect(["connect", host, port])
    else:
        parser.commands._print("Be sure to run 'connect' before anything else.\n")
    if sourcefile:
        try:
            parser.parse(sourcefile)
        except CLI.CommandQuit:
            pass
    else:
        parser.interact()


if __name__ == "__main__":
    imapcli(sys.argv)

