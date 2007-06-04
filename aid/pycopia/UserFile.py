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
Defines the UserFile file object. This enhances the standard file object with
easier file locking. It also handles interrupted system calls when reading.  

This module also provides a TextFile object that can read and write text files
for the different platforms that have different line ending styles.

"""

import sys, os
import fcntl, stat
from errno import EINTR


class UserFile(file):
    def read(self, amt=-1):
        while 1:
            try:
                next = super(UserFile, self).read(amt)
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return next

    def readline(self, amt=-1):
        while 1:
            try:
                next = super(UserFile, self).readline(amt)
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return next

    def ttyname(self):
        return os.ttyname(self.fileno())

    def tcgetpgrp(self):
        return os.tcgetpgrp(self.fileno())

    def stat(self):
        return os.fstat(self.fileno())
    fstat = stat # alias

    def get_flags(self):
        return fcntl.fcntl(self.fileno(), fcntl.F_GETFL)
    flags = property(get_flags)

    filemode = property(lambda self: stat.S_IMODE(self.stat().st_mode))
    inode = property(lambda s: s.stat().st_ino)
    device = property(lambda s: s.stat().st_dev)
    links = property(lambda s: s.stat().st_nlink)
    uid = property(lambda s: s.stat().st_uid)
    gid = property(lambda s: s.stat().st_gid)
    size = property(lambda s: s.stat().st_size)
    blocks = property(lambda s: s.stat().st_blocks)
    devicetype = property(lambda s: s.stat().st_rdev)
    atime = property(lambda s: s.stat().st_atime)
    mtime = property(lambda s: s.stat().st_mtime)
    ctime = property(lambda s: s.stat().st_ctime)
    # checkers
    isdir = property(lambda self: stat.S_ISDIR(stat.S_IFMT(self.stat().st_mode)))
    ischar = property(lambda self: stat.S_ISCHR(stat.S_IFMT(self.stat().st_mode)))
    isblock = property(lambda self: stat.S_ISBLK(stat.S_IFMT(self.stat().st_mode)))
    isfile = property(lambda self: stat.S_ISREG(stat.S_IFMT(self.stat().st_mode)))
    isfifo = property(lambda self: stat.S_ISFIFO(stat.S_IFMT(self.stat().st_mode)))
    islink = property(lambda self: stat.S_ISLNK(stat.S_IFMT(self.stat().st_mode)))
    issock = property(lambda self: stat.S_ISSOCK(stat.S_IFMT(self.stat().st_mode)))

    # these return a base file object... cant "cast" to a subclass
    def dup(self):
        return os.fdopen(os.dup(self.fileno()), self.mode)

    def dup2(self, fd):
        os.dup2(self.fileno(), fd)
        return os.fdopen(fd, self.mode)

    def _lock(self, flag, length, start, whence):
        fcntl.lockf(self.fileno(), flag, length, start, whence)

    def lock_shared(self, length=0, start=0, whence=0, nb=0):
        if nb:
            flag = fcntl.LOCK_SH | fcntl.LOCK_NB
        else:
            flag = fcntl.LOCK_SH
        self._lock(flag, length, start, whence)

    def lock_exclusive(self, length=0, start=0, whence=0, nb=0):
        if nb:
            flag = fcntl.LOCK_EX | fcntl.LOCK_NB
        else:
            flag = fcntl.LOCK_EX
        self._lock(flag, length, start, whence)
    lock = lock_exclusive # alias

    def unlock(self, length=0, start=0, whence=0):
        self._lock(fcntl.LOCK_UN, length, start, whence)


class TextFile(UserFile):
    """TextFile(self, name, mode="r", bufsize=-1, linesep=None)
