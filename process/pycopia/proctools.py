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
Classes and functions for controlling, reading, and writing to co-processes. 

"""

import sys, os
from signal import signal, pause 
from signal import SIGCHLD, SIGTERM, SIGSTOP, SIGCONT, SIGHUP, SIG_DFL, SIGINT
from errno import EINTR, EBADF, ECHILD, EAGAIN, EIO

from pycopia import asyncio
from pycopia import shparser
from pycopia.OS.procfs import ProcStat
from pycopia import scheduler

from pycopia.aid import Enum

# Exec flags
IPIPE = Enum(1, "IPIPE")
OPIPE = Enum(2, "OPIPE")

class ProcessError(Exception):
    pass

class NotFoundError(ValueError):
    """Raised when the `which` function cannot find the given command."""
    pass

class Process(object):
    """Abstract base class for Processes. Handles all process handling, and
    some common functionality. I/O is handled in subclasses.
    """
    def __init__(self, cmdline, logfile=None, callback=None, async=False, flags=0, devnull=False):
        self.cmdline = cmdline
        self.deadchild = 0
        self.callback = callback # called at death of process
        self._log = logfile # should be file-like object
        self._restart = True # restart interrupted system calls
        self._rawq = []
        self._buf = ''
        self._errbuf = ''
        self._writebuf = ''
        self.exitstatus = None
        self._async = bool(async) # use asyncio, or not
        self._flags = int(flags)

#   def __del__(self):
#       if not self.deadchild:
#           self.killwait()
#       self.close()

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.cmdline, self._log)

    def __str__(self):
        if self.deadchild:
            return str(self.exitstatus)
        else:
            st = self.stat()
            try:
                tty = os.ttyname(self.fileno())
            except:
                tty = "?"
            return "%6d %-7s (%s) %s" % (st.pid, tty, st.statestr(), self.cmdline)

    def __int__(self):
        return self.childpid

    def __hash__(self):
        return id(self)

    def restart(self, flag=1):
        old = self._restart
        self._restart = bool(flag)
        return old

    def newlog(self, newlog):
        newlog.write # asserts newlog has write method
        self._log = newlog
    setlog = newlog

    def getlog(self):
        return self._log
    
    def removelog(self):
        self._log = None

    logfile = property(getlog, newlog, removelog, "logfile object")

    def log(self, entry):
        if self._log:
            self._log.write(entry)

    def flushlog(self):
        if self._log:
            self._log.flush()
    
    def clone(self, env=None):
        """clone([newenv])
Spawns a copy of this process. Note that the log file is not inherited."""
        return self.__class__(self.cmdline, env=env, callback=self.callback, async=self._async)

    def basename(self):
        return os.path.basename(self.cmdline.split()[0])

    def kill(self, sig=SIGTERM):
        if not self.deadchild:
            os.kill(self.childpid, sig)

    def killwait(self, sig=SIGTERM):
        if not self.deadchild:
            os.kill(self.childpid, sig)
        return self.wait()

    def stop(self):
        os.kill(self.childpid, SIGSTOP)

    def cont(self):
        os.kill(self.childpid, SIGCONT)
        self.deadchild = 0

    def hangup(self):
        os.kill(self.childpid, SIGHUP)

    def wait(self, option=0):
        """wait() retrieves process exit status. Note that this may block if
the process is still running."""
        pm = get_procmanager()
        pm.waitproc(self, option)
        return self.exitstatus

    def setpgid(self, pgid):
        os.setpgid(self.childpid, pgid)

    def set_exitstatus(self, exitstatus):
        self.exitstatus = exitstatus

    def set_callback(self, cb=None):
        """set_callback(cb) Sets the callback function that will be
called when child dies. """
        self.callback = cb

    def dead(self):
        """dead() Called when the child dies. Usually only the
