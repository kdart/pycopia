#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#        Copyright (C) 2007    Keith Dart <keith@kdart.com>
#
#        This library is free software; you can redistribute it and/or
#        modify it under the terms of the GNU Lesser General Public
#        License as published by the Free Software Foundation; either
#        version 2.1 of the License, or (at your option) any later version.
#
#        This library is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
#        Lesser General Public License for more details.

"""
Web server using FCGI interface of lighttpd, adapted to WSGI.
"""


import sys
import os
import getopt
import cgitb

from pycopia.OS import procfs
from pycopia import passwd
from pycopia import basicconfig
from pycopia.WWW import framework

from pycopia.inet.fcgi import FCGIServer


class ProcessManager(object):
    """Defines the process model the server uses."""
    def __init__(self, pwent=None):
        from pycopia import proctools
        self._procmanager = proctools.get_procmanager()
        self._pwent = pwent

    def __call__(self, func):
        self._procmanager.submethod(func, pwent=self._pwent)


# Factory function creats a server instance with our interface
# handlers.
def get_server(config):
    username = config.get("USERNAME")
    if username and os.getuid() == 0:
        pwent = passwd.getpwnam(username)
    else:
        pwent = None
    pm = ProcessManager(pwent)

    app = framework.WebApplication(config)

    if config.DEBUG:
        pass
        #from paste.evalexception.middleware import EvalException
        #app = EvalException(app)

    return FCGIServer(app,
            procmanager=pm,
            bindAddress=config.SOCKETPATH,
            umask=config.get("SOCKET_UMASK", 0),
            debug=config.DEBUG)


def check4server(config):
    if os.path.exists(config.SOCKETPATH):
        if os.path.exists(config.PIDFILE):
            pid = int(open(config.PIDFILE).read().strip())
            s = procfs.ProcStat(pid)
            if s and s.command.find(config.SERVERNAME) >= 0:
                return pid
    return 0


def kill_server(config):
    import signal
    pid = check4server(config)
    if pid:
        os.kill(pid, signal.SIGTERM)
        print "Killed %s (%s)." % (config.SERVERNAME, pid)
    else:
        print "%s not running." % (config.SERVERNAME,)


def run_server(argv):
    username = None
    do_daemon = True
    debug = False
    killserver = False
    try:
        optlist, args = getopt.getopt(argv[1:], "dnh?kl:f:p:s:")
    except getopt.GetoptError:
        print run_server._doc % (argv[0],)
        return

    if len(args) > 0:
        servername = args[0]
    else:
        servername = os.path.basename(argv[0])

    logfilename = "/var/log/%s.log" % (servername,)
    cffilename = "/etc/pycopia/%s.conf" % (servername,)
    pidfile="/var/run/%s.pid" % (servername,)
    socketpath = '/tmp/%s.sock' % (servername,)

    for opt, optarg in optlist:
        if opt == "-n":
            do_daemon = False
        elif opt == "-k":
            killserver = True
        elif opt == "-d":
            debug = True
        elif opt == "-u":
            username = optarg
        elif opt == "-l":
            logfilename = optarg
        elif opt == "-f":
            cffilename = optarg
        elif opt == "-p":
            pidfile = optarg
        elif opt == "-s":
            socketpath = optarg
        elif opt in ("-h", "-?"):
            print run_server._doc % (argv[0],)
            return 2

    try:
        config = basicconfig.get_config(cffilename, 
                    CONFIGFILE=cffilename,
                    PIDFILE=pidfile,
                    SOCKETPATH=socketpath,
                    LOGFILENAME=logfilename, 
                    DEBUG=debug, 
                    SERVERNAME=servername)
    except:
        ex, val, tb = sys.exc_info()
        print >>sys.stderr, "Could not get server config: %s (%s)" % (ex, val)
        return 1

    if username:
        config.USERNAME = username

    if killserver:
        kill_server(config)
        return 0

    if check4server(config):
        print >>sys.stderr, "Server %r already running on socket %r." % (servername, socketpath)
        return 1

    if do_daemon and not debug:
        from pycopia import daemonize
        from pycopia import logfile
        lf = logfile.ManagedStdio(logfilename)
        daemonize.daemonize(lf, pidfile=pidfile)
    else: # for controller
        fo = open(pidfile, "w")
        fo.write("%s\n" % (os.getpid(),))
        fo.close()
        del fo

    server = get_server(config)
    return int(server.run())


# Add it this way since server is run in optimized mode.
run_server._doc = """Run the Pycopia FCGI web server.

    %s [-ndk?] [-l <logfile>] [-f <configfile>] [-p <pidfile>] 
                 [-s <socketpath>] [<servername>]

    <servername> determines the configuration, socket, log names, etc. to
    use and defines the FCGI server.

    Options:
         -n = Do NOT become a deamon.
         -d = Enable debugging. Also does not become a deamon.
         -k = Kill a running server.
         -l <filename> = Path name of file to log output to.
         -f <filename> = Path to config file.
         -p <pidfile> = Path to PID file.
         -s <socketpath> = Path to UNIX socket.
    """

