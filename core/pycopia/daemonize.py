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

"""The daemonize module contains a function (deamonize) that when run will
cause the current process to detach itself from a controlling terminal and run
in the background (that is, become a Unix daemon).  """

import sys, os

DEVNULL = "/dev/null"

def daemonize(logfile=None, pidfile=None):
    """This forks the current process into a daemon. Takes an optional
    file-like object to write stdout and stderr to. Preferrable this will
    be a logfile.ManagedLog object so that your disk does not fill up.
    """ 

    # Do first fork.
    try: 
        if os.fork() > 0:
            os._exit(0) # Exit first parent.
    except OSError, e: 
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))

    # Decouple from parent environment.
    os.chdir("/") 
    os.umask(0) 
    os.setsid() 

    # Do second fork.
    pid = os.fork()
    if pid > 0:
        if pidfile:
            fo = open(pidfile, "w")
            fo.write("%s\n" % (pid,))
            fo.close()
        os._exit(0)

    # Redirect standard file descriptors.
    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.__stdin__.fileno())
    os.close(sys.__stdout__.fileno())
    os.close(sys.__stderr__.fileno())

    # stdin always from /dev/null
    sys.stdin = open(DEVNULL, 'r')

    # log file is stdout and stderr, otherwise /dev/null
    if logfile is None:
        sys.stdout = open(DEVNULL, 'w')
        sys.stderr = open(DEVNULL, 'w', 0)
    else:
        so = se = sys.stdout = sys.stderr = logfile
        os.dup2(so.fileno(), 1)
        os.dup2(se.fileno(), 2)
    return pid


if __name__ == "__main__":
    import time
    #import logfile
    #lf = logfile.ManagedStdio("/var/tmp/test_daemonize", 1000, 5)
    lf = None
    try:
        daemonize(lf)
    except SystemExit:
        pass
    except:
        import traceback
        ex, val, tb = sys.exc_info()
        print ex, val
        print "----"
        traceback.print_tb(tb)

    else:
        c = 0
        sys.stdout.write('Daemon stdout output\n')
        sys.stdout.write(repr(sys.stdout))
        sys.stdout.write('\n')
        while 1:
            sys.stdout.write('%d: %s\n' % (c, time.asctime()) )
            sys.stdout.flush()
            c += 1
            time.sleep(1)


