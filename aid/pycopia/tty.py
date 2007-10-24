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
Useful terminal/curses related objects. Use this instead of the stock 'tty'
module,  as this module subsumes that functionality.

"""

import sys, os
import stat
import signal
import fcntl
import struct
from termios import *
from errno import EINTR

from pycopia.aid import systemcall


class PageQuitError(Exception):
    pass

# Indexes for termios list.
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

IFLAGS = [ "IGNBRK", "BRKINT", "IGNPAR", "PARMRK", "INPCK", "ISTRIP", 
        "INLCR", "IGNCR", "ICRNL", "IXON", "IXANY", "IXOFF", "IMAXBEL", ]

OFLAGS = [ "OPOST", "ONLCR", "OCRNL", "ONOCR", "ONLRET"]

CFLAGS = ["CSTOPB", "CREAD", "PARENB", "CLOCAL", "CRTSCTS",]

LFLAGS = [ "ISIG", "ICANON", "XCASE", "ECHO", "ECHOE", "ECHOK", "ECHONL", 
        "ECHOCTL", "ECHOPRT", "ECHOKE", "FLUSHO", "NOFLSH", "TOSTOP", 
        "PENDIN", "IEXTEN",]

BAUDS = [ 'B0', 'B50', 'B75', 'B110', 'B134', 'B150', 'B200', 'B300', 
    'B600', 'B1200', 'B1800', 'B2400', 'B4800', 'B9600', 'B19200', 'B38400', 
    'B57600', 'B115200', 'B230400', 'B460800',]

CCHARS = [ "VINTR", "VQUIT", "VERASE", "VKILL", "VEOF", "VTIME",
        "VMIN", "VSWTC", "VSTART", "VSTOP", "VSUSP", "VEOL",
        "VREPRINT", "VDISCARD", "VWERASE", "VLNEXT", "VEOL2",]


def get_baud(cflags):
    mod = sys.modules[__name__]
    bv = cflags & CBAUD
    for bn in BAUDS:
        if getattr(mod, bn) == bv:
            return bn

def set_baud(fd, baud):
    mod = sys.modules[__name__]
    try:
        sym = getattr(mod, "B%s" % baud)
    except AttributeError:
        raise ValueError, "bad baud value"
    [iflags, oflags, cflags, lflags, ispeed, ospeed, cc] = tcgetattr(fd)
    ispeed = ospeed = sym
    tcsetattr(fd, TCSANOW, [iflags, oflags, cflags, lflags, ispeed, ospeed, cc])

def set_flag(fd, flag):
    mode = tcgetattr(fd)
    _set_flag(mode, flag)
    tcsetattr(fd, TCSANOW, mode)

def _set_flag(mode, flagname):
    mod = sys.modules[__name__]
    if flagname.startswith("-"):
        off = 1
        flagname = flagname[1:].upper()
    else:
        off = 0
        flagname = flagname.upper()
    try:
        flagval = getattr(mod, flagname)
    except AttributeError:
        raise ValueError, "no stty flag named %r" % (flagname,)
    if flagname in IFLAGS:
        if off:
            mode[IFLAG] &= ~flagval
        else:
            mode[IFLAG] |= flagval
    elif flagname in OFLAGS:
        if off:
            mode[OFLAG] &= ~flagval
        else:
            mode[OFLAG] |= flagval
    elif flagname in CFLAGS:
        if off:
            mode[CFLAG] &= ~flagval
        else:
            mode[CFLAG] |= flagval
    elif flagname in LFLAGS:
        if off:
            mode[LFLAG] &= ~flagval
        else:
            mode[LFLAG] |= flagval

def flag_string(fd):
    mod = sys.modules[__name__]
    [iflags, oflags, cflags, lflags, ispeed, ospeed, cc] = tcgetattr(fd)
    chars = [] ; ires = [] ; ores = [] ; cres = [] ; lres = []
    for cname in CCHARS:
        chars.append("%s=%r" % (cname[1:].lower(), cc[getattr(mod, cname)]))
    for flag in IFLAGS:
        if iflags & getattr(mod, flag):
            ires.append(flag.lower())
        else:
            ires.append("-%s" % (flag.lower(),))
    for flag in OFLAGS:
        if oflags & getattr(mod, flag):
            ores.append(flag.lower())
        else:
            ores.append("-%s" % (flag.lower(),))
    for flag in CFLAGS:
        if cflags & getattr(mod, flag):
            cres.append(flag.lower())
        else:
            cres.append("-%s" % (flag.lower(),))
    for flag in LFLAGS:
        if lflags & getattr(mod, flag):
            lres.append(flag.lower())
        else:
            lres.append("-%s" % (flag.lower(),))
    s = ["baud: %s" % (get_baud(cflags),)]
    #s.append("ispeed: %d, ospeed: %d" % (ispeed, ospeed))
    s.append("CCHARS: %s" % (", ".join(chars)))
    s.append("IFLAGS: %s" % (", ".join(ires)))
    s.append("OFLAGS: %s" % (", ".join(ores)))
    s.append("CFLAGS: %s" % (", ".join(cres)))
    s.append("LFLAGS: %s" % (", ".join(lres)))
    return "\n".join(s)

def stty(fd, *args):
    """stty(fd, [flags...]) 
