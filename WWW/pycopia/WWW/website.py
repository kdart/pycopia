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

"""
Master web site control. Handles virtual host setups using lighttpd as a
front-end.

This controller also handles the lighttpd process itself. So if you have
it enabled in your site's init.d system you should disable it if they are
configured to listen on the same port. The lighttpd server is run under
the pycopia process manager and will be automatically restarted if it
abnormally exits.

The pycopia web framework provides its own configuration file. Changes
made to any installed lighttpd configuration won't be used.

The lighttpd build was configured like this:

./configure --prefix=/usr --with-fam --with-openssl --with-attr --with-pcre --with-zlib --disable-ipv6

"""


import sys
import os

from pycopia import basicconfig
from pycopia import passwd
from pycopia import socket

LTCONFIG = "/etc/pycopia/lighttpd/lighttpd.conf"
# Master site config. controls all virtual host configuration.
SITE_CONFIG = "/etc/pycopia/website.conf"


def start(config):
    setup(config)
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


def setup(config):
    siteuser = passwd.getpwnam(config.SITEUSER)
    siteowner = passwd.getpwnam(config.SITEOWNER)
    logroot = config.get("LOGROOT", "/var/log/lighttpd")
    fqdn = socket.get_fqdn()
    def _mkdir(path):
        if not os.path.isdir(path):
            os.mkdir(path, 0755)
            os.chown(path, siteowner.uid, siteowner.gid)
    for vhost in config.VHOSTS.keys():
        vhostdir = config.SITEROOT + "/" + vhost
        vhostlogdir = logroot + "/" + vhost
        if not os.path.isdir(vhostlogdir):
            os.mkdir(vhostlogdir, 0755)
            os.chown(vhostlogdir, siteuser.uid, siteuser.gid)
        if not os.path.isdir(vhostdir):
            if fqdn == vhost:
                os.symlink(config.SITEROOT + "/localhost", vhostdir)
            else:
                _mkdir(vhostdir)
            _mkdir(vhostdir + "/htdocs")
            _mkdir(vhostdir + "/htdocs-secure")
            _mkdir(vhostdir + "/media")
            _mkdir(vhostdir + "/media/js")
            _mkdir(vhostdir + "/media/css")
            _mkdir(vhostdir + "/media/images")


def start_proc_manager(config, logfile):
    from pycopia import proctools
    from pycopia import scheduler
    from pycopia import asyncio

    pm = proctools.get_procmanager()
    libexec = config.get("LIBEXEC", "/usr/libexec/pycopia")

    for name, serverlist in config.VHOSTS.items():
        for servername in serverlist:
            print "Starting %s for %s." % (servername, name)
            p = pm.spawnpipe("%s/fcgi_server -n %s" % (libexec, servername), persistent=True, logfile=logfile)
            asyncio.poller.register(p)
            #scheduler.sleep(1.0) # give it time to init...
    if config.USEFRONTEND:
        lighttpd = proctools.which("lighttpd")
        if asyncio.poller:
            pm.spawnpipe("%s -D -f %s" % (lighttpd, LTCONFIG), persistent=True, logfile=logfile)
        else: # no servers, just run frontend alone
            pm.spawnpipe("%s -f %s" % (lighttpd, LTCONFIG))
    try:
        asyncio.poller.loop()
        print "No servers, exited loop."
    except KeyboardInterrupt:
        pass
    if asyncio.poller:
        asyncio.poller.unregister_all()
        for proc in pm.getprocs():
            proc.killwait()
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
            print "Process manager running: pid %s: %s." % (pid, s.cmdline)
            return 0
    print "Process manager not running."
    return 1


def robots(config):
    user = passwd.getpwnam(config.SITEOWNER)
    for vhost, scripts in config.VHOSTS.items():
        rname = os.path.join(config.SITEROOT, vhost, "htdocs", "robots.txt")
        if os.path.exists(rname):
            continue
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
 -f  <cffile> Override config file to use.
 -D  <fqdn> Override FQDN config variable.

Where command is one of:
    setup   - create directory structures according to config file entries.
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
    dname = None
    servername = os.path.basename(argv[0])
    logfilename = "/var/log/%s.log" % (servername,)
    pidfilename = "/var/run/%s.pid" % (servername,)
    cffile = SITE_CONFIG
    try:
        optlist, args = getopt.getopt(argv[1:], "?hdnNl:p:f:D:")
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
        elif opt == "-D":
            dname = optarg
        elif opt == "-f":
            cffile = optarg
        elif opt == "-p":
            pidfilename = optarg
        elif opt == "-d":
            from pycopia import autodebug # Sets up auto debugging handler.

    glbl = {"FQDN": dname or socket.get_fqdn()}

    config = basicconfig.get_config(cffile, globalspace=glbl)

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
    elif cmd.startswith("set"):
        return setup(config)
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


