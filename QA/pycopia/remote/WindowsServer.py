#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

r"""
Implements a Windows version of a client responder. This should run with the
native Python for Windows.

Install on a Windows server:

Place the following lines in c:\autoexec.bat::

    PATH=%PATH%;C:\Python23;C:\Python23\Scripts

Now run (all on one line)::

    C:\Python23>python.exe %PYTHONLIB%\lib\remote\WindowsServer.py 
            --username DOMAIN\Administrator --password xxxxxxxx install

Now, go to the Service Manger from the Windows control panel, and perform the following.

    - Select "Client Operations Server" from the list. Right-clieck and select "properties".
    - Select the "Log On" tab. 
    - Click the "This account:" radio button.
    - Enter QA1\Administrator in the account box (or something else appropriate).
    - Enter the proper password (twice).
    - Click "Apply". You should confirm a message saying Administrator is being
      added to services group or some such.
    - Click "General" tab.
    - You may now start the service.

"""


import os, sys, shutil, errno
import threading

# Pycopia imports
from pycopia.aid import IF
from pycopia.anypath import cygwin2nt, nt2cygwin
from pycopia import shparser
 # returnable objects
from pycopia.remote.WindowsObjects import ExitStatus

# Windows stuff
import msvcrt
import win32api
import win32file
import win32net
import win32process
import win32event
# constants
import pywintypes
import win32con
import win32netcon
# some constants that the API forgot...
USE_WILDCARD = -1
USE_DISKDEV = 0
USE_SPOOLDEV = 1
USE_CHARDEV = 2
USE_IPC = 3

def setConfig():
    #Pyro.config.PYRO_MULTITHREADED = 0
    #Pyro.config.PYRO_STORAGE = os.path.splitdrive(win32api.GetSystemDirectory())[0]+os.sep
    Pyro.config.PYRO_STORAGE = "C:\\tmp\\"
    Pyro.config.PYRO_LOGFILE = "C:\\tmp\\ClientServer_svc.log"
    Pyro.config.PYRO_TRACELEVEL=3
    Pyro.config.PYRO_USER_LOGFILE = "C:\\tmp\\COS_user.log"
    Pyro.config.PYRO_USER_TRACELEVEL = 3
    Pyro.config.PYRO_PORT = 7867 # don't conflict with cygwin Pyro
    Pyro.config.PYRO_NS_URIFILE = os.path.join(Pyro.config.PYRO_STORAGE, "ClientServer_URI.txt")


import Pyro
import Pyro.util
setConfig()
Log=Pyro.util.Log
import Pyro.core
import Pyro.naming

from Pyro.ext.BasicNTService import BasicNTService, getRegistryParameters

_EXIT = False

UserLog = Pyro.util.UserLogger()
# msg, warn, or error methods

class WindowsFile(file):
    """A file object with some extra methods that match those in UserFile
    (which has Posix extensions)."""
    def locking(self, mode, nbytes):
        return msvcrt.locking(self.fileno(), mode, nbytes)

    def __repr__(self):
        return "WindowsFile(%r, %r)" % (self.name, self.mode)

    def lock_exclusive(self, length, start=0, whence=0, nb=0):
        """Locking method compatible with Posix files."""
        if nb:
            mode = msvcrt.LK_NBLCK
        else:
            mode = msvcrt.LK_LOCK
        orig = self.tell()
        self.seek(start, whence)
        try:
            msvcrt.locking(self.fileno(), mode, length)
        finally:
            self.seek(orig)
    lock = lock_exclusive

    def unlock(self, length, start=0, whence=0):
        """Posix compatible unlock."""
        orig = self.tell()
        self.seek(start, whence)
        try:
            msvcrt.locking(self.fileno(), msvcrt.LK_UNLCK, length)
        finally:
            self.seek(orig)

    def get_osfhandle(self):
        return msvcrt.get_osfhandle(self.fileno())


split_command_line = shparser.get_command_splitter()

