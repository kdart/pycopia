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
Use the 'cu' command to connect to a serial port.

"""

import proctools
import expect

try:
    CU = proctools.which("cu")
except ValueError:
    raise ImportError, "cu program not found!"

CU_OPTIONS = '--parity=none --nostop'

class CUExpect(expect.Expect):
    def command(self, cmd):
        """Perform a cu command. Leaves cu in online mode."""
        self.send("\r~%s" % (cmd,))
    
    def send_break(self):
        self.send("\r~#")

    def death_callback(self, deadcu):
        if self._log:
            self._log.write("cu exited: %s" % (deadcu.exitstatus))
        self.close()

def get_cu(port, speed, user=None, password=None, prompt=None, callback=None, 
        logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s -l %s -s %s dir" % (CU, CU_OPTIONS, extraoptions, port, speed)
    cuproc = pm.spawnpty(command, logfile=logfile, async=async)
    cu = CUExpect(cuproc)
    cuproc.set_callback(callback or cu.death_callback)
    cu.set_prompt(prompt or "$")
    if password is not None:
        cu.login(user, password)
    return cu

get_expect = get_cu

def get_serial(port, speed, user=None, password=None, prompt=None, callback=None, 
        logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s -l %s -s %s dir" % (CU, CU_OPTIONS, extraoptions, port, speed)
    cuproc = pm.spawnpty(command, logfile=logfile, async=async)
    return cuproc

def _test(argv):
    pass # XXX

if __name__ == "__main__":
    import sys
    _test(sys.argv)