Stty gets or sets the termios flags for the specified file descriptor. If
no argument is given a report is returned as a string.  If a flag string
is given in the form "flag" or "-flag" then the flag is set, or reset,
respectively. Multiple flags of this form may be supplied.
    """
    if not args: # return a report string
        return flag_string(fd)
    else:
        mode = tcgetattr(fd)
        for arg in args: # should be set of strings, possibly with leading "-"
            cmd = {"sane":sane, "reset":sane, "cbreak":setcbreak, 
                    "raw":setraw, "cooked":cooked }.get(arg, None)
            if cmd is None:
                _set_flag(mode, arg)
            else:
                cmd(fd)
                break
        else:
            tcsetattr(fd, TCSANOW, mode)

def setraw(fd, when=TCSAFLUSH):
    """Put tty into a raw mode."""
    mode = tcgetattr(fd)
    old = mode[:]
    mode[IFLAG] &= ~(BRKINT | ICRNL | INLCR | INPCK | ISTRIP | IXON | IXOFF)
    mode[IFLAG] |= (IGNPAR | IGNBRK)
    mode[OFLAG] &= ~(OPOST)
    mode[OFLAG] |= (ONLCR)
    mode[CFLAG] &= ~(PARENB)
    mode[CFLAG] |= CS8
    mode[LFLAG] &= ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[LFLAG] |= (ECHOCTL)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    return old

def set_8N1(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    old = mode[:]
    mode[IFLAG] &= ~(INPCK | ISTRIP)
    mode[IFLAG] |= (IGNPAR)
    mode[CFLAG] &= ~(PARENB | CSTOPB)
    mode[CFLAG] |= CS8
    tcsetattr(fd, when, mode)
    return old

def set_7E1(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    old = mode[:]
    mode[IFLAG] &= ~(IGNPAR | ISTRIP)
    mode[IFLAG] |= (INPCK)
    mode[CFLAG] &= ~(CSTOPB | PARODD)
    mode[CFLAG] |= (CS7 | PARENB)
    tcsetattr(fd, when, mode)
    return old

def setcbreak(fd, when=TCSAFLUSH):
    """Put tty into a cbreak mode."""
    mode = tcgetattr(fd)
    old = mode[:]
    mode[LFLAG] &= ~(ECHO | ICANON)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    return old

def noecho(fd, when=TCSANOW):
    """turn off echo (for slave pty's)"""
    mode = tcgetattr(fd)
    old = mode[:]
    mode[LFLAG] &= ~(ECHO | ECHOE | ECHOCTL | ECHOK | ECHONL)
    mode[OFLAG] &= ~(OPOST | ONLCR)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    return old

def cooked(fd, when=TCSANOW):
    mode = tcgetattr(fd)
    old = mode[:]
    # brkint ignpar istrip icrnl ixon opost isig icanon,
    #eof and eol characters to their default values
    mode[IFLAG] &= ~(INPCK )
    mode[IFLAG] |= (ICRNL | BRKINT | IGNPAR | ISTRIP | IXON )
    mode[OFLAG] &= ~( OCRNL | ONLRET | ONOCR )
    mode[OFLAG] |= (OPOST | ONLCR)
    mode[LFLAG] &= ~(ECHO | ECHONL | ECHOPRT)
    mode[LFLAG] |= (ICANON | ISIG | ECHOCTL | ECHOE | ECHOK | ECHOKE)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    return old

def sane(fd, when=TCSANOW):
    mode = tcgetattr(fd)
    old = mode[:]
    mode[CFLAG] &= ~(CSIZE | PARENB | CRTSCTS | CLOCAL | CSTOPB | HUPCL)
    mode[CFLAG] |= (CS8)
    mode[IFLAG] &= ~(INPCK | PARMRK | IGNBRK | ISTRIP | INLCR | IGNCR | IXOFF | IUCLC | IXANY )
    mode[IFLAG] |= (ICRNL | BRKINT | IGNPAR | IXON )
    mode[OFLAG] &= ~(OLCUC | OCRNL | ONLRET | ONOCR | OFILL | OFDEL )
    mode[OFLAG] |= (OPOST | ONLCR | NL0 | CR0 | TAB0 | BS0 | VT0 | FF0)
    mode[LFLAG] &= ~(ECHONL | ECHOPRT | NOFLSH | XCASE | TOSTOP)
    mode[LFLAG] |= (ICANON | ISIG | IEXTEN | ECHO | ECHOCTL | ECHOE | ECHOK | ECHOKE)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    return old

# XXX
def slavepty(fd, when=TCSANOW):
    """set a pty as ssh does."""
    mode  = tcgetattr(0) # copy and modify our stdin terminal
#    mode[IFLAG] &= ~(ICRNL | INPCK | ISTRIP | IXON)
    mode[IFLAG] |= (BRKINT | IXANY | IMAXBEL)
#    mode[OFLAG] &= ~( OCRNL | ONLRET | ONOCR )
#    mode[OFLAG] |= (OPOST | ONLCR)
#    mode[CFLAG] &= ~(CSIZE | PARENB | CRTSCTS | CLOCAL | CSTOPB)
#    mode[CFLAG] |= (CS8 | HUPCL)
#    mode[LFLAG] &= ~(ECHO | ECHONL | ECHOPRT | ICANON)
    mode[LFLAG] |= (IEXTEN | ISIG | ECHOCTL | ECHOE | ECHOK | ECHOKE)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def masterpty(fd, when=TCSANOW):
    mode  = tcgetattr(0) # copy and modify our stdin terminal
    mode[IFLAG] &= ~(ICRNL | INPCK | ISTRIP)
    mode[IFLAG] |= (BRKINT | IXANY | IMAXBEL | IXON)
    mode[OFLAG] &= ~( OCRNL |  ONLRET | ONOCR )
    mode[OFLAG] |= (OPOST | ONLCR)
    mode[CFLAG] &= ~(CSIZE | PARENB | CRTSCTS | CLOCAL | CSTOPB)
    mode[CFLAG] |= (CS8 | HUPCL)
    mode[LFLAG] &= ~(ECHO | ECHONL | ECHOPRT | ICANON | ISIG | NOFLSH | FLUSHO)
    mode[LFLAG] |= (IEXTEN | ECHOCTL | ECHOE | ECHOK | ECHOKE)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)
    x, y, xpix, ypix = get_winsize(0)
    set_winsize(fd, x, y, xpix, ypix)


