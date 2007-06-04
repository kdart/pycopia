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
This module defines the ScriptManager class. This is used to manage
running shell scripts on a remote POSIX device, while keeping the scripts
in your local storage.

"""

import os

import expect

class ScriptSetEntry(object):
    """
This is the script to manage. Don't use this class. Use the ScriptManger
add_script() method instead.

    """
    def __init__(self, name, script, rvset=None):
        self.name = name
        self.script = script
        self.rvset = rvset
        self.pushed = 0

    def clear_script(self):
        self.script = None

    def __str__(self):
        return "ScriptSetEntry:\n name=%s\n script=%s\n rvset=%s\n pushed=%d\n" % \
            (self.name, self.script, self.rvset, self.pushed)


class ScriptManager(expect.Expect):
    """
An instance of this class manages "stuffing", running, and checking
results of shell scripts on remote POSIX shells.

Usage:
ss = ScriptManager(procobject, [prompt], [timeout])

Where console is an Console.Console instance or a Telnet instance, which
should already be connected. 

Methods:

add_script(pathname, script, matchset)
    Adds a script to a set of scripts that this instance manages.
    The pathname is the name of the script on the remote system, and also
    servers as the index for the other methods.
    the script parameter is the actual script, as a string.
    the matchset should be a list of regular expressions that match
    possible outputs of the script.

push_script(name)
    Stuffs the named script through the connection to the remote shell.
    This is run automatically by the run_script method if it has not
    already been pushed.

run_script(name)
    runs the named script on the romote system. Return an tuple of (index,
    re_matchobject, text) as matched by the matchset. See the
    documentation for telnetlib.Telnet.expect() for details.

    """

    def __init__(self, fo=None, prompt="$", timeout=30.0):
        expect.Expect.__init__(self, fo, prompt, timeout)
        self.scriptset = {}

    def add_script(self, name, script, rvset=None):
        """
add_script(name, script, rvset)
Adds a script to the set to be managed. You supply a name that will be
used to reference this script (and is used for the file name on the remote
host), the script itself as a string, and an optional "rvset".  The rvset
is a python list of regular expressions matching strings that the main
script could possibly emit.  These will be matched when the script is run
allowing you to take different actions in you controlling python script
depending on the returned value.

        """
        self.scriptset[name] = ScriptSetEntry(name, script, rvset)
    
    def load_script(self, pathname, rvset=None):
        """load_script(filename, [rvset])
        loads the file given by the filename parameter if not already loaded."""
        name = os.path.basename(pathname)
        if self.scriptset.has_key(name):
            return
        body = open(pathname).read()
        self.add_script(name, body, rvset)

    def has_script(self, name):
        return self.scriptset.has_key(name)

    def clear_script(self, name):
        if self.scriptset.has_key(name):
            del self.scriptset[name]


    def push_script(self, name):
        """
    push_script(name)
    Pushes the named script down to the device, and makes it runnable (+x mode).
        """
        sse = self.scriptset[name]
        self.send("\r")
        self.wait_for_prompt()
        self.send("cat - > /tmp/%s\r" % sse.name)
        # delay between lines to try and avoid serial port overruns.
        for line in sse.script.split("\n"):
            self.send(line+"\n")
            self.delay(1)
        self.send(chr(4)) # ^D
        self.send("\r")
        self.wait_for_prompt()
        self.send("chmod +x /tmp/%s\r" % sse.name)
        rv = self.wait_for_prompt()
        sse.pushed = 1
        sse.clear_script() # save space
        return rv
    
    def write_file(self, path, body):
        self.send("\r")
        self.wait_for_prompt()
        self.send("cat - > %s\r" % path)
        self.delay(0.2)
        self.send(body)
        self.send("\n")
        self.send(chr(4)) # ^D
        self.send("\r")
        self.wait_for_prompt()


    def run_script(self, name, async=0):
        """
run_script(name, [asyncflag])
Runs the named script on the remote device. If it has not been pushed
it will be pushed first. 
If an rvset is included, this will return a match object of the pattern from
the set that matched (and will have its listindex attribute set to the position
in that list).  if the asyncflag is given (evaluates to true), the script is
run in the background on the remote machine.

        """
        sse = self.scriptset[name]
        if not sse.pushed:
            self.push_script(name)
        if not sse.pushed: # not connected?
            raise expect.ExpectError, "ScriptManager: tried to run script that is not pushed."
        if async:
            self.send("/tmp/%s &\r" % name) # invoke the script
            self.wait_for_prompt()
            return None
        #else
        self.send("/tmp/%s\r" % name) # invoke the script
        if sse.rvset:
            mo = self.expect(sse.rvset)
            return mo
        else: # no return value checks
            self.wait_for_prompt()
            return None


    def pass_or_fail(self, name):
        """
Run a script that has simple pass-fail patterns. Return true, or false.
The rvset should include two patterns. The first pattern in the rvset
(return-value-set) should match a true, or positive, condition. The second
pattern should match a false, or negative, condition. Raises an exception
if script could not be run at all.

        """
        if not self.scriptset[name].pushed:
            self.push_script(name)
        if not self.scriptset[name].pushed: # not connected?
            raise RuntimeError, "could not push script to device"
        self.send("%s\r" % name)
        mo = self.expect(self.scriptset[name].rvset, 10.0)
        self.discard()
        return not mo.listindex # force boolean

    def exit(self):
        rv = None
        self.send("\rexit\r")
        try: # fd might have gone away by now.
            rv = self.read() # this won't block now due to eof condition.
        except:
            pass
        return rv