ProcManager uses this."""
        self.deadchild = 1
        if self.callback:
            self.callback(self)

    def stat(self):
        if not self.deadchild:
            return ProcStat(self.childpid)
        else:
            return self.exitstatus

    def fstat(self):
        return os.fstat(self.fileno())

    def isdead(self):
        return self.deadchild
    # process object considered true if child alive, false if child dead
    def __nonzero__(self):
        return not self.deadchild

    def read(self, amt=2147483646):
        if amt < 0:
            amt = 2147483646
        bs = len(self._buf)
        try:
            while bs < amt:
                if self._rawq:
                    c = self._rawq.pop(0)
                else:
                    c = self._read(4096)
                if not c:
                    break
                self._buf += c
                bs = len(self._buf)
        except EOFError: # XXX log an error
            pass # let it ruturn rest of buffer
        data = self._buf[:amt]
        self._buf = self._buf[amt:]
        return data

    def readerr(self, amt=2147483646):
        if amt < 0:
            amt = 2147483646
        rs = 1024
        try:
            while len(self._errbuf) < amt:
                c = self._readerr(rs)
                if not c:
                    break
                self._errbuf += c
        except EOFError:
            pass
        amt = min(amt, len(self._errbuf))
        data = self._errbuf[:amt]
        self._errbuf = self._errbuf[amt:]
        return data

# extra fileobject methods. 
    def readline(self, amt=2147483646):
        if amt < 0:
            amt = 2147483646
        bufs = []
        rs = min(100, amt)
        while 1:
            c = self.read(rs)
            i = c.find("\n")

            if i < 0 and len(c) > amt:
                i = amt-1
            elif amt <= i:
                i = amt-1
            if i >= 0 or c == '':
                bufs.append(c[:i+1])
                self._unread(c[i+1:])
                return "".join(bufs)

            bufs.append(c)
            amt -= len(c)
            rs = min(amt, rs*2)

    def readlines(self, sizehint=2147483646):
        if sizehint < 0:
            sizehint = 2147483646
        rv = []
        while sizehint > 0:
            line = self.readline()
            if not line:
                break
            rv.append(line)
            sizehint -= len(line)
        return rv

    def _write_buf(self):
        writ = self._write(self._writebuf)
        self._writebuf = self._writebuf[writ:]
        return writ

    def write(self, data):
        while self._writebuf:
            writ = self._write(self._writebuf)
            self._writebuf = data[writ:]
        writ = self._write(data)
        self._writebuf = data[writ:]
        return writ
    send = write

    def tell(self):
        raise IOError, (EBADF, "Process object not seekable")

    def seek(self, pos, whence=0):
        raise IOError, (EBADF, "Process object not seekable")

    def rewind(self):
        raise IOError, (EBADF, "Process object not seekable")

    def flush(self):
        return None

    def _unread(self, data):
        self._buf = data + self._buf

    # just fill local buffer. 
    def _read_fill(self):
        try:
            data = self._read(16384)
            if not data:
                return
            self._rawq.append(data)
        except (IOError, EOFError):
            ex, val, tb = sys.exc_info()
            print >>sys.stderr, "*** Error:", ex, val

    def _readerr_fill(self):
        try:
            c = self._readerr(8192)
            if not c:
                return
            self._errbuf += c
        except (IOError, EOFError):
            ex, val, tb = sys.exc_info()
            print >>sys.stderr, "*** Error:", ex, val

# interfaces for asyncio poller/manager.
    def readable(self):
        return bool(self._rawq)

    def writable(self):
        return len(self._writebuf)

    def priority(self):
        return 0

    def handle_hangup_event(self):
        pass
        #self._read_fill()

    def handle_error(self, ex, val, tb):
        if self._log:
            self._log.write("error event: %s (%s)\n" % (ex, val))



class ProcessPipe(Process):
    """Process(<commandline>, [<logfile>], [environ])
    Forks and execs a process as given by the command line argument. The
    process's stdio is connected to this instance via pipes, and can be read
    and written to by the instances read() and write() methods.

    """
    def __init__(self, cmdline, logfile=None,  env=None, callback=None, merge=1, pwent=None, async=False, devnull=None):
        Process.__init__(self, cmdline, logfile, callback, async)

        cmd = split_command_line(self.cmdline)
        # now, fork the child connected by pipes
        p2cread, self._p_stdin = os.pipe()
        self._p_stdout, c2pwrite = os.pipe()
        if merge:
            self._stderr, c2perr = None, None
        else:
            self._stderr, c2perr = os.pipe()
        self.childpid = os.fork()
        self.childpid2 = None # for compatibility with pipeline
        if self.childpid == 0:
            # Child
            os.close(0)
            os.close(1)
            os.close(2)
            if os.dup(p2cread) <> 0:
                os._exit(1)
            if os.dup(c2pwrite) <> 1:
                os._exit(1)
            if merge:
                if os.dup(c2pwrite) <> 2: # merge stderr into stdout from child process
                    os._exit(1)
            else:
                if os.dup(c2perr) <> 2:
                    os._exit(1)
            # close all other file descriptors for child.
            for i in xrange(3, 255):
                try:
                    os.close(i)
                except: pass
            try:
                if pwent:
                    run_as(pwent)
                if env:
                    os.execvpe(cmd[0], cmd, env)
                else:
                    os.execvp(cmd[0], cmd)
            finally:
                os._exit(1)
            # Shouldn't come here
            os._exit(1)
        os.close(p2cread)
        os.close(c2pwrite)
        if c2perr:
            os.close(c2perr)

    def isatty(self):
        return os.isatty(self._p_stdin)

    def fileno(self): 
        if self._p_stdout is None:
            raise ValueError, "I/O operation on closed process"
        return self._p_stdout

    def filenos(self):
        """filenos() Returns tuple of all file descriptors used in this object."""
        if self._p_stdout is None:
            raise ValueError, "I/O operation on closed process"
        return self._p_stdout, self._p_stdin, self._stderr

    def nonblocking(self, flag=1):
        for fd in self._p_stdout, self._p_stdin, self._stderr:
           set_nonblocking(fd, flag)

    def interrupt(self):
        self.kill(SIGINT)

    def close(self):
        try:
            os.close(self._p_stdin)
        except (TypeError, OSError):
            pass
        try:
            os.close(self._p_stdout)
        except (TypeError, OSError):
            pass
        if self._stderr:
            try:
                os.close(self._stderr)
            except (TypeError, OSError):
                pass
            self._stderr = None
        self._p_stdin = None
        self._p_stdout = None
        self.callback = None # break a possible reference loop

    def _write(self, data):
        while 1:
            try:
                writ = os.write(self._p_stdin, data)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                return writ

    def _read_fd(self, fd, length):
        while 1:
            try:
                next = os.read(fd, length)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        if self._log:
            self._log.write(next)
        return next

    def _read(self, amt=4096):
        if self._p_stdout is None:
            return ""
        return self._read_fd(self._p_stdout, amt)

    def _readerr(self, amt):
        if self._stderr is None:
            return ""
        return self._read_fd(self._stderr, amt)

    # poller interface method
    def err_readable(self):
        return self._stderr # true

    def get_handlers(self):
        outh = asyncio.HandlerMethods(self._p_stdout, 
                 readable=self.readable, read_handler=self._read_fill)
        inh =  asyncio.HandlerMethods(self._p_stdin, 
                 writable=self.writable, write_handler=self._write_buf)
        if self._stderr is None:
            return outh, inh
        else:
            return (outh, inh, asyncio.HandlerMethods(self._stderr, 
                 readable=self.err_readable, read_handler=self._readerr_fill))



class ProcessPty(Process):
    """ProcessPty(<commandline>, [<logfilename>], [environ])
    Forks and execs a process as given by the command line argument. The
    process's stdio is connected to this instance via a pty, and can be read
    and written to by the instances read() and write() methods. That pty
    becomes the processes controlling terminal. 

    """
    def __init__(self, cmdline, logfile=None, env=None, callback=None, merge=1, pwent=None, async=False, devnull=False):
        Process.__init__(self, cmdline, logfile, callback, async)
        cmd = split_command_line(self.cmdline)
        try:
            pid, self._fd = os.forkpty()
        except OSError, err:
            print >>sys.stderr, "ProcessPty: Cannot forkpty."
            print >>sys.stderr, str(err)
        else:
            if pid == 0: # child
                for i in xrange(3, 256):
                    try:
                        os.close(i)
                    except: pass
                if devnull:
                    # Redirect standard file descriptors.
                    sys.stdout.flush()
                    sys.stderr.flush()
                    os.close(sys.__stdin__.fileno())
                    os.close(sys.__stdout__.fileno())
                    os.close(sys.__stderr__.fileno())
                    # stdin always from /dev/null
                    sys.stdin = open("/dev/null", 'r')
                    os.dup2(sys.stdin.fileno(), 0)
                    # log file is stdout and stderr, otherwise /dev/null
                    if logfile is None:
                        sys.stdout = open("/dev/null", 'a+')
                        sys.stderr = open("/dev/null", 'a+', 0)
                        os.dup2(sys.stdout.fileno(), 1)
                        os.dup2(sys.stderr.fileno(), 2)
                    else:
                        so = se = sys.stdout = sys.stderr = logfile
                        os.dup2(so.fileno(), 1)
                        os.dup2(se.fileno(), 2)

                try:
                    if pwent:
                        run_as(pwent)
                    if env:
                        os.execvpe(cmd[0], cmd, env)
                    else:
                        os.execvp(cmd[0], cmd)
                finally:
                    os._exit(1) # should not be reached

            else: # parent
                self.childpid = pid
                self.childpid2 = None # for compatibility with pipeline
                self._intr = None

    def isatty(self):
        return os.isatty(self._fd)

    def fileno(self):
        if self._fd is None:
            raise ValueError, "I/O operation on closed process"
        return self._fd

    def filenos(self):
        """filenos() Returns tuple of all file descriptors used in this object."""
        if self._fd is None:
            raise ValueError, "I/O operation on closed process"
        return (self._fd,)

    def nonblocking(self, flag=1):
        set_nonblocking(self._fd, flag)

    def interrupt(self):
        if self._intr is None:
            from pycopia import tty
            self._intr = tty.get_intr_char(self._fd)
        self._write(self._intr)

    def close(self):
        try:
            os.close(self._fd)
        except (TypeError, OSError):
            pass
        self._fd = None
        self.callback = None # break a possible reference loop

    def _write(self, data):
        while 1:
            try:
                writ = os.write(self._fd, data)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                return writ

    def _read(self, length=100):
        while 1:
            try:
                next = os.read(self._fd, length)
            except EnvironmentError, why:
                if self._restart and why.errno == EINTR:
                    continue
                elif why.errno == EIO:
                    raise EOFError, "pty is closed"
                else:
                    raise
            else:
                break
        if self._log:
            self._log.write(next)
        return next
    

    def get_handlers(self):
        return (
            asyncio.HandlerMethods(self._fd, 
                 readable=self.readable, read_handler=self._read_fill,
                 writable=self.writable, write_handler=self._write_buf,
                 hangup_handler=self.handle_hangup_event),)


# A process connected by a named pipe
# XXX
class ProcessNamedPipe(Process):
    pass


class CoProcessPty(ProcessPty):
    def __init__(self, method, logfile=None, env=None, 
                    callback=None, async=False, pwent=None):
        Process.__init__(self, "python: %s" % (method.func_name,), logfile, callback, async)
        pid, self._fd = os.forkpty()
        self.childpid = pid
        self.childpid2 = None # for compatibility with pipeline
        if pid == 0 and pwent:
            run_as(pwent)


class CoProcessPipe(ProcessPipe):
    def __init__(self, method, logfile=None, env=None, 
                    callback=None, merge=False, async=False, pwent=None):
        Process.__init__(self, "python <=> %s" % (method.func_name,), logfile, callback, async)

        p2cread, self._p_stdin = os.pipe()
        self._p_stdout, c2pwrite = os.pipe()
        if merge:
            self._stderr, c2perr = None, None
        else:
            self._stderr, c2perr = os.pipe()
        self.childpid = os.fork()
        self.childpid2 = None
        if self.childpid == 0:
            # Child
            os.close(0)
            os.close(1)
            os.close(2)
            if os.dup(p2cread) <> 0:
                os._exit(1)
            if os.dup(c2pwrite) <> 1:
                os._exit(1)
            if merge:
                if os.dup(c2pwrite) <> 2:
                    os._exit(1)
            else:
                if os.dup(c2perr) <> 2:
                    os._exit(1)

            if pwent:
                run_as(pwent)

        os.close(p2cread)
        os.close(c2pwrite)
        if c2perr:
            os.close(c2perr)


# simply forks this python process
class SubProcess(Process):
    def __init__(self, pwent=None):
        Process.__init__(self, sys.argv[0])
        pid = os.fork()
        if pid == 0 and pwent:
            run_as(pwent)
        self.childpid = pid
        self.childpid2 = None # for compatibility with pipeline

# XXX need a more general pipeline
class ProcessPipeline(ProcessPipe):
    """Connects two commands via a pipe, they appear as one process object."""
    def __init__(self, cmdline, logfile=None,  env=None, callback=None, 
                    merge=None, pwent=None, async=False, devnull=None):
        assert cmdline.count("|") == 1
        [cmdline1, cmdline2] = cmdline.split("|")
        Process.__init__(self, cmdline2, logfile, callback, async)
        self._stderr= None

        cmd1 = split_command_line(cmdline1)
        cmd2 = split_command_line(cmdline2)

        # self._p_stdin -> cmd1 -> p_write|p_read -> cmd2 -> self._p_stdout

        _p_stdout, self._p_stdin = os.pipe()
        p_read, p_write = os.pipe()
        self._p_stdout, _p_stdin = os.pipe()

        self.childpid = os.fork()
        # cmd1
        if self.childpid == 0:
            # Child 1
            os.dup2(_p_stdout, 0)
            os.dup2(p_write, 1)
            self._exec(cmd1, env, pwent)
            os._exit(99)

        # cmd2
        cmd2pid = os.fork()
        #os.setpgid(pid, pgrp)
        if cmd2pid == 0:
            # Child 2
            os.dup2(p_read, 0)
            os.dup2(_p_stdin, 1)
            self._exec(cmd2, env, pwent)
            os._exit(99)

        self.childpid2 = cmd2pid # XXX
        # close our copies
        os.close(_p_stdout)
        os.close(_p_stdin)
        os.close(p_read)
        os.close(p_write)

    def _exec(self, cmd, env, pwent):
        # close all other file descriptors for child.
        if pwent:
            run_as(pwent)
        for i in xrange(3, 256):
            try:
                os.close(i)
            except: 
                pass
        if env:
            os.execvpe(cmd[0], cmd, env)
        else:
            os.execvp(cmd[0], cmd)


class ExitStatus(object):
    EXITED = 1
    STOPPED = 2
    SIGNALED = 3
    def __init__(self, cmdline, sts):
        self.cmdline = cmdline
        if os.WIFEXITED(sts):
            self.state = 1
            self._status = self._es = os.WEXITSTATUS(sts)

        elif os.WIFSTOPPED(sts):
            self.state = 2
            self._status = self.stopsig = os.WSTOPSIG(sts)

        elif os.WIFSIGNALED(sts):
            self.state = 3
            self._status = self.termsig = os.WTERMSIG(sts)

    def status(self):
        return self.state, self._status

    def exited(self):
        return self.state == 1
    
    def stopped(self):
        return self.state == 2
    
    def signalled(self):
        return self.state == 3
    
    def __int__(self):
        if self.state == 1:
            return self._status
        else:
            name = self.cmdline.split()[0]
            raise ValueError, "ExitStatus: %r did not exit normally." % (name,)

    # exit status truth value is true if normal exit, and false otherwise.
    def __nonzero__(self):
        return (self.state == 1) and not self._status

    def __str__(self):
        name = self.cmdline.split()[0]
        if self.state == 1:
            if self._es == 0:
                return "%s: Exited normally." % (name)
            else:
                return "%s: Exited abnormally with status %d." % (name, self._es)
        elif self.state == 2:
            return "%s is stopped." % (name)
        elif self.state == 3:
            return "%s exited by signal %d. " % (name, self.termsig)
        else:
            return "FIXME! unknown state"


# this is the SIGCHLD signal handler
def _child_handler(sig, stack):
    procmanager.waitpid(-1, os.WNOHANG)
    # reset handler
    signal(SIGCHLD, _child_handler)

class ProcManager(object):
    """An instance of ProcManager manages a collection of child processes. It
