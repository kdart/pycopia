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
Factory for getting a wrapper for the telnet program.

"""


import proctools
import expect


try:
    TELNET = proctools.which("telnet")
except ValueError:
    raise ImportError, "telnet program not found!"

TELNET_OPTIONS = '-8c'

class TelnetExpect(expect.Expect):
    def command(self, cmd):
        """Perform telnet command. Leaves telnet in online mode."""
        self.send(chr(29)) # XXX settable escape char
        self.expect("telnet>")
        self.send(cmd+"\r")

    def send_break(self):
        self.command("send brk")

    def death_callback(self, deadtelnet):
        if self._log:
            self._log.write("telnet exited: %s" % (deadtelnet.exitstatus))
        self.close()

    def login(self, user, password=None):
        if password is None:
            import getpass
            password = getpass.getpass("Password: ")
        self.expect("login:", timeout=20)
        self.send(user+"\r")
        self.expect("assword:", timeout=20)
        self.send(password+"\r")
        self.wait_for_prompt()

    def quit(self):
        self.command("quit")
        rv = self.readline()
        self.close()
        return rv
    exit = quit


def get_expect(host, port=23, user=None, password=None, prompt=None, callback=None, 
        logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s %s %s" % (TELNET, TELNET_OPTIONS, extraoptions, host, port)
    telnetproc = pm.spawnpty(command, logfile=logfile, async=async)
    tn = TelnetExpect(telnetproc)
    telnetproc.set_callback(callback or tn.death_callback)
    tn.set_prompt(prompt or "$")
    if password is not None:
        tn.login(user, password)
    return tn

def get_telnet(host, port=23, user=None, password=None, prompt=None, callback=None, 
        logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s %s %s" % (TELNET, TELNET_OPTIONS, extraoptions, host, port)
    return pm.spawnpty(command, logfile=logfile, callback=callback, async=async)

def _test(argv):
    pass # XXX

if __name__ == "__main__":
    import sys
    _test(sys.argv)