A file object that handles different line separator conventions. This file
object's readline() method returns the line with trailing line separator
stripped, and raises EOFError on end of file. The writelines() method will
append an appropriate line separator when writing. Thus, this file object
allows reading and writeing non-native text files.
    """
    def __init__(self, name, mode="r", bufsize=-1, linesep=None):
        super(TextFile, self).__init__(name, mode, bufsize)
        self.linesep = linesep or os.linesep # default to native

    # note this changes the semantics of the standard readline method. This
    # one strips line separators and raises EOFError on end of file.
    def readline(self, hint=-1):
        line = super(TextFile, self).readline(hint)
        if not line:
            raise EOFError
        return line.rstrip("\r\n")

    def readlines(self):
        rv = []
        while 1:
            try:
                l = self.readline()
            except EOFError:
                break
            rv.append(l)
        return rv

    def writeline(self, line):
        self.write(line)
        self.write(self.linesep)
    writeln = writeline # alias

    # note this changes the semantics of the standard writelines method. This
    # one adds line separators.
    def writelines(self, llist):
        map(self.writeline, llist)


############################################################################
#### safe file object wrapper. Protected against interrupted system calls.

class FileWrapper(object):
    """FileWrapper(fileobject, [logfile])
Wraps a file-like object with safe read methods, and allows logged reads."""
    def __init__(self, fo, linesep=None, logfile=None, restart=True):
        self._fo = fo
        self.linesep = linesep or os.linesep
        self._logfile = logfile
        self.mode = fo.mode
        self.closed = 0
        self.softspace = 0
        self._restart = restart

    # delegate other methods, note that they are not protected from EINTR...
    def __getattr__(self, name):
        return getattr(self._fo, name)

    def close(self):
        sts = self._fo.close()
        self._fo = None
        self._logfile = None
        self.closed = 1
        return sts # for popen

    def read(self, amt=-1):
        while 1:
            try:
                text = self._fo.read(amt)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        if self._logfile:
            self._logfile.write(text)
        return text

    def readline(self, amt=-1):
        while 1:
            try:
                line = self._fo.readline(amt)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        if self._logfile:
            self._logfile.write(line)
        return line

    def readlines(self):
        rv = []
        while 1:
            line = self.readline()
            if not line:
                return rv
            else:
                rv.append(line)

    def raw_input(self, prompt=""):
        if prompt:
            self.write(prompt)
        return "%s\n" % (self.read(4096),)

    def write(self, text):
        while 1:
            try:
                writ = self._fo.write(text)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return writ

    def writeline(self, text):
        self.write(text)
        self.write(self.linesep)

    def writelines(self, lines):
        map(self.write, lines)

    def restart(self, flag=True):
        self._restart = bool(flag)



class MergedIO(object):
    """MergedIO(outfile, infile)
Combines a write stream and a read stream into one read/write object."""
    def __init__(self, outf, inf):
        self._outf = outf
        self._inf = inf
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        # reading methods
        self.read = inf.read
        self.readline = inf.readline
        self.readlines = inf.readlines
        self.xreadlines = inf.xreadlines
        # writing methods
        self.write = outf.write
        self.flush = outf.flush
        self.writelines = outf.writelines

    def close(self):
        self._outf.close()
        self._inf.close()
        self._outf = None
        self._inf = None
        self.closed = 1

    def fileno(self): # ??? punt, since reads are most common, return reader fd
        return self._inf.fileno()

    def filenos(self):
        return self._inf.fileno(), self._outf.fileno()

    def isatty(self):
        return self._inf.isatty() and self._outf.isatty()

# XXX
class PipeIO(MergedIO):
    """PipeIO(pipefileobject)
Reads from and manages the reading from a named pipe. Useful for daemon processes.
"""
    def __init__(self, pipe):
        import signal
        self._fo = pipe
        self._out = None
        self.oname = self._fo.name + ".out" # XXX
        signal.signal(signal.SIGPIPE, self._noclient)

    def _noclient(self, sig, st):
        self._fo = None
        if self._out:
            self._out.close()
            self._out = None

    def _reconnect(self):
        outpipe = os.open(self.oname, os.O_WRONLY|os.O_NONBLOCK)
        self._out = os.fdopen(outpipe, "w", 0)

    def handle_read_event(self):
        line = self._fo.readline()
        if self._out is None:
            self._reconnect()


# in case you want to write to a file-like object that is not a TextFile
# object...
class FileConverter(object):
    """Converts text files to and from various platform line ending
