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
Module to provide a callable interface to a Digi PortServer terminal server.

"""

import sys, os, string
import telnetlib
from socket import error


class DigiPort(object):
    """
Instances of this class represent an active connection to DigiPort terminal server.

DigiPort(devicename, password=None, timeout=20)
Supply a device name or IP address, and the administrative password (which
defaults to "dbps"). 

You may use the following methods:

kill(portnum)
    turns specified plug on.

    """
    prompt = "#>"
    def __init__(self, devicename, password=None, timeout=20):
        try:
            self.tn = telnetlib.Telnet(devicename)
        except error, err:
            print "Unable to connect:", err
            return
        if password:
            self.password = password
        else:
            self.password = "dbps"
        self.timeout = timeout
        self.active = 0
        self.login()

    # when printed, print the current status
    def __str__(self):
        return self.getstats()

    def kill(self, port):
        """
kill(portnum)
Clears ("kills") the given port number, making it available for use.
        """
        if self.active:
            self.tn.write("kill tty=%s\r" % (port))
            # eat returned prompt
            self.tn.read_until(DigiPort.prompt, self.timeout)

    def getstats(self):
        """
getstats()
Return a textual report of who is logged in.
        """
        if self.active:
            self.tn.write("who\r")
            return self.tn.read_until(DigiPort.prompt, self.timeout)

    def login(self): 
        """
login()
Logs into the PortServer as the administrative user.
        """
        if not self.active:
            self.tn.read_until("login:", self.timeout)
            self.tn.write("root\r")
            self.tn.read_until("passwd:", self.timeout)
            self.tn.write(self.password + "\r")
            self.tn.read_until(DigiPort.prompt, self.timeout)
            self.active = 1

    def logoff(self):
        """
logoff()
Logs off and closes the TELNET session.
        """
        if self.active:
            self.tn.write("exit\r")
            self.tn.read_until(DigiPort.prompt, 2)
            self.tn.close()
            self.active = 0

    def __del__(self):
        if self.active:
            self.logoff()

# end of DigiPort class

# a CLI class for a DigiPort, to allow interactive remote control.
import cmd

class DigiPortCLI(cmd.Cmd):
    """
DigiPortCLI provides a simple CLI (via the cmd module) to remotely control a
Network Power System device.

    """
    def __init__(self, diginame):
        global socket
        import socket
        cmd.Cmd.__init__(self)
        self.digi = DigiPort(diginame)
        self.prompt = "DigiPort:%s> " % (diginame)
        self.intro = """
Type "help" for a list of commands.
"""
        try:
            import readline
        except ImportError:
            pass

    def emptyline(self):
        pass

    def do_status(self,arg):
        try:
            print self.digi
        except socket.error:
            print "Session timed out!"
            return 1

    def do_kill(self, arg):
        return self._doCommand(self.digi.kill, arg)
    
    def do_exit(self, arg):
# returning a value that evaluates to True will exit the cmdloop
        return 1

    def do_EOF(self, arg):
        return 1

    def _doCommand(self, cmd, arg):
        try:
            if arg[0] in string.digits:
                cmd(string.atoi(arg))
            else:
                cmd(arg)
        except ValueError, err:
            print "Bad argument. Operation not performed."
            print err
        except socket.error:
            print "Session timed out!"
            return 1



if __name__ == '__main__':
    digi = DigiPortCLI("digi_m4d")
    print digi
    digi.cmdloop()
    del digi

