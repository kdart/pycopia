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
A command shell using Python. This is a mix of Unix shell functionality and Python.
The input is read and interpreted as Python. If a syntax or name error occurs
it is assumed to be a shell style command and it is re-parsed and run as a
system command.

"""

import sys, os, sre, readline, glob
import debugger

import interactive
import proctools
import shparser

sys.ps1 = "pysh$ "

PM = proctools.get_procmanager()

def shell_hook(type, value, tb):
    if type in (NameError, SyntaxError):
        do_shell(value)
    elif type in (IndentationError,):
        sys.__excepthook__(type, value, tb)
    else:
        print
        if __debug__:
            debugger.post_mortem(tb, type, value)
        else:
            import traceback
            traceback.print_exception(type, value, tb)

sys.excepthook = shell_hook

class SubProcess(proctools.Process):
    def __init__(self, argv, logfile=None, env=None, callback=None, pwent=None, merge=None, async=0):
        super(SubProcess, self).__init__(argv[0], logfile, env, callback)
        self.childpid = os.fork()
        if self.childpid == 0:
            try:
                os.execvp(argv[0], argv)
            except:
                ex, val, tb = sys.exc_info()
                print "*** %s: %s" % (argv[0], val)
                os._exit(99)

def _child_exited(ret):
    global _
    _ = ret

def do_command(argv):
    newargv = argv[:1]
    for arg in argv[1:]:
        if glob.has_magic(arg):
            newargv.extend(glob.glob(arg))
        else:
            newargv.append(arg)
    proc = PM.spawnprocess(SubProcess, newargv, logfile=None, env=None,
                callback=_child_exited, persistent=0, merge=1, async=0)
    proc.wait()

SHP = shparser.ShellParser(do_command)

def do_shell(exval):
    SHP.feedline(readline.get_line_buffer())

# this Python should be in interactive mode, so it should be running a prompt now.