conventions."""
    def __init__(self, linesep=None):
        self.linesep = linesep or os.linesep

    def convert(self, srcname, dstname):
        src = TextFile(srcname)
        dst = TextFile(dstname, mode, bufsize, self.linesep)
        copylines(src, dst)

    def convertfileobject(self, src, dst):
        while 1:
            line = src.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            dst.write(line)
            dst.write(self.linesep)

### utility functions
def get_mac_converter():
    return FileConverter("\r")

def get_dos_converter():
    return FileConverter("\r\n")

def get_unix_converter():
    return FileConverter("\n")

def open(name, mode="r", bufsize=-1):
    return UserFile(name, mode, bufsize)

def open_macfile(name, mode="r", bufsize=-1):
    """returns a TextFile with Macintosh style line endings."""
    return TextFile(name, mode, bufsize, "\r")

def open_dosfile(name, mode="r", bufsize=-1):
    """returns a TextFile with DOS style line endings."""
    return TextFile(name, mode, bufsize, "\r\n")

def open_unixfile(name, mode="r", bufsize=-1):
    """returns a TextFile with Unix style line endings."""
    return TextFile(name, mode, bufsize, "\n")

def open_textfile(name, mode="r", bufsize=-1, linesep="unix"):
    """Open a text file of a particular platform flavor. Text lines written to
this file with the writeline(s) method will have the appropriate line
endings.  """
    # may specify line separator by platform name as well.
    linesep = {"unix":"\n", "dos":"\r\n", 
                "mac":"\r", "ietf":"\r\n"}.get(linesep, linesep)
    return TextFile(name, mode, bufsize, linesep)

def copyfileobj(fsrc, fdst, bufsize=16384):
    """copyfileobj(src, dst, [bufsize])
copy data from file-like object fsrc to file-like object fdst"""
    while 1:
        buf = fsrc.read(bufsize)
        if not buf:
            break
        fdst.write(buf)

def copylines(src, dst):
    """copylines(src, dst)
Copy text lines from file-like object src to TextFile object dst. End-of-line
conversion is performed (via the TextFile object)."""
    while 1:
        try:
            line = src.readline()
        except EOFError:
            break
        dst.writeline(line)

def writelines(filename, lines, texttype="unix"):
    """writelines(filename, lines, texttype="unix")
Make a file of a particular text type, given a list of lines (without line
endings), and a file name.  """
    fo = open_textfile(filename, "w", linesep=texttype)
    fo.writelines(list(lines))
    fo.close()

def unix2dos(srcname, dstname):
    """Copies a file in unix text format to DOS text format."""
    src = open_unixfile(srcname)
    dst = open_dosfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def unix2mac(srcname, dstname):
    """Copies a file in unix text format to Macintosh text format."""
    src = open_unixfile(srcname)
    dst = open_macfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def dos2unix(srcname, dstname):
    """Copies a file in DOS text format to Unix text format."""
    src = open_dosfile(srcname)
    dst = open_unixfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def mac2unix(srcname, dstname):
    """Copies a file in Macintosh text format to Unix text format."""
    src = open_macfile(srcname)
    dst = open_unixfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def dos2mac(srcname, dstname):
    """Copies a file in DOS text format to Macintosh text format."""
    src = open_dosfile(srcname)
    dst = open_macfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def mac2dos(srcname, dstname):
    """Copies a file in Macintosh text format to DOS text format."""
    src = open_macfile(srcname)
    dst = open_dosfile(dstname, "w")
    try:
        copylines(src, dst)
    finally:
        src.close()
        dst.close()

def mode2flags(mode):
    """mode2flags(modestring)
    Converts a file mode in string form (e.g. "w+") to an integer flag value
    suitable for os.open().  """
    flags = os.O_LARGEFILE # XXX only when Python compiled with large file support
    if mode == "a":
        flags = flags | os.O_APPEND | os.O_WRONLY
    elif mode == "a+":
        flags = flags | os.O_APPEND | os.O_RDWR | os.O_CREAT
    elif mode == "w":
        flags = flags | os.O_WRONLY | os.O_CREAT
    elif mode == "w+":
        flags = flags | os.O_RDWR | os.O_CREAT
    elif mode == "r":
        pass # O_RDONLY is zero already
    elif mode == "r+":
        flags = flags | os.O_RDWR
    return flags


