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
slogsink is a module (that is used in conjuctions with the slogsink C
program) that receives syslog messages over a network. This is not a full
syslog implementation, but a simple syslog protocol receiver that listens
on the standard syslog/udp port for incoming messages and forwards them
to your callback function. 

The slogsink C program is used because the syslog port is a privileged
port, and requires root access to open. The slogsink program should have
been install SUID to root. 

"""


import os, sys, struct
import re
from errno import EAGAIN

from pycopia import socket
from pycopia import asyncio
from pycopia import UI
from pycopia import CLI
from pycopia import timelib
from pycopia.ipv4 import IPv4

now = timelib.now


FACILITY = {
    0: "kern",
    1: "user",
    2: "mail",
    3: "daemon",
    4: "auth",
    5: "syslog",
    6: "lpr",
    7: "news",
    8: "uucp",
    9: "cron",
    10: "authpriv",
    11: "ftp",
    16: "local0",
    17: "local1",
    18: "local2",
    19: "local3",
    20: "local4",
    21: "local5",
    22: "local6",
    23: "local7",
}
PRIORITY = {
    0: "emerg",
    1: "alert",
    2: "crit",
    3: "err",
    4: "warning",
    5: "notice",
    6: "info", 
    7: "debug",
}

_default_addr=("", 514)
_user_default_addr = ("", 10514)


class SyslogMessage(object):
    def __init__(self, msg, fac, pri, host=None, timestamp=None, tag=""):
        self.message = msg
        self.facility = int(fac)
        self.priority = int(pri)
        self.host = host
        self.timestamp = timestamp
        self.tag = tag
    
    def __str__(self):
        return "%.2f|%s|%s: %s" % (self.timestamp, self.host, self.tag, self.message)
    
    def encode(self):
        ts = timelib.strftime("%b %d %H:%M:%S", timelib.localtime(self.timestamp))
        return "<%s>%s %s %s: %s" % ((self.facility<<3) + self.priority, ts, self.tag, self.message)
    
    def __repr__(self):
        return "%s(%r, %r, %r, %r, %r)" % (self.__class__.__name__, self.message, self.facility, self.priority, 
                self.host, self.timestamp)
    


_MSG_RE = re.compile("<(\d+?)>(.*)")
def parse_message(timestamp, srcip, rawmsg):
    mo = _MSG_RE.search(rawmsg)
    code = int(mo.group(1))
    fac, pri = code>>3, code & 0x07
    msg = mo.group(2)
    return SyslogMessage(msg, fac, pri, srcip, timestamp)


class SlogDispatcher(socket.AsyncSocket):
    def __init__(self, callback, addr=_default_addr):
        super(SlogDispatcher, self).__init__(socket.AF_UNIX, socket.SOCK_STREAM)
        loc, port = addr
        self.callback = callback # should be a callable object
        self.connect("/tmp/.slog-%d" % (port,))

    def writable(self):
        return False

    def readable(self):
        return True

    def handle_error(self, ex, val, tb):
        print >> sys.stderr, "*** Dispatcher:", ex, val

    def handle_read(self):
        ip = struct.unpack("!i", self.recv(4))[0] # network byte-order
        port = struct.unpack("!h", self.recv(2))[0] # network byte-order
        length = struct.unpack("i", self.recv(4))[0] # host byte-order
        msg = self.recv(length)
        assert length == len(msg)
        return self.callback(parse_message(now(), IPv4(ip), msg))

class UserSlogDispatcher(socket.AsyncSocket):
    def __init__(self, callback, addr=_user_default_addr):
        super(UserSlogDispatcher, self).__init__(socket.AF_INET, socket.SOCK_DGRAM)
        self.callback = callback # should be a callable object
        self.bind(addr)

    def writable(self):
        return False

    def readable(self):
        return True

    def handle_error(self, ex, val, tb):
        print "*** Dispatcher:", ex, val

    def handle_read(self):
        try:
            while 1:
                msg, addr = self.recvfrom(4096, socket.MSG_DONTWAIT)
                self.callback(parse_message(now(), IPv4(addr[0]), msg))
        except SocketError, err:
            if err[0] == EAGAIN:
                return
            else:
                raise


class Syslog(object):
    """A syslog program object."""
    def __init__(self, files=None):
        self._FLIST = []
        if files:
            assert type(files) is list
            self.openlogs(files)

    logfiles = property(lambda s: s._FLIST[:])

    def addlog(self, fp):
        self._FLIST.append(fp)

    def openlog(self, fname):
        from pycopia import logfile
        try:
            fp = logfile.open(fname, "w")
        except: # non fatal
            ex, val, tb = sys.exc_info()
            print >>sys.stderr, "Warning: could not open %r for writing: %s (%s)." % (fname, ex, val)
        else:
            self._FLIST.append(fp)
    
    def openlogs(self, flist):
        for fn in flist:
            self.openlog(fn)

    def message(self, tag, msg, facility=5, priority=6):
        self.dispatch(SyslogMessage(msg, facility, priority, timestamp=now(), tag=tag))

    def write(self, msg):
        for fp in self._FLIST:
            fp.write(msg)

    def close(self):
        while self._FLIST:
            fn = self._FLIST.pop()
            if not fn.name.startswith("<"):
                fn.close()

    def flush(self):
        asyncio.poller.poll(0)
        for fp in self._FLIST:
            fp.flush()

    def dispatch(self, msg):
        for fp in self._FLIST:
            fp.write(str(msg)) # XXX
            fp.write("\n")


class SyslogApp(object):
    def __init__(self, syslog, ps1="%Isyslog%N> "):
        self.syslog = syslog
        theme = UI.DefaultTheme(ps1)
        self.parser = CLI.get_cli(SyslogCLI, paged=False, theme=theme, aliases=_CMDALIASES)
        self.parser.command_setup(syslog, ps1)

    def mainloop(self, debug=False):
        try:
            self.parser.interact()
        except KeyboardInterrupt:
            self.syslog.message("EXITING", "User interrupt")
            return
        except:
            exc, val, tb = sys.exc_info()
            self.syslog.message("EXCEPTION", "internal error: %s(%s)" % (exc, val))
            if debug:
                from pycopia import debugger
                debugger.post_mortem(tb)
        else:
            self.syslog.message("EXITING", "User exited")



class SyslogCLI(CLI.BaseCommands):
    def message(self, argv):
        """message <text>
    Place a manual entry in the log file."""
        self._obj.message("USER", " ".join(argv[1:]))

    def flush(self, argv):
        """flush
    Flush all of the log files."""
        self._obj.flush()
    
    def ctime(self, argv):
        """ctime <timeval>
    Expand <timeval> (a float) to a readable form."""
        t = float(argv[1])
        self._print(timelib.ctime(t))

_CMDALIASES = {"log":["message"]}


    
# the daemonize and slogsink program source code is in the
# $PYNMS_HOME/src/utils directory. This is a shim that runs as root and
# forwards UDP syslog port to a UNIX socket.
def start_slogsink(port=514):
    from pycopia import scheduler
    if port != 514:
        cmd = "daemonize slogsink %d" % port
    else:
        cmd = "daemonize slogsink"
    rv =  os.system(cmd)
    scheduler.sleep(2)
    return rv


def default_logger(message):
    sys.stdout.write("%s\n" % (message,))
    sys.stdout.flush()

def get_dispatcher(addr, callback=default_logger):
    port = addr[1]
    if port <= 1024 and os.getuid() > 0:
        start_slogsink(port)
        slogsink = SlogDispatcher(callback, addr)
    else:
        slogsink = UserSlogDispatcher(callback, addr)
    asyncio.register(slogsink)
    return slogsink

# simple syslog server
def slog(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 514
    get_dispatcher(("", port))
    try:
        while 1:
            asyncio.pause()
    except KeyboardInterrupt:
        return

# full syslog server with command interface
def nmslog(argv):
    """
Usage:
    nmslog [-p port] [-d] [<logfile> ...]

Record external syslog events. An optional list of file names may be
supplied on the command line. The received event will be written to each
file given, including stdout. The user may also type in a message at
anytime which will also be added to the log files.

The -d flag enables debugging mode. The -p flag specifies a non-standard UDP
port to listen to.

    """
    import getopt
    port = 514
    debug = False
    try:
        opts, args = getopt.getopt(argv[1:], "p:dh?")
    except getopt.GetoptError:
        print __doc__
        return
    for opt, arg in opts:
        if opt == "-p":
            port = int(arg)
        if opt == "-d":
            debug = True
        elif opt in ("-?", "-h"):
            print __doc__
            return

    sl = Syslog(args)
    get_dispatcher(("", port), sl.dispatch)
    sl.addlog(sys.stdout)
    print "Logging started. Listening on UDP port %d. You may type manual entries at will." % (port,)
    sl.message("STARTING", ", ".join(map(lambda o: o.name, sl.logfiles)))

    sa = SyslogApp(sl)
    sa.mainloop(debug)
    sl.close()


if __name__ == "__main__":
    msg = parse_message(now(), "localhost", '<177>local6 alert')
    print msg
    dis = get_dispatcher(_user_default_addr)