# quick hack ... Windows sucks. No signal handling or anything useful, so it has to be faked.
class WindowsProcess(object):
    def __init__(self, cmdline, logfile=None,  env=None, callback=None, merge=True, pwent=None, async=False):
        self.deadchild = False
        self.exitstatus = None
        self.cmdline = cmdline
        self._callback = callback
        self._buf = ""
        self._log = logfile
        if merge:
            self.child_stdin, self.child_stdout = os.popen2(cmdline, "t", -1)
            self.child_stderr = None
        else:
            self.child_stdin, self.child_stdout, self.child_stderr = os.popen3(cmdline, "t", -1)
        self.childpid, self.handle = self._scan_for_self()

    # since the Python popenX functions do not provide the PID, it must be
    # scanned for in this ugly manner. 8-(
    def _scan_for_self(self):
        win32api.Sleep(2000) # sleep to give time for process to be seen in system table.
        basename = self.cmdline.split()[0]
        pids = win32process.EnumProcesses()
        if not pids:
            UserLog.warn("WindowsProcess", "no pids", pids)
        for pid in pids:
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                        pywintypes.FALSE, pid)
            except pywintypes.error, err:
                UserLog.warn("WindowsProcess", str(err))
                continue
            try:
                modlist = win32process.EnumProcessModules(handle)
            except pywintypes.error,err:
                UserLog.warn("WindowsProcess",str(err))
                continue
            for mod in modlist:
                mname = win32process.GetModuleFileNameEx(handle, mod)
                if mname.find(basename) >= 0:
                    return int(pid), handle
        raise WindowsError, "could not find process for %r" % (basename,)

    def write(self, data):
        return self.child_stdin.write(data)

    def kill(self):
        handle = win32api.OpenProcess(
            win32con.PROCESS_VM_READ | win32con.PROCESS_TERMINATE, pywintypes.FALSE, self.childpid)
        win32process.TerminateProcess(handle, 3)

    def read(self, amt=1048576):
        bs = len(self._buf)
        while bs < amt:
            c = self._read(4096)
            if not c:
                break
            self._buf += c
            bs = len(self._buf)
        data = self._buf[:amt]
        self._buf = self._buf[amt:]
        return data

    def readerr(self, amt=-1):
        if self.child_stderr:
            return self.child_stderr.read(amt)

    def _read(self, amt):
        data = self.child_stdout.read(amt)
        if self._log:
            self._log.write(data)
        return data

    def close(self):
        if win32process.GetExitCodeProcess(self.handle) == win32con.STILL_ACTIVE:
            self.kill()
        self.child_stdin.close()
        self.child_stdin = None
        if self.child_stderr:
            self.child_stdin.close()
            self.child_stdin = None
        es = ExitStatus(self.cmdline, self.child_stdout.close())
        if self.exitstatus is None:
            self.exitstatus = es
        self.child_stdout = None
        self.dead()
        return self.exitstatus

    def poll(self):
        es = win32process.GetExitCodeProcess(self.handle)
        if es == win32con.STILL_ACTIVE:
            return None
        else:
            self.exitstatus = ExitStatus(self.cmdline, es)
            self.dead()
            return self.exitstatus

    # called when process determined to be daed
    def dead(self):
        if not self.deadchild:
            self.deadchild = True
            if self._callback:
                self._callback(self)

    # check if still running
    def alive(self):
        es = win32process.GetExitCodeProcess(self.handle)
        if es == win32con.STILL_ACTIVE:
            return True
        else:
            return False

    # wait until finished
    def wait(self):
        # let python read until EOF for a wait
        try:
            self._buf += self.child_stdout.read()
            self.close()
        except: # closed file?
            pass
        return self.exitstatus

    def status(self):
        return self.exitstatus

    def isdead(self):
        return self.deadchild
    # considered true if child alive, false if child dead
    def __nonzero__(self):
        return not self.deadchild