is a singleton, and you should use the get_procmanager() factory function
to get the instance.  """

    def __init__(self):
        self._procs = {}
        self._graveyard = {}
        self.poller = asyncio.get_poller()
        self.poll = self.poller.poll # delegate poll method
        signal(SIGCHLD, _child_handler)
    
    def __len__(self):
        return len(self._procs)

    def __str__(self):
        s = []
        for p in self.getprocs():
            s.append(str(p))
        return "\n".join(s)
    
    def spawnprocess(self, pklass, cmd, logfile=None, env=None, callback=None, 
                persistent=False, merge=True, pwent=None, async=False, devnull=False):
        """spawnclass(classobj, cmd, logfile=None, env=None, callback=None, persistent=0) 
Start a child process using a user supplied subclass of ProcessPty or
ProcessPipe.  """

        if persistent and (callback is None):
            callback = self._persistent_callback
        signal(SIGCHLD, SIG_DFL) # critical area
        proc = pklass(cmd, logfile=logfile, env=env, callback=callback, 
                    merge=merge, pwent=pwent, async=async, devnull=devnull)
        self._procs[proc.childpid] = proc
        # XXX need a more general pipeline
        if proc.childpid2:
            self._procs[proc.childpid2] = proc
        signal(SIGCHLD, _child_handler)
        if proc._async:
            self.poller.register(proc)
        return proc

    def spawnpipe(self, cmd, logfile=None, env=None, callback=None, 
                    persistent=False, merge=True, pwent=None, async=False, devnull=False):
        """spawn(cmd, logfile=None, env=None, callback=None, persisten=None)