#struct winsize {
#   unsigned short ws_row;
#   unsigned short ws_col;
#   unsigned short ws_xpixel;
#   unsigned short ws_ypixel;
#};
_WINSIZEFMT = "HHHH"

def get_winsize(fd):
    """get_winsize(fd)
Return a tuple of (row, col, xpixel, ypixel) when the file descriptor (or file
object) is a terminal.  """
    winsize = fcntl.ioctl(fd, TIOCGWINSZ, "\0"*struct.calcsize(_WINSIZEFMT))
    # row, col, xpix, ypix
    return struct.unpack(_WINSIZEFMT, winsize)

def set_winsize(fd, row, col, xpix=0, ypix=0):
    winsize = struct.pack(_WINSIZEFMT, row, col, xpix, ypix)
    fcntl.ioctl(fd, TIOCSWINSZ, winsize)

def get_intr_char(fd=0):
    mode = tcgetattr(fd)
    return mode[CC][VINTR]

def interrupt(fd, intr=None):
    if intr is None:
        mode = tcgetattr(fd)
        intr = mode[CC][VINTR]
    tcflush(fd, TCOFLUSH)
    os.write(fd, intr)

class PagedIO(object):
    """PagedIO([pagerprompt])
Reads and writes to stdin/stdout while paging output. 
automatically adjusts output according to screen size.  """
    def __init__(self, pagerprompt=None):
        self.stdout = sys.stdout 
        self.stdin = sys.stdin
        self.stderr = sys.stderr
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        self._writtenlines = 0
        self.set_pagerprompt(pagerprompt)
        # reading methods
        self.readlines = self.stdin.readlines
        self.xreadlines = self.stdin.xreadlines
        # writing methods
        self.flush = self.stdout.flush
        self.writelines = self.stdout.writelines
        if self.stdout.isatty(): # page only if output is a tty
            self.set_size()
            self._oldhandler = signal.getsignal(signal.SIGWINCH)
            signal.signal(signal.SIGWINCH, self._winch_handler)
            self.readline = self._readline
            self.write = self.page_write
            self.read = self.page_read
        else:
            self.readline = self.stdin.readline
            self.write = self.stdout.write
            self.read = self.stdin.read

    def set_pagerprompt(self, pagerprompt):
        self.pagerprompt = pagerprompt or "-- more (press any key to continue) --"
        lpp = len(self.pagerprompt)
        self.prompterase = "\b"*lpp+" "*lpp+"\b"*lpp

    def close(self):
        self.unregister()
        self.stdout = None
        self.stdin = None
        self.closed = 1
        del self.readline, self.readlines, self.xreadlines
        del self.flush, self.writelines, self.write

    # can't use __del__ because the signal module holds a reference to this
    # object, via the handler method. It cannot be garbage collected until
    # unregistered.
    def unregister(self):
        signal.signal(signal.SIGWINCH, self._oldhandler)

    def page_read(self, amt=-1):
        self._writtenlines = 0
        return self.stdin.read(amt)

    def _readline(self, hint=-1):
        self._writtenlines = 0
        return self.raw_input()+"\n"

    def fileno(self): # ??? punt, since mostly used by readers
        return self.stdin.fileno()

    def isatty(self):
        return self.stdin.isatty() and self.stdout.isatty()

    def set_size(self):
        self.rows, self.cols, self.xpixel, self.ypixel = get_winsize(self.stdout.fileno())

    def _winch_handler(self, sig, st):
        self.set_size()

    def errlog(self, text):
        self.stderr.write("%s\n" % (text,))
        self.stderr.flush()

    def page_write(self, data):
        ld = len(data)
        rows = self.rows-1
        needed = rows - self._writtenlines
        i = 0
        while i < ld:
            b = i
            i, lines = self._get_index(data, needed, i)
            self.stdout.write(data[b:i])
            self._writtenlines += lines
            if self._writtenlines >= rows:
                c = self._pause()
                if c in "qQ":
                    raise PageQuitError
                elif c == "\r": # XXX still needs work 
                    rows = needed = 1
                else:
                    rows = needed = self.rows-1

    # get the index into the data string that will give you the needed number
    # of lines, also taking into account implicit wrapping.
    def _get_index(self, data, needed, i):
        cols = self.cols
        l = n = 0 
        ld = len(data)
        while 1:
            n = data.find("\n", i)
            n = ((n<0 and ld) or n) + 1
            l += 1 + ((n-i)/cols)
            if l == needed or n >= ld:
                return n, l
            i = n

    def _pause(self):
        c = ""
        self._writtenlines = 0
        savestate = tcgetattr(self.stdin)
        self.stdout.write(self.pagerprompt)
        self.stdout.flush()
        try:
            setraw(self.stdin)
            while 1:
                try:
                    c = self.stdin.read(1)
                    break
                except EnvironmentError, why:
                    if why.errno == EINTR:
                        continue
                    else:
                        raise
        finally:
            tcsetattr(self.stdin, TCSAFLUSH, savestate)
        self.stdout.write(self.prompterase)
        return c

    # user input
    def raw_input(self, prompt=""):
        self._writtenlines = 0
        return raw_input(prompt)
    user_input = raw_input