# A server that performs filer client operations. This mostly delegates to the
# os module. But some special methods are provided for common functions.
class ClientServer(Pyro.core.SynchronizedObjBase, object):
    def __init__(self):
        Pyro.core.SynchronizedObjBase.__init__(self)
        self._files = {}
        self._procs = {}
        self._dirstack = []

    def platform(self):
        return sys.platform

    # Since file objects are not pickle-able, a handle is returned. Use the
    # handle for subsequent file operations on f* methods.
    def fopen(self, fname, mode="r", bufsize=-1):
        "Opens a file object and returns a handle to it."
        fname = cygwin2nt(fname)
        fo = WindowsFile(fname, mode, bufsize)
        UserLog.msg("fopen", fname)
        handle = fo.fileno()
        self._files[handle] = fo
        return handle

    def CreateFile(self, fname, mode="r", bufsize=-1):
        "Open a file the same way a File Directory migration engine would."
        fname = cygwin2nt(fname)
        UserLog.msg("CreateFile", fname)
        if mode == "r":
            wmode = win32file.GENERIC_READ
        elif mode == "w":
            wmode = win32file.GENERIC_WRITE
        elif mode in ( 'r+', 'w+', 'a+'):
            wmode = win32file.GENERIC_READ | win32file.GENERIC_WRITE
        else:
            raise ValueError, "invalid file mode"
        h = win32file.CreateFile(
            fname,                           #  CTSTR lpFileName,
            wmode,                           #  DWORD dwDesiredAccess,
            win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE, #  DWORD dwShareMode,
            None,                            #  LPSECURITY_ATTRIBUTES lpSecurityAttributes,
            win32file.OPEN_EXISTING,         #  DWORD dwCreationDisposition,
            win32file.FILE_ATTRIBUTE_NORMAL, #  DWORD dwFlagsAndAttributes,
            0,                               #  HANDLE hTemplateFile
            )
        self._files[int(h)] = h
        return int(h)

    def fclose(self, handle):
        "Closes a file object given the handle."
        fo = self._files.get(handle, None)
        if fo:
            if type(fo) is WindowsFile:
                fo.close()
                del self._files[handle]
            else:
                fo.Close() # pyHANDLE from CreateFile

    def fread(self, handle, amt=-1):
        "Reads from the file object given the handle and amount to read."
        fo = self._files.get(handle, None)
        if fo:
            if type(fo) is WindowsFile:
                return fo.read(amt)
            else:
                return win32file.ReadFile(fo, amt, None)

    def fwrite(self, handle, data):
        "Writes to a file object given the handle."
        fo = self._files.get(handle, None)
        if fo:
            if type(fo) is WindowsFile:
                return fo.write(data)
            else:
                return win32file.WriteFile(fo, data, None)

    def fsync(self, handle):
        "fsync the file object."
        fo = self._files.get(handle, None)
        if fo:
            fo.flush()
            return os.fsync(fo.fileno())

    def fseek(self, handle, pos, how=0):
        "Seek in the file object."
        fo = self._files.get(handle, None)
        if fo:
            if type(fo) is WindowsFile:
                return fo.seek(pos, how)
            else:
                win32file.SetFilePointer(fo, pos, how)

    def ftell(self, handle):
        "Tell where the seek pointer is in the file object."
        fo = self._files.get(handle, None)
        if fo:
            if type(fo) is WindowsFile:
                return fo.tell()

    def fflush(self, handle):
        """Flush the file object buffer."""
        fo = self._files.get(handle, None)
        if fo:
            return fo.flush()

    def fileno(self, handle):
        "Return the file objects file descriptor."
        fo = self._files.get(handle, None)
        if fo:
            return fo.fileno()

    def get_handle_info(self, handle):
        fo = self._files.get(handle, None)
        if fo:
            return repr(fo) # XXX
        else:
            return None

    def flock(self, handle, length=0, start=0, whence=0, nonblocking=False):
        """Lock the file with the given range."""
        fo = self._files.get(handle, None)
        if fo:
            return fo.lock_exclusive(length, start, whence, nonblocking)

    def funlock(self, handle, length, start=0, whence=0):
        fo = self._files.get(handle, None)
        if fo:
            fo.unlock(length, start, whence)

    def flist(self):
        return self._files.keys()

    def unlink(self, path):
        "Unlink (delete) the given file."
        path = cygwin2nt(path)
        return os.unlink(path)

    def rename(self, src, dst):
        "Rename file from src to dst."
        src = cygwin2nt(src)
        dst = cygwin2nt(dst)
        return os.rename(src, dst)

    # directory methods
    def mkdir(self, path, mode=0777):
        "Make a directory."
        path = cygwin2nt(path)
        return os.mkdir(path, mode)

    def makedirs(self, path, mode=0777):
        "Make a full path."
        path = cygwin2nt(path)
        return os.makedirs(path, mode)

    def chdir(self, path):
        path = cygwin2nt(path)
        return os.chdir(path)

    def rmdir(self, path):
        "Delete a directory."
        path = cygwin2nt(path)
        return os.rmdir(path)

    def getcwd(self):
        return os.getcwd()

    def getcwdu(self):
        return os.getcwdu()

    def pushd(self, path=None):
        self._dirstack.append(os.getcwd())
        if path:
            path = cygwin2nt(path)
            os.chdir(path)

    def popd(self):
        try:
            path = self._dirstack.pop()
        except IndexError:
            return None
        else:
            os.chdir(path)
            return path

    def listdir(self, path):
        path = cygwin2nt(path)
        return os.listdir(path)
    ls = listdir

    def listfiles(self, path):
        path = cygwin2nt(path)
        isfile = os.path.isfile
        pjoin = os.path.join
        rv = []
        for fname in os.listdir(path):
            if isfile(pjoin(path, fname)):
                rv.append(nt2cygwin(fname))
        return rv

    def chmod(self, path, mode):
        path = cygwin2nt(path)
        return os.chmod(path, mode)

    def chown(self, path, uid, gid):
        path = cygwin2nt(path)
        return os.chown(path, uid, gid)

    def stat(self, path):
        path = cygwin2nt(path)
        return os.stat(path)

    def statvfs(self, path):
        path = cygwin2nt(path)
        return os.statvfs(path)

    # fd ops ruturn the file descript as handle (of course)
    def open(self, fname, flags, mode=0777):
        fd = os.open(fname, mode)
        return fd

    def close(self, fd):
        return os.close(fd)

    def write(self, fd, data):
        return os.write(fd, data)

    def read(self, fd, n):
        return os.read(fd, n)

    # end fd ops

    # shutil interface
    def copyfile(self,src, dst):
        return shutil.copyfile(src, dst)

    def copymode(self, src, dst):
        return shutil.copymode(src, dst)

    def copystat(self, src, dst):
        return shutil.copystat(src, dst)

    def copy(self, src, dst):
        return shutil.copy(src, dst)

    def copy2(self, src, dst):
        return shutil.copy2(src, dst)

    def copytree(self, src, dst, symlinks=False):
        return shutil.copytree(src, dst, symlinks)

    def move(self, src, dst):
        return win32file.MoveFile(unicode(src), unicode(dst))

    def rmtree(self, path):
        path = cygwin2nt(path)
        for fname in os.listdir(path):
            file_or_dir = os.path.join(path, fname)
            if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
                self.rmtree(file_or_dir) #it's a directory reucursive call to function again
            else:
                try:
                    os.remove(file_or_dir) #it's a file, delete it
                except:
                    #probably failed because it is not a normal file
                    win32api.SetFileAttributes(file_or_dir, win32file.FILE_ATTRIBUTE_NORMAL)
                    os.remove(file_or_dir) #it's a file, delete it
        os.rmdir(path) #delete the directory here

    # os.path delegates
    def exists(self, path):
        path = cygwin2nt(path)
        return os.path.exists(path)
    def isabs(self, path):
        path = cygwin2nt(path)
        return os.path.isabs(path)
    def isdir(self, path):
        path = cygwin2nt(path)
        return os.path.isdir(path)
    def isfile(self, path):
        path = cygwin2nt(path)
        return os.path.isfile(path)
    def islink(self, path):
        path = cygwin2nt(path)
        return os.path.islink(path)
    def ismount(self, path):
        path = cygwin2nt(path)
        return os.path.ismount(path)

    # process control, these calls are syncronous (they block)
    def system(self, cmd):
        UserLog.msg("system", cmd)
        return os.system(cmd) # remember, stdout is on the server

    def run(self, cmd, user=None):
        UserLog.msg("run", cmd, str(user))
        if user is None:
            return self.pipe(cmd)
        else:
            return self.run_as(cmd, user.name, user.passwd)

    def run_async(self, cmd, user=None):
        UserLog.msg("run_async", cmd, str(user))
        proc = WindowsProcess(cmd, pwent=user)
        self._procs[proc.childpid] = proc
        return proc.childpid

    def _get_process(self, pid):
        return self._procs.get(pid, None)

    def read_process(self, pid, N=-1):
        proc = self._get_process(pid)
        if proc:
            return proc.read(N)
        else:
            return ''

    def write_process(self, pid, data):
        proc = self._get_process(pid)
        if proc:
            return proc.write(data)

    def poll(self, pid):
        """Poll for async process. Returns exitstatus if done."""
        try:
            proc = self._procs[pid]
        except KeyError:
            return -errno.ENOENT
        if proc.poll() is None:
            return -errno.EAGAIN
        else:
            del self._procs[pid]
            return proc.exitstatus

    def waitpid(self, pid):
        while True:
            rv = self.poll(pid)
            if rv == -errno.ENOENT:
                return None
            if rv == -errno.EAGAIN:
                proc = self._procs[pid]
                es = proc.wait()
                del self._procs[pid]
                return es
            else: # already exited
                del self._procs[pid]
                return rv

    def kill(self, pid):
        """Kills a process that was started by run_async."""
        try:
            proc = self._procs.pop(pid)
        except KeyError:
            return -errno.ENOENT
        else:
            proc.kill()
            sts = proc.wait()
            return sts

    def killall(self):
        rv = []
        for pid in self._procs:
            rv.append(self.kill(pid))
        return rv

    def plist(self):
        return self._procs.keys()

    def spawn(self, cmd):
        UserLog.msg("spawn", cmd)
        L = split_command_line(cmd)
        pid = os.spawnv(os.P_DETACH, L[0], L)
        return pid

    def pipe(self, cmd):
        UserLog.msg("pipe", cmd)
        proc = os.popen(cmd, 'r')
        text = proc.read()
        sts = proc.close()
        if sts is None:
            sts = 0
        return ExitStatus(cmd, sts), text

    def python(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<WindowsServer>', 'eval')
            rv = eval(code, globals(), vars(self))
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return rv

    def pyexec(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<WindowsServer>', 'exec')
            exec code in globals(), vars(self)
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return

    # method that exists just to check if everything is working
    def alive(self):
        return True

    def suicide(self):
        "Kill myself. The server manager will ressurect me. How nice."
        global _EXIT
        _EXIT = True

    def clean(self):
        self.chdir("C:\\tmp")
        for f in self.flist():
            try:
                self.fclose(f)
            except:
                pass
        for pid in self.plist():
            try:
                self.kill(pid)
            except:
                pass

    def NetUseAdd(self, drive, share, username=None, domainname=None, password=None):
        """Calls Windows API to map a drive. Note that this does not automatically use DFS."""
        ui2={}
        ui2['local'] = "%s:" % drive[0].upper()
        ui2['remote'] = str(share) # \\servername\sharename
        ui2['asg_type'] = USE_DISKDEV
        if username:
            ui2['username'] = str(username)
        if domainname:
            ui2['domainname'] = str(domainname)
        if password:
            ui2['password'] = str(password)
        return win32net.NetUseAdd(None,2,ui2)

    def NetUseDelete(self, drive, forcelevel=0):
        """Remove a mapped drive."""
        ui2 = win32net.NetUseGetInfo(None, "%s:" % drive[0].upper(), 2)
        return win32net.NetUseDel(None, ui2['remote'], max(0, min(forcelevel, 3)))
        #win32net.USE_NOFORCE
        #win32net.USE_FORCE
        #win32net.USE_LOTS_OF_FORCE

    def net_use(self, drive, share, user=None, domainname=None, password=None):
        """Map a drive on a Windows client using the *net* command."""
        cmd = "net use %s: %s %s" % (drive[0].upper(), share, IF(password, password, ""))
        if user:
            cmd += " /USER:%s%s" % (IF(domainname, "%s\\"%domainname, ""), user)
        return self.pipe(cmd)

    def net_use_delete(self, drive):
        """Unmap a drive on a Windows client using the *net* command."""
        cmd = "net use  %s: /delete /y" % (drive[0].upper(),)
        return self.pipe(cmd)

    def md5sums(self, path):
        """Reads the md5sums.txt file in path and returns the number of files
        checked good, then number bad (failures), and a list of the failures."""
        from pycopia import md5lib
        failures = []
        counter = Counter()
        md5lib.check_md5sums(path, failures.append, counter)
        return counter.good, counter.bad, failures

    def _get_home(self):
        try: # F&*#!&@ windows
            HOME = os.environ['USERPROFILE']
        except KeyError:
            try:
                HOME = os.path.join(os.environ["HOMEDRIVE"], os.environ["HOMEPATH"])
            except KeyError:
                HOME = "C:\\"
        return HOME

    def get_tarball(self, url):
        self.pushd(self._get_home())
        # the ncftpget will check if the file is current, will not download if not needed
        exitstatus, out = self.pipe('ncftpget -V "%s"' % (url,))
        self.popd()
        return exitstatus

    def run_script(self, script):
        """Runs a script from a shell."""
        name = os.path.join("c:\\", "tmp", "clnt%d.bat" % (os.getpid(),))
        sfile = open(name, "w")
        sfile.write(str(script))
        sfile.write("\n") # just in case string has no newline at the end
        sfile.close()
        try:
            sts, out = self.pipe(name)
        finally:
            os.unlink(name)
        return ExitStatus("cmd.exe", sts), out

    # for PosixServer polymorphism
    def mount(self, host, export, mountpoint):
        """Map a drive on a client. Same as mount on NFS. The mountpoint should
        be a drive letter (without the colon).  """
        return self.net_use(mountpoint, r"\\%s\%s" % (host, export))

    def umount(self, mountpoint):
        """Unmap a drive on a client."""
        return self.net_use_delete(mountpoint)

    def run_as(self, cmd, user, password):
        cmd = 'runas /user:%s %s' % (user, cmd)
        UserLog.msg("run_as", cmd)
        return self.pipe(cmd)

    def get_short_pathname(self, path):
        """Get the short file name of path."""
        path = cygwin2nt(path)
        return win32api.GetShortPathName(path)

    def win32(self, funcname, *args, **kwargs):
        """Generic interface to win32. Calls a win32api function by name."""
        f = getattr(win32api, funcname)
        return f(*args, **kwargs)

    def hostname(self):
        """Returns the client hosts name."""
        return win32api.GetComputerName()

    # Windows file API interface
    def CopyFile(self, src, dst):
        src = cygwin2nt(src)
        dst = cygwin2nt(dst)
        return win32file.CopyFile(src, dst, 1)

    def GetFileAttributes(self, name):
        name = cygwin2nt(name)
        return win32file.GetFileAttributes(name)

    def GetFileAttributeFlags(self):
        return {
        "ARCHIVE":win32file.FILE_ATTRIBUTE_ARCHIVE,
        "COMPRESSED":win32file.FILE_ATTRIBUTE_COMPRESSED,
        "DIRECTORY":win32file.FILE_ATTRIBUTE_DIRECTORY,
        "HIDDEN":win32file.FILE_ATTRIBUTE_HIDDEN,
        "NORMAL":win32file.FILE_ATTRIBUTE_NORMAL,
        "OFFLINE":win32file.FILE_ATTRIBUTE_OFFLINE,
        "READONLY":win32file.FILE_ATTRIBUTE_READONLY,
        "SYSTEM":win32file.FILE_ATTRIBUTE_SYSTEM,
        "TEMPORARY":win32file.FILE_ATTRIBUTE_TEMPORARY,
        }

    def SetFileAttributes(self, name, flags):
        name = cygwin2nt(name)
        return win32file.SetFileAttributes(name, flags)

    def add_share(self, pathname):
        """Create a new share on this server. A directory is also created.  """
        drive, sharename = os.path.split(pathname)
        if not os.path.isdir(pathname):
            os.mkdir(pathname)
        shinfo={} # shinfo struct
        shinfo['netname'] = sharename
        shinfo['type'] = win32netcon.STYPE_DISKTREE
        shinfo['remark'] = 'Testing share %s' % (sharename,)
        shinfo['permissions'] = 0
        shinfo['max_uses'] = -1
        shinfo['current_uses'] = 0
        shinfo['path'] = pathname
        shinfo['passwd'] = ''
        win32net.NetShareAdd(None,2,shinfo)
        return sharename

    def del_share(self, pathname):
        """Remove a share. Returns True if successful, False otherwise."""
        drive, sharename = os.path.split(pathname)
        try:
            win32net.NetShareDel(None, sharename, 0)
        except:
            ex, val, tb = sys.exc_info()
            UserLog.warn("del_share", str(ex), str(val))
            return False
        else:
            return True

# md5sums callback for counting files
class Counter(object):
    def __init__(self):
        self.good = 0
        self.bad = 0

    def __call__(self, name, disp):
        if disp:
            self.good += 1
        else:
            self.bad += 1


######## main program #####

class ClientServerThread(threading.Thread):
    """ The Pyro Naming Service will run in this thread
    """
    def __init__(self, args, stopcallback):
        threading.Thread.__init__(self)
        Log.msg("ClientServer", "initializing")
        self._args = list(args)
        self._stopcallback = stopcallback

    def run(self):
        try:
            run_server()
        except Exception,x :
            Log.error("NS daemon","COULD NOT START!!!",x)
            raise SystemExit
        self._stopcallback()


def run_server():
    os.chdir("C:\\tmp")
    Pyro.core.initServer(banner=0, storageCheck=0)
    ns=Pyro.naming.NameServerLocator().getNS()

    daemon=Pyro.core.Daemon()
    daemon.useNameServer(ns)

    uri=daemon.connectPersistent(ClientServer(), 
                ":Client.%s" % (win32api.GetComputerName().lower(),))
    daemon.requestLoop(_checkexit)
    daemon.shutdown()

def _checkexit():
    global _EXIT
    return not _EXIT

class ClientServerService(BasicNTService):
    _svc_name_ = 'ClientServerService'
    _svc_display_name_ = "Client Operations Server"
    _svc_description_ = 'Provides Windows Client API methods.'
    def __init__(self, args):
        BasicNTService.__init__(self, args)
        setConfig()
        try:
            args = getRegistryParameters(self._svc_name_).split()
        except Exception,x:
            Log.error("PyroNS_svc","PROBLEM GETTING ARGS FROM REGISTRY:",x)
        self._thread = ClientServerThread(args, self.SvcStop)

    def _doRun(self):
        self._thread.start()

    def _doStop(self):
        self._thread.join()
        self._thread = None


if __name__ == '__main__':
    ClientServerService.HandleCommandLine()