Start a child process, connected by pipes."""
        if cmd.find("|") > 0:
            klass = ProcessPipeline
        else:
            klass = ProcessPipe
        return self.spawnprocess(klass, cmd, logfile, env, callback, 
                    persistent, merge, async, devnull)

    # default spawn method
    spawn = spawnpipe

    def spawnpty(self, cmd, logfile=None, env=None, callback=None, 
                    persistent=False, merge=True, pwent=None, async=False, devnull=False):
        """spawnpty(cmd, logfile=None, env=None, callback=None, persisten=None)
Start a child process using a pty. The <persistent> variable is the number of
times the process will be respawned if the previous invocation dies.  """
        return self.spawnprocess(ProcessPty, cmd, logfile, env, callback, 
                    persistent, merge, pwent, async, devnull)

    def coprocess(self, method, args=(), logfile=None, env=None, callback=None, async=False):
        signal(SIGCHLD, SIG_DFL) # critical area
        #proc = CoProcessPty(method, logfile=logfile, env=env, callback=callback, async=async)
        proc = CoProcessPipe(method, logfile=logfile, env=env, callback=callback, async=async)
        if proc.childpid == 0:
            sys.excepthook = sys.__excepthook__
            # child is not managing any of these
            self._procs.clear()
            self._graveyard.clear()
            self.poller.clear()
            try:
                rv = apply(method, args)
            except SystemExit, val:
                rv = int(val)
            except:
                ex, val, tb = sys.exc_info()
                tb = None
                errfile = open("/tmp/proctools_coprocess.log", "w")
                print >>errfile, "Coprocess exception: %s (%s)." % (ex, val)
                errfile.close()
                rv = 127
            if rv is None:
                rv = 0
            try:
                rv = int(rv)
            except:
                rv = 0
            os._exit(rv)
        self._procs[proc.childpid] = proc
        signal(SIGCHLD, _child_handler)
        if proc._async:
            self.poller.register(proc)
        return proc

    def subprocess(self, _method, *args, **kwargs):
        return self.submethod(_method, args, kwargs)

    def submethod(self, _method, args=None, kwargs=None, pwent=None):
        args = args or ()
        kwargs = kwargs or {}
        signal(SIGCHLD, SIG_DFL) # critical area
        proc = SubProcess(pwent=pwent)
        if proc.childpid == 0: # in child
            sys.excepthook = sys.__excepthook__
            self._procs.clear()
            self._graveyard.clear()
            self.poller.clear()
            try:
                rv = _method(*args, **kwargs)
            except SystemExit, val:
                rv = int(val)
            except:
                ex, val, tb = sys.exc_info()
                tb = None
                errfile = open("/tmp/proctools_submethod.log", "w")
                print >>errfile, "Submethod exception: %s (%s)." % (ex, val)
                errfile.close()
                rv = 127
            if rv is None:
                rv = 0
            try:
                rv = int(rv)
            except:
                rv = 0
            os._exit(rv)
        else:
            self._procs[proc.childpid] = proc
            signal(SIGCHLD, _child_handler)
            return proc


    # introspection and query methods
    def getpids(self):
        """getpids() Returns a list of managed PIDs (which are integers)."""
        return self._procs.keys()

    def getprocs(self):
        """getprocs() Returns a list of managed process objects."""
        return self._procs.values()

    def getbyname(self, name):
        """getbyname(procname) Returns a list of process objects that match the given name."""
        name = os.path.basename(name)
        return filter(lambda p: p.basename() == name, self._procs.values())

    def getbypid(self, pid):
        """getbypid(pid) Returns the process object that matches the given PID."""
        try:
            return self._procs[pid]
        except KeyError:
            return None

    def getstats(self):
        """getstats() Returns a list of process status objects (ProcStat) for each managed process."""
        return map(ProcStat, self._procs.keys())

    def killall(self, name=None, sig=SIGTERM):
        """killall([name, [SIG]]) Kills all managed processes with the name