def get_key(prompt=""):
    c = ""
    so = sys.stdout
    si = sys.stdin
    clear = "\b"*len(prompt)+" "*len(prompt)+"\b"*len(prompt)
    savestate = tcgetattr(si)
    try:
        so.write(prompt)
        so.flush()
        setraw(si)
        while 1:
            try:
                c = si.read(1)
                break
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
    finally:
        tcsetattr(si, TCSAFLUSH, savestate)
    so.write(clear)
    return c

def getpass(prompt="Password: "):
    so = sys.stdout
    si = sys.stdin
    savestate = noecho(si)
    try:
        if prompt:
            so.write(prompt)
        so.flush()
        while True:
            try:
                c = si.readline()
                break
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
    finally:
        tcsetattr(si, TCSAFLUSH, savestate)
    so.write('\n')
    if c.endswith("\n"):
        return c[:-1]
    return c

def getuser():
    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            return user
    import pwd
    return pwd.getpwuid(os.getuid())[0]


def terminal_lines(data, cols=80):
    """Returns the number of lines of a terminal with 'cols' columns that the
string will consume."""
    l = n = i = 0 
    while n >= 0:
        n = data.find("\n", i)
        l += 1 + ((((n<0 and len(data)) or n)-i)/cols)
        i = n + 1
    return l


