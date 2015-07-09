#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""The daemonize module contains a function (deamonize) that when run will
cause the current process to detach itself from a controlling terminal and run
in the background (that is, become a Unix daemon).  """

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

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
    except OSError as e:
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
        sys.stderr = open(DEVNULL, 'wb', 0)
    else:
        so = se = sys.stdout = sys.stderr = logfile
        os.dup2(so.fileno(), 1)
        os.dup2(se.fileno(), 2)
    return pid


if __name__ == "__main__":
    import time
    from pycopia import logfile
    lf = logfile.ManagedStdio("/var/tmp/test_daemonize", 1000, 5)
    #lf = None
    try:
        daemonize(lf)
    except SystemExit:
        pass
    except:
        import traceback
        ex, val, tb = sys.exc_info()
        print (ex, val)
        print ("----")
        traceback.print_tb(tb)

    else:
        c = 0
        sys.stdout.write(b'Daemon stdout output\n')
        sys.stdout.write(repr(sys.stdout).encode("ascii"))
        sys.stdout.write(b'\n')
        while 1:
            sys.stdout.write(('%d: %s\n' % (c, time.asctime())).encode("ascii") )
            sys.stdout.flush()
            c += 1
            time.sleep(1)


