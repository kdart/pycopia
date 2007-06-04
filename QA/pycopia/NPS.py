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
Module to provide a callable interface to a WTI Network Power Switch.

"""

import sys, os, string, re
from types import *
import telnetlib

class NPSPlug(object):
    """
This class represents a plug (port) on an NPS.
    """
    header = "Plug| Name            | Status | Delay | Password        | Default"
    def __init__(self, number, name, status, bootdelay, password, defaultstate):
        self.number = number
        self.name = name
        self.status = status
        self.bootdelay = bootdelay
        self.password = password
        self.defaultstate = defaultstate

    def __str__(self):
        return "%-3d | %-15s | %-6s | %-5d | %-15s | %-4s" % \
            (self.number, self.name, self.status, self.bootdelay, self.password, self.defaultstate)
    
    def __repr__(self):
        return "NPSPlug(%d, %s, %s, %d, %s, %s)" % \
            (self.number, self.name, self.status, self.bootdelay, self.password, self.defaultstate)

# The NPS class is used to control a WTI Network Power Switch via telnet. The NPS commands are:
#
# Commands:
# /H         Display this help screen
# /G         View/Set General Parameters
# /P [n]     View/Set Plug Parameters
# /N         View/Set Network Parameters
# /S         Display Plug Status
# /T         Reset Network Interface
# /R         Relogin as different user
# /D         Set Plugs to default setting
# /X         Exit/Disconnect
# /Boot <n>  Boot Plug n
# /On <n>    Turn On Plug n
# /Off <n>   Turn Off Plug n
# 
# [n] = optional plug name or number
# <n> = required plug name or number
# n+n = plug n and plug n
# n:n = plug n through plug n
# * = all plugs with access
# 

class NPS(object):
    """
Instances of this class represent an active connection to an NPS power controller.
You may use the following methods:

on(plugnum)
    turns specified plug on.

off(plugnum)
    turns specified plug off.

boot(plugnum)
    Power cycles specified plug.

status([plugnum])
    If a plug number is given, return a string that is either "ON", or "OFF".
    If no parameter is given, return a list of tuples of all plug object's status. 

You can also view the current status of the NPS by simply printing the instance.

Note that the NPS will automatically close the connection after two minutes
(the default time). So you should probably delete this object as soon as you
are finished with it.

    """
    prompt = "NPS>"
    def __init__(self, devicename, password="cosine"):
        try:
            self.tn = telnetlib.Telnet(devicename)
        except socket.error, err:
            print "Unable to connect:", err
            return
        self.password = password
        self.timeout = 120
        self.plugs = {}
        self._loginAndGetStats()


    # when printed, print the current status
    def __str__(self):
        s = [NPSPlug.header]
        self.getstats()
        plugs = self.plugs.keys()
        plugs.sort()
        for plug in plugs:
            s.append(str(self.plugs[plug]))
        return string.join(s, "\n")

    def on(self, plug):
        if type(plug) is IntType:
            pl = plug
        elif type(plug) is InstanceType and plug.__class__ is NPSPlug:
            pl = plug.number
            plug.status = "ON"
        elif type(plug) is StringType: # name of attached device stored in NPS
            pl = self._findplugbyname(plug)
        else:
            raise ValueError
        self.tn.write("/On %d,y\r" % (pl))
        # eat returned prompt
        self.tn.read_until(NPS.prompt, 20)


    def off(self, plug):
        if type(plug) is IntType:
            pl = plug
        elif type(plug) is InstanceType and plug.__class__ is NPSPlug:
            pl = plug.number
            plug.status = "OFF"
        elif type(plug) is StringType: # name of attached device stored in NPS
            pl = self._findplugbyname(plug)
        else:
            raise ValueError
        self.tn.write("/Off %d,y\r" % (pl))
        # eat returned prompt
        self.tn.read_until(NPS.prompt, 20)


    def boot(self, plug):
        if type(plug) is IntType:
            pl = plug
        elif type(plug) is InstanceType and plug.__class__ is NPSPlug:
            pl = plug.number
        elif type(plug) is StringType: # name of attached device stored in NPS
            pl = self._findplugbyname(plug)
        else:
            raise ValueError
        self.tn.write("/Boot %d,y\r" % (pl))
        # eat returned prompt
        self.tn.read_until(NPS.prompt, 20)

    def status(self, plug=None):
        self.getstats()
        if plug is None:
            rv = []
            for plug in self.plugs.values():
                rv.append( (plug.number, plug.name, plug.status,) )
            return rv
        # else
        if type(plug) is IntType:
            pl = plug
        elif type(plug) is InstanceType and plug.__class__ is NPSPlug:
            pl = plug.number
        elif type(plug) is StringType: # name of attached device stored in NPS
            pl = self._findplugbyname(plug)
        else:
            raise ValueError
        return self.plugs[pl].status

    def _loginAndGetStats(self): 
        """
