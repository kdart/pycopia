#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2004  Keith Dart <keith@kdart.com>
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
Master web site control. Handles virtual host setups using lighttpd as a
front-end.

This controller also handles the lighttpd process itself. So if you have
it enabled in your site's init.d system you should disable it if they are
configured to listen on the same port.

"""


import sys
import os

from pycopia.WWW import serverconfig

LTCONFIG = "/etc/pycopia/lighttpd/lighttpd.conf"

def start(config):
    if config.DAEMON:
        from pycopia import daemonize
        from pycopia import logfile
        lf = logfile.ManagedStdio(config.LOGFILENAME)
        daemonize.daemonize(lf, pidfile=config.PIDFILE)
    else:
        lf = sys.stdout
        fo = file(config.PIDFILE, "w")
        fo.write("%s\n" % (os.getpid(),))
        fo.close()
    start_proc_manager(config, lf)


def start_proc_manager(config, logfile):
    from pycopia import proctools
    from pycopia import scheduler
    from pycopia import asyncio

    asyncio.start_sigio()
    pm = proctools.get_procmanager()

    for name, serverlist in config.VHOSTS.items():
        for servername in serverlist:
            print "Starting %s for %s." % (servername, name)
            p = pm.spawnpipe("%s/fcgi_server -n %s" % (config.LIBEXEC, servername), persistent=True, logfile=logfile)
            asyncio.poller.register(p)
            scheduler.sleep(1.0) # give it time to init...
    if config.USEFRONTEND:
        lighttpd = proctools.which("lighttpd")
        pm.spawnpipe("%s -D -f %s" % (lighttpd, LTCONFIG), persistent=True, logfile=logfile)
    try:
        while 1:
            asyncio.poller.loop()
            for proc in pm.getprocs():
                if proc.readable():
                    print proc.read(4096)
    except KeyboardInterrupt:
        asyncio.poller.unregister_all()
        for proc in pm.getprocs():
            proc.kill()
            proc.wait()
        if os.path.exists(config.PIDFILE):
            os.unlink(config.PIDFILE)


def stop(config):
    import signal
    if os.path.exists(config.PIDFILE):
        pid = int(open(config.PIDFILE).read().strip())
        os.kill(pid, signal.SIGINT)


def status(config):
    from pycopia.OS import procfs
    if os.path.exists(config.PIDFILE):
        pid = int(open(config.PIDFILE).read().strip())
        s = procfs.ProcStat(pid)
        if s and s.command.find(config.SERVERNAME) >= 0:
            print "Process manager running (pid %s)." % (pid,)
            return 0
    print "Process manager not running."
    return 1


def robots(config):
    from pycopia import passwd
    user = passwd.getpwnam(config.SITEOWNER)
    for vhost, scripts in config.VHOSTS.items():
        rname = os.path.join(config.SITEROOT, vhost, "htdocs", "robots.txt")
        fo = open(rname, "w")
        fo.write(_get_robots_txt(scripts))
        fo.close()
        os.chown(rname, user.uid, user.gid)


def check(config):
    "Check the lighttpd configuration."
    from pycopia import proctools
    pm = proctools.get_procmanager()
    lighttpd = proctools.which("lighttpd")
    proc = pm.spawnpipe("%s -p -f %s" % (lighttpd, LTCONFIG))
    out = proc.read()
    es = proc.wait()
    if es:
        print out
    else:
        print "Error: %s" % (es,)


def _get_robots_txt(scripts):
    s = ["User-agent: *"]
    for name in scripts:
        s.append("Disallow: /%s" % (name,))
    s.append("")
    return "\n".join(s)


# Don't use a docstring since server is run in optimized mode.
_doc = """Pycopia server controller.

%s [-?hnN] [-l <logfilename>] [-p <pidfilename>] [<command>]

Options:
 -? or -h   Show this help.
 -l  override log file name. 
 -p  override pid file name. 
 -n  do NOT become a daemon when starting.
 -d  Enable automatic debugging.
 -N  do NOT start the web server front end (lighttpd).

Where command is one of:
    start   - start all web services and virtual hosts
    stop    - stop a running server
    status  - status of server
    robots  - update robots.txt files.
    check   - Emit the generated lighttpd config, so you can check it.
"""

def main(argv):
    import getopt
    daemonize = True
    frontend = True
    servername = os.path.basename(argv[0])
    logfilename = "/var/log/%s.log" % (servername,)
    pidfilename = "/var/run/%s.pid" % (servername,)
    try:
        optlist, args = getopt.getopt(argv[1:], "?hdnNl:p:")
    except getopt.GetoptError:
        print _doc % (servername,)
        return

    for opt, optarg in optlist:
        if opt in ("-?", "-h"):
            print _doc % (servername,)
            return 2
        elif opt == "-l":
            logfilename = optarg
        elif opt == "-n":
            daemonize = False
        elif opt == "-N":
            frontend = False
        elif opt == "-p":
            pidfilename = optarg
        elif opt == "-d":
            from pycopia import autodebug # Sets up auto debugging handler.

    config = serverconfig.get_site_config()

    config.SERVERNAME = servername
    config.LOGFILENAME = logfilename
    config.PIDFILE = pidfilename
    config.DAEMON = daemonize
    config.USEFRONTEND = frontend
    config.ARGV = args

    if not args:
        return status(config)
    cmd = args[0]

    if cmd.startswith("stat"):
        return status(config)
    elif cmd.startswith("star"):
        return start(config)
    elif cmd.startswith("stop"):
        return stop(config)
    elif cmd.startswith("rob"):
        return robots(config)
    elif cmd.startswith("che"):
        return check(config)
    else:
        print _doc % (servername,)
        return 2