'name'. If 'name' not given kill ALL processes. Default signal is SIGTERM."""
        if name is None:
            procs = self._procs.values()
        else:
            procs = self.getbyname(name)
        for p in procs:
            self.kill(p, sig)

    def kill(self, proc, sig=SIGTERM):
        proc.set_callback(None) # explicit kill means no restart
        proc.kill(sig)

    def stopall(self):
        """stopall() sends STOP to all managed processes. To restart get the
process objects and invoke the cont() method."""
        for p in self._procs.values():
            p.stop()

    def waitproc(self, proc, option=0): # waits for a Process object.
        """waitproc(process, [option])
Waits for a process object to finish. Works like os.waitpid, but takes a
process object instead of a process ID.  """
        pid = int(proc)
        while 1:
            if pid in self._graveyard:
                es = self._graveyard[pid]
                del self._graveyard[pid]
                return es
            elif pid in self._procs:
                if (option & os.WNOHANG):
                    return 0
                self.waitpid(pid, 0)
            else:
                raise ValueError, "pid or proc is unmanaged."

    def clone(self, proc=None):
        """clone([proc]) clones the supplied process object and manages it as
well. If no process object is supplied then clone the first managed
process found in this ProcManager."""
        if proc is None: # default to cloning first process found.
            procs = self._procs.values()
            if procs:
                proc = procs[0]
                del procs
            else:
                return
        signal(SIGCHLD, SIG_DFL) # critical area
        newproc = proc.clone()
        self._procs[newproc.childpid] = newproc 
        signal(SIGCHLD, _child_handler)
        return newproc

    def _persistent_callback(self, deadproc):
        if not deadproc.exitstatus: # abnormal exit
            deadproc.log("*** process '%s' died: %s (restarting).\n" % (deadproc.cmdline, deadproc.exitstatus))
            scheduler.sleep(1.0)
            new = self.clone(deadproc)
            new.logfile = deadproc.logfile
            if new._async:
                self.poller.register(new)
        else:
            deadproc.log("*** process '%s' normal exit (NOT restarting).\n" % (deadproc.cmdline,))

    def child_status(self, pid_or_proc):
        pid = int(pid_or_proc)
        try:
            es = self._graveyard[pid]
            del self._graveyard[pid]
            return es
        except KeyError:
            try:
                proc = self._procs[pid]
                return proc.stat()
            except KeyError:
                return None # XXX exception?

    def waitpid(self, pid, option=0):
        while 1: # loop to collect all pending exited processes
            try:
                pid, sts = os.waitpid(pid, option)
            except EnvironmentError, why:
                if why.errno == ECHILD: # no children left
                    break
                elif why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                if pid == 0: # no child ready
                    break
                else:
                    try:
                        proc = self._procs[pid]
                    except KeyError:
                        sys.stderr.write("warning: caught SIGCHLD for unmanaged process (pid: %s).\n" % pid) 
                        continue
                    es = ExitStatus(proc.cmdline, sts)
                    proc.set_exitstatus(es)
                    if es.state != ExitStatus.STOPPED: # XXX untested with stopped processes
                        if proc._async:
                            self.poller.unregister(proc)
                        proc.dead()
                        del self._procs[pid]
                        self._graveyard[pid] = proc.exitstatus

    def flushlogs(self):
        "Force flushing all process logs."
        for proc in self._procs.values():
            proc.flushlog()

def get_procmanager():
    """get_procmanager() returns the procmanager. A ProcManager is a singleton