Perform the login process by giving the password at the login prompt. Since the
NPS seems to dump its current status without asking for it at this time, might
as well grab that while it's available.

        """
        self.tn.read_until("Password:")
        self.tn.write(self.password + "\r")
        stats = self.tn.read_until(NPS.prompt)
        self._parsestats(stats)

    def getstats(self):
        self.tn.write("/s\r")
        stats = self.tn.read_until(NPS.prompt)
        self._parsestats(stats)

    def _findplugbyname(self, name):
        plugs = self.plugs.values()
        for plug in plugs:
            if plug.name == name:
                return plug.number
        # plug name not found
        raise ValueError, "NPS: plug named '%s' not found in list" % name 
        
    def _parsestats(self, rawstats):
        plug_re = re.compile("^[0-9]")
        lines = string.split(rawstats, "\n")
        for line in lines:
            line = string.strip(line)
            if plug_re.match(line):
                parts = string.split(line, "|")
                number = string.atoi(string.strip(parts[0]))
                name = string.strip(parts[1])
                status = string.strip(parts[2])
                bootdelay = string.atoi(string.strip(string.split(parts[3])[0]))
                password = string.strip(parts[4])
                if password == "(none)":
                    password = None
                defaultstate = string.strip(parts[5])
                self.plugs[number] = NPSPlug(number, name, status, bootdelay, password, defaultstate)
            elif line[:10] == "Disconnect":
                self.timeout = string.atoi(string.strip(string.split(line)[2]))*60

    def logoff(self):
        self.tn.write("/x,y\r")
        self.tn.close()

    def __del__(self):
        self.logoff()

# end of NPS class

# a CLI class for a NPS, to allow interactive remote control.
import cmd
# for socket.error
import socket

class NPSCLI(cmd.Cmd):
    """
NPSCLI provides a simple CLI (via the cmd module) to remotely control a
Network Power System device.

    """
    def __init__(self, npsname):
        cmd.Cmd.__init__(self)
        self.nps = NPS(npsname)
        self.prompt = "NPS:%s> " % (npsname)
        self.intro = """
Network Power System remote control. 
Type "help" for a list of commands.
WARNING: session will fail after NPS's timeout period (default is 2 minutes).
"""
        self.isdigit_re = re.compile('^[0-9]')
        try:
            import readline
        except ImportError:
            pass

    def emptyline(self):
        pass

    def do_status(self,arg):
        try:
            print self.nps
        except socket.error:
            print "Session timed out!"
            return 1

    def do_on(self, arg):
        return self._doCommand(self.nps.on, arg)
    
    def do_off(self, arg):
        return self._doCommand(self.nps.off, arg)

    def do_boot(self, arg):
        return self._doCommand(self.nps.boot, arg)

    def do_exit(self, arg):
# returning a value that evaluates to True will exit the cmdloop
        return 1

    def do_EOF(self, arg):
        return 1

    def _doCommand(self, cmd, arg):
        try:
            if self.isdigit_re.match(arg):
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
    # this test routine does not actually test the power cycling. You'll have
    # to do that by hand.
    nps = NPS("nps")
    print nps
    del nps

