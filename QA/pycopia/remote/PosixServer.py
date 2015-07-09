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
Remote control agent that runs on Posix systems.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os, sys, shutil, errno

from pycopia import proctools
from pycopia import UserFile
from pycopia import passwd
from pycopia import logging
from pycopia.remote import pyro



_EXIT = False # signals the server wants to exit.

class PosixFile(UserFile.UserFile):
    def __repr__(self):
        return "PosixFile(%r, %r)" % (self.name, self.mode)

# A server that performs client operations. This mostly delegates to the
# os module. But some special methods are provided for common functions.
class PosixAgent(object):
    def __init__(self):
        self._files = {}
        self._status = {} # holds async process pids
        self._dirstack = []

    def platform(self):
        return sys.platform

    def whatami(self):
        """Return agent implementation (class name)."""
        return self.__class__.__name__

    # Since file objects are not pickle-able, a handle is returned. Use the
    # handle for subsequent file operations on f* methods.
    def fopen(self, fname, mode="r", bufsize=-1):
        "Opens a file object and returns a handle to it."
        fo = PosixFile(fname, mode, bufsize)
        handle = fo.fileno()
        self._files[handle] = fo
        return handle

    def fclose(self, handle):
        "Closes a file object given the handle."
        fo = self._files.get(handle, None)
        if fo:
            fo.close()
            del self._files[handle]

    def fread(self, handle, amt=-1):
        "Reads from the file object given the handle and amount to read."
        fo = self._files.get(handle, None)
        if fo:
            return fo.read(amt)
        else:
            return ''

    def fwrite(self, handle, data):
        "Writes to a file object given the handle."
        fo = self._files.get(handle, None)
        if fo:
            return fo.write(data)

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
            return fo.seek(pos, how)

    def ftell(self, handle):
        "Tell where the seek pointer is in the file object."
        fo = self._files.get(handle, None)
        if fo:
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

    def flock(self, handle, length=0, start=0, whence=0, nonblocking=False):
        """Lock the file with the given range."""
        fo = self._files.get(handle, None)
        if fo:
            return fo.lock_exclusive(length, start, whence, nonblocking)

    def funlock(self, handle, length, start=0, whence=0):
        fo = self._files.get(handle, None)
        if fo:
            fo.unlock(length, start, whence)

    def fstat(self, handle):
        fo = self._files.get(handle, None)
        if fo:
            return os.fstat(fo.fileno())

    def fstatvfs(self, handle):
        fo = self._files.get(handle, None)
        if fo:
            return os.fstatvfs(fo.fileno())

    def ftruncate(self, handle, length):
        fo = self._files.get(handle, None)
        if fo:
            return os.ftruncate(fo.fileno(), length)

    def flist(self):
        return self._files.keys()

    def get_handle_info(self, handle):
        fo = self._files.get(handle, None)
        if fo:
            return repr(fo) # XXX
        else:
            return None

    def unlink(self, path):
        "Unlink (delete) the given file."
        return os.unlink(path)

    def rename(self, src, dst):
        "Rename file from src to dst."
        return os.rename(src, dst)

    # directory methods
    def mkdir(self, path, mode=0777):
        "Make a directory."
        return os.mkdir(path, mode)

    def makedirs(self, path, mode=0777):
        "Make a full path."
        return os.makedirs(path, mode)

    def chdir(self, path):
        return os.chdir(path)

    def rmdir(self, path):
        "Delete a directory."
        return os.rmdir(path)

    def getcwd(self):
        return os.getcwd()

    def getcwdu(self):
        return os.getcwdu()

    def pushd(self, path=None):
        self._dirstack.append(os.getcwd())
        if path:
            os.chdir(path)

    def popd(self):
        try:
            path = self._dirstack.pop()
        except IndexError:
            return None
        else:
            os.chdir(path)
            return path

    def get_pwent(self, name=None, uid=None):
        if uid is not None:
            return passwd.getpwuid(int(uid))
        return passwd.getpwnam(name)

    def listdir(self, path):
        return os.listdir(path)

    def listfiles(self, path):
        isfile = os.path.isfile
        pjoin = os.path.join
        rv = []
        for fname in os.listdir(path):
            if isfile(pjoin(path, fname)):
                rv.append(fname)
        return rv

    def chmod(self, path, mode):
        return os.chmod(path, mode)

    def chown(self, path, uid, gid):
        return os.chown(path, uid, gid)

    def stat(self, path):
        return os.stat(path)

    def statvfs(self, path):
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
        return shutil.move(src, dst)

    def rmtree(self, path):
        self._rmtree_errors = []
        shutil.rmtree(path, ignore_errors=True, onerror=self._rmtree_error_cb)
        return self._rmtree_errors

    def _rmtree_error_cb(self, func, arg, exc):
        self._rmtree_errors.append((str(arg), str(exc[1])))

    # os.path delegates
    def exists(self, path):
        return os.path.exists(path)
    def isabs(self, path):
        return os.path.isabs(path)
    def isdir(self, path):
        return os.path.isdir(path)
    def isfile(self, path):
        return os.path.isfile(path)
    def islink(self, path):
        return os.path.islink(path)
    def ismount(self, path):
        return os.path.ismount(path)

    def system(self, cmd):
        return proctools.system("%s >/dev/null 2>&1" % cmd)

    def run(self, cmd, user=None):
        """Run a subprocess, wait for completion and return status and
        stdout as text.
        """
        logging.msg("run", cmd, "user=", str(user))
        pm = proctools.get_procmanager()
        if type(user) is str:
            user = passwd.getpwnam(user)
        proc = pm.spawnpty(cmd, pwent=user)
        text = proc.read()
        sts = proc.wait()
        proc.close()
        return sts, text

    def pipe(self, cmd, user=None):
        """Run a subprocess, but connect by pipes rather than pty."""
        logging.msg("pipe", cmd, "user=", str(user))
        pm = proctools.get_procmanager()
        if type(user) is str:
            user = passwd.getpwnam(user)
        proc = pm.spawnpipe(cmd, pwent=user, callback=self._status_cb)
        text = proc.read()
        sts = proc.wait()
        proc.close()
        return sts, text

    def spawn(self, cmd, user=None, async=False):
        """Spawn a subprocess and return immediatly."""
        pm = proctools.get_procmanager()
        if type(user) is str:
            user = passwd.getpwnam(user)
        proc = pm.spawnpty(cmd, callback=self._status_cb, pwent=user, async=async)
        # status with a key present, but None value means a running process.
        self._status[proc.childpid] = None
        logging.msg("spawn", cmd, "user=%s async=%s pid=%d" % (user, async, proc.childpid))
        return proc.childpid

    def subprocess(self, _meth, *args, **kwargs):
        """Run a python method asynchronously as a subprocess."""
        logging.msg("subprocess", str(_meth))
        pm = proctools.get_procmanager()
        proc = pm.submethod(_meth, args, kwargs)
        proc.callback = self._status_cb
        self._status[proc.childpid] = None
        return proc.childpid

    def _status_cb(self, proc):
        self._status[proc.childpid] = proc.exitstatus
        logging.msg("exited", str(proc.exitstatus))

    def _get_process(self, pid):
        pm = proctools.get_procmanager()
        return pm.getbypid(pid)

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
        """Poll for async process.

        Returns exitstatus if done, -ENOENT if no such pid is managed, or -EAGAIN
        if pid is still running.
        """
        try:
            sts  = self._status[pid]
        except KeyError:
            return -errno.ENOENT
        if sts is None:
            return -errno.EAGAIN
        else: # finished
            del self._status[pid]
            return sts

    def waitpid(self, pid):
        pm = proctools.get_procmanager()
        while True:
            rv = self.poll(pid)
            if rv == -errno.ENOENT:
                return None
            if rv == -errno.EAGAIN:
                pm.waitpid(pid)
                es = self.poll(pid)
                del self._status[pid]
                return es
            else: # already exited
                es = self.poll(pid)
                del self._status[pid]
                return es

    def kill(self, pid):
        """Kills a process that was started by spawn."""
        logging.msg("kill", str(pid))
        try:
            sts = self._status.pop(pid)
        except KeyError:
            return -errno.ENOENT
        else:
            if sts is None: # a running process
                pm = proctools.get_procmanager()
                proc = pm.getbypid(pid)
                proc.kill()
                proc.wait()
                sts = self.poll(pid)
                return sts
            else: # already exited
                return sts

    def killall(self):
        rv = []
        for pid in self._status:
            rv.append(self.kill(pid))
        return rv

    def plist(self):
        return self._status.keys()

    def pstat(self, pid):
        pm = proctools.get_procmanager()
        proc = pm.getbypid(pid)
        if proc is not None:
            return proc.stat()
        else:
            return -errno.ENOENT


    def python(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<PosixAgent>', 'eval')
            rv = eval(code, globals(), vars(self))
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return rv

    def pyexec(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<PosixAgent>', 'exec')
            exec code in globals(), vars(self)
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return True

    # method that exists just to check if everything is working
    def alive(self):
        return True
    ping = alive

    # used to force external shell script to reload us
    def suicide(self):
        global _EXIT
        _EXIT = True

    def clean(self):
        self.chdir("/tmp")
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

    def hostname(self):
        """Returns the client hosts name."""
        return os.uname()[1]

    def md5sums(self, path):
        """Reads the md5sums.txt file in path and returns the number of files
        checked good, then number bad (failures), and a list of the failures."""
        from pycopia import md5lib
        return md5lib.md5sums(path)

    def get_tarball(self, url):
        self.pushd(os.environ["HOME"])
        # the ncftpget will check if the file is current, will not download if not necessary
        exitstatus, out = self.pipe('wget -q "%s"' % (url,))
        self.popd()
        return exitstatus

    def run_script(self, script):
        """Runs a script from a shell."""
        name = os.path.join("/", "tmp", "_clientserver-%d-%d" % (os.getpid(),id(script)))
        if os.path.islink(name):
            raise IOError, "temp name is symlinked!"
        sfile = open(name, "w+")
        sfile.write(str(script))
        sfile.write("\n") # just in case string has no newline at the end
        sfile.close()
        try:
            os.chmod(name, 0555)
            sts, out = self.run("sh -c %s" % (name,))
        finally:
            os.unlink(name)
        return sts, out



###################################
######## main program #############

_DOC = """qaagentd [-nh?] [-p <pidfile>]

Starts the Posix QA agent (server).

Where:
    -n = Do NOT run as a daemon, but stay in foreground.
    -p = Write the process ID to this file.

"""

def run_server(argv):
    import getopt
    do_daemon = True
    pidfile = None
    try:
        optlist, args = getopt.getopt(argv[1:], "nh?p:")
    except getopt.GetoptError:
        print(_DOC)
        sys.exit(2)

    for opt, optarg in optlist:
        if opt in ("-h", "-?"):
            print(_DOC)
            return
        elif opt == "-n":
            do_daemon = False
        elif opt == "-p":
            pidfile = optarg

    if do_daemon:
        from pycopia import daemonize
        daemonize.daemonize(pidfile=pidfile)

    logging.msg("qaagent", "initializing")
    h = pyro.register_server(PosixAgent())
    def _exit_checker(poller):
        if _EXIT:
            pyro.unregister_server(h)
    try:
        pyro.loop(2.0, _exit_checker)
    finally:
        if do_daemon and pidfile:
            os.unlink(pidfile)



if __name__ == "__main__":
    from pycopia import autodebug
    #run_server(sys.argv)
    run_server(["qaagentd", "-n"])