instance. Always use this factory function to get it."""
    global procmanager
    try:
        return procmanager
    except NameError:
        procmanager = ProcManager()
    return procmanager


def remove_procmanager():
    global procmanager
    signal(SIGCHLD, SIG_DFL)
    del procmanager 

#######################################
#### Utility functions for Linux ######

# standalone process factory functions
def spawnpipe(cmd, logfile=None, env=None, callback=None, 
                persistent=False, merge=True, pwent=None, async=False):
    """spawn(cmd, logfile=None, env=None)
Start a child process, connected by pipes."""
    pm = get_procmanager()
    proc = pm.spawnpipe(cmd, logfile, env, callback, persistent, merge, pwent, async)
    return proc


def spawnpty(cmd, logfile=None, env=None, callback=None, 
                persistent=False, merge=True, pwent=None, async=False, devnull=False):
    """spawnpty(cmd, logfile=None, env=None)
Start a child process using a pty."""
    pm = get_procmanager()
    proc = pm.spawnpty(cmd, logfile, env, callback, persistent, merge, pwent, async, devnull)
    return proc


def coprocess(func, args=(), logfile=None, env=None, callback=None, async=0):
    """coprocess(func, args, [logfile, callback])
Works like fork(), but connects the childs stdio to a pty. Returns a file-like
object connected to the master end of the child pty.  """
    pm = get_procmanager()
    cp = pm.coprocess(func, args, logfile, env, callback, async)
    return cp


def run_as(pwent, umask=022):
  """Drop privileges to given user's password entry, and set up
  environment. Assumes the parent process has root privileges.
  """
  os.umask(umask)
  home = pwent.home
  try:
    os.chdir(home) 
  except OSError:
    os.chdir("/") 
  # drop privs to user
  os.setgroups(pwent.groups)
  os.setgid(pwent.gid)
  os.setegid(pwent.gid)
  os.setuid(pwent.uid)
  os.seteuid(pwent.uid)
  os.environ["HOME"] = home
  os.environ["USER"] = pwent.name
  os.environ["LOGNAME"] = pwent.name
  os.environ["SHELL"] = pwent.shell
  os.environ["PATH"] = "/bin:/usr/bin:/usr/local/bin"

def waitproc(proc, option=0):
    pm = get_procmanager()
    return pm.waitproc(proc, option)

def subprocess(method, *args, **kwargs):
    pm = get_procmanager()
    return pm.subprocess(method, *args, **kwargs)

def submethod(_method, args=None, kwargs=None, pwent=None):
    pm = get_procmanager()
    return pm.submethod(_method, args, kwargs, pwent)

def getstatusoutput(cmd, logfile=None, env=None, callback=None):
    p = spawnpipe(cmd, logfile, env, callback)
    text = p.read()
    p.wait()
    return p.exitstatus, text

def set_nonblocking(fd, flag=1):
    import fcntl
    try:
        fd = int(fd)
    except TypeError:
        return
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    if flag:
        flags |= os.O_NONBLOCK # set non-blocking
    else:
        flags &= ~os.O_NONBLOCK # set blocking
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def system(cmd):
    sts = os.system(cmd)
    return ExitStatus(cmd, sts)

def call(*args, **kwargs):
    return spawnpipe(*args, **kwargs).wait()

def setpgid(pid_or_proc, pgrp):
    pid = int(pid_or_proc)
    return os.setpgid(pid, pgrp)

def which(basename):
    """Returns the fully qualified path name (by searching PATH) of the given program name."""
    for pe in os.environ["PATH"].split(os.pathsep):
        testname = os.path.join(pe, basename)
        if os.access(testname, os.X_OK):
            return testname
    raise NotFoundError, "which: no %r found in $PATH." % (basename,)


split_command_line = shparser.get_command_splitter()



if __name__ == "__main__":
    print system("qaunittest test_proctools")