# stores any tty states for cleanup up at Python exit
_TTYSTATES = {}

def _cleanup():
    global _TTYSTATES
    for fd, state in _TTYSTATES.items():
        tcsetattr(fd, TCSANOW, state)


def save_state(fd):
    global _TTYSTATES
    if not _TTYSTATES:
        import atexit
        atexit.register(_cleanup)
    savestate = tcgetattr(fd)
    _TTYSTATES[fd] = savestate



class SerialPort(object):
    def __init__(self, fname, setup="9600 8N1"):
        st = os.stat(fname).st_mode
        if not stat.S_ISCHR(stat.S_IFMT(st)):
            raise ValueError, "%s is not a character device." % fname
        fd = os.open(fname, os.O_RDWR)
        tcflush(fd, TCIOFLUSH)
        setraw(fd)
        fo = os.fdopen(fd, "w+", 0)
        self._fo = fo
        self.name = fname
        self.closed = False
        self.set_serial(setup)

    def fileno(self):
        return self._fo.fileno()

    def sendbreak(self, duration=0):
        tcsendbreak(self._fo.fileno(), duration)

    def set_baud(self, baud):
        set_baud(self._fo.fileno(), baud)

    def set_serial(self, spec):
        """Quick and easy way to setup the serial port.
        Supply a string such as "9600 8N1".
        """
        fd = self._fo.fileno()
        baud, mode = spec.split() 
        set_baud(fd, baud)
        if mode == "8N1":
            return set_8N1(fd)
        elif mode == "7E1":
            return set_7E1(fd)
        else:
            raise ValueError, "set_serial: bad serial string."

    def get_inqueue(self):
        v = fcntl.ioctl(self._fo.fileno(), TIOCINQ, '\x00\x00\x00\x00')
        return struct.unpack("i", v)[0]

    def __str__(self):
        if not self.closed:
            fl = flag_string(self._fo.fileno())
            return "%s:\n%s" % (self.name, fl)
        else:
            return "SerialPort %r is closed." % self.name

    def stty(self, *args):
        return stty(self._fo.fileno(), *args)

    @systemcall
    def read(self, amt=4096):
        amt = min(amt, self.get_inqueue())
        return self._fo.read(amt)

    @systemcall
    def write(self, data):
        return self._fo.write(data)

    @systemcall
    def readline(self, hint=-1):
        return self._fo.readline(hint)

    @systemcall
    def close(self):
        fo = self._fo
        self._fo = None
        self.closed = True
        return fo.close()

