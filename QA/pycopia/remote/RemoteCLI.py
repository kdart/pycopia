#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 1999-2009  Keith Dart <keith@kdart.com>
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
Command line interface to Remote QA agent servers.

"""

import sys, os, time, errno

os.environ["PYRO_CONFIG_FILE"] = "/etc/pycopia/Pyro.conf"

import Pyro.core
import Pyro.naming
import Pyro.errors

from pycopia import CLI
from pycopia import UI
from pycopia import cliutils
from pycopia.remote import Client

PROMPT = "remote> "

class FileCommand(CLI.BaseCommands):
    WHENCES = {"set":0, "current":1, "end":2}
    def _setup(self, client, handle, prompt):
        self._obj = client
        self._handle = handle
        self._environ["PS1"] = prompt
        self._namespace = {"client":client, "environ":self._environ}
        self._reset_scopes()

    def close(self, argv):
        """close
    Close the file object."""
        self._obj.fclose(self._handle)
        raise CLI.CommandQuit, self._handle

    def read(self, argv):
        """read <N>
    Read N bytes from object."""
        try:
            n = int(argv[1])
        except:
            n = -1
        rv = self._obj.fread(self._handle, n)
        if rv:
            self._print(rv)
        return rv

    def write(self, argv):
        """write <data>
    Writes <data> to file object."""
        data = " ".join(argv[1:])
        rv = self._obj.fwrite(self._handle, data)
        return rv

    def writefrom(self, argv):
        """writefrom <filename>
    Writes from the local file into this interactive remote file object."""
        fname = argv[1]
        fo = open(fname)
        try:
            data = fo.read(1024)
            while data:
                self._obj.fwrite(self._handle, data)
                data = fo.read(1024)
        finally:
            fo.close()

    def fileno(self, argv):
        """fileno
    Get the file descriptor."""
        return self._obj.fileno(self._handle)

    def lock(self, argv):
        """lock <length> <start> [whence]
    Sets an exclusive lock on the file. The extent of bytes is given by
    <length>, and starting position by <start>. The start position is dependent
    on <whence>. 
    Values for whence:
        "set" - relative to the start of the file (SEEK_SET) 
        "current" - relative to the current buffer position (SEEK_CUR) 
        "end" - relative to the end of the file (SEEK_END) """
        length = int(argv[1])
        start = int(argv[2])
        if len(argv) > 3:
            whence = self.WHENCES.get(argv[3], 0)
        else:
            whence = 0
        return self._obj.flock(self._handle, length, start, whence)

    def unlock(self, argv):
        """unlock <length> <start> <whence>
    Unlocks the byte range specified by <length>, <starte>, and <whence>."""
        length = int(argv[1])
        start = int(argv[2])
        if len(argv) > 3:
            whence = self.WHENCES.get(argv[3], 0)
        else:
            whence = 0
        self._obj.funlock(self._handle, length, start, whence)

    def seek(self, argv):
        """seek <pos> [<whence>]
    Seek the file to the indicated postion. Whence is one of
    "set", "current", or "end", and defaults to "set". """
        pos = int(argv[1])
        if len(argv) > 2:
            whence = self.WHENCES.get(argv[2], 0)
        else:
            whence = 0
        return self._obj.fseek(self._handle, pos, whence)

    def tell(self, argv):
        """tell
    Prints the current seek pointer offset."""
        offset = self._obj.ftell(self._handle)
        self._print(offset)
        return offset

    def flush(self, argv):
        """flush
    Flush the buffered data to the file."""
        return self._obj.fflush(self._handle)

    def sync(self, argv):
        """sync
    Syncs this file to disk."""
        return self._obj.fsync(self._handle)

    def statvfs(self, argv):
        """statvfs 
    Print information about the volume that this file is located in."""
        vfsstat = self._obj.fstatvfs(self._handle)
        self._print("Volume stats:")
        self._print("               fragment size = %s" % (vfsstat.f_frsize,))
        self._print("                      blocks = %s" % (vfsstat.f_blocks,))
        self._print("                 blocks free = %s" % (vfsstat.f_bfree,))
        self._print(" blocks available (non-root) = %s" % (vfsstat.f_bavail,))
        self._print("          no. files (inodes) = %s" % (vfsstat.f_files,))
        self._print("                 free inodes = %s" % (vfsstat.f_ffree,))
        self._print("      free inodes (non-root) = %s" % (vfsstat.f_favail,))
        self._print("     maximum filename length = %s" % (vfsstat.f_namemax,))
        self._print("                 mount flags = %s" % (vfsstat.f_flag,))
        return vfsstat

    def stat(self, argv):
        """stat
    Print information about this file."""
        stat = self._obj.fstat(self._handle)
        self._print("Stats:")
        self._print("      inode = %s" % (stat.st_ino,))
        self._print("       mode = %o" % (stat.st_mode,))
        self._print(" hard links = %s" % (stat.st_nlink,))
        self._print("    user id = %s" % (stat.st_uid,))
        self._print("   group id = %s" % (stat.st_gid,))
        self._print("       size = %s" % (stat.st_size,))
        self._print("     device = %s" % (stat.st_dev,))
        self._print("access time = %s" % (time.ctime(stat.st_atime),))
        self._print("   mod time = %s" % (time.ctime(stat.st_mtime),))
        self._print("change time = %s" % (time.ctime(stat.st_ctime),))
        return stat


class ProcCommand(CLI.BaseCommands):
    def _setup(self, client, pid, prompt):
        self._obj = client
        self._pid = pid
        self._environ["PS1"] = prompt
        self._namespace = {"client":client, "pid":pid, "environ":self._environ}
        self._reset_scopes()

    def read(self, argv):
        """read <N>
    Read N bytes from process."""
        try:
            n = int(argv[1])
        except:
            n = -1
        rv = self._obj.read_process(self._pid, n)
        if rv:
            self._print(rv)
        return rv

    def write(self, argv):
        """write <data>
    Writes <data> to process object."""
        data = " ".join(argv[1:])
        rv = self._obj.write_process(self._pid, data)
        return rv

    def kill(self, argv):
        """kill
    Kills this interactive process."""
        es = self._obj.kill(self._pid)
        self._print(str(es))
        raise CLI.CommandQuit, self._pid

    def poll(self, argv):
        """poll
    Polls this process object."""
        sts = self._obj.poll(self._pid)
        if sts == -errno.EAGAIN:
            self._print("running.")
        elif sts == -errno.ENOENT:
            self._print("Process disappeared!")
            raise CLI.CommandQuit, self._pid
        else:
            self._print(sts)
            self._print("Exited.")
            raise CLI.CommandQuit, self._pid


# main command class
class RemoteCLI(CLI.BaseCommands):

    PROMPTFORMAT = "Agent:%s> "

    def _setup(self, client, name):
        self._obj = client
        self._environ["PS1"] = self.PROMPTFORMAT % name
        self._namespace = {"client":client, "environ":self._environ}
        self._reset_scopes()

    def _generic_call(self, argv):
        meth = getattr(self._obj, argv[0])
        args, kwargs = CLI.breakout_args(argv[1:], vars(self._obj))
        rv = apply(meth, args, kwargs)
        if rv:
            self._print(rv)
        return rv

    def up(self, argv):
        """up
    Move context up to global context."""
        raise CLI.CommandQuit

    def alive(self, argv):
        """alive
    Check that the server is alive and kicking."""
        try:
            if self._obj.alive():
                self._print("Server is alive.")
            else:
                self._print("Server is NOT alive.")
        except:
            ex, val, tb = sys.exc_info()
            self._print("Problem with client:")
            self._print(ex, "\r", val)

    def suicide(self, argv):
        """suicide
    Make the remote agent exit."""
        self._obj.suicide()
        raise CLI.CommandQuit

    def run(self, argv):
        """run [-u <user>] <cmd>
    Runs the command on this client. Waits for process to exit.  """
        user = None
        opts, longopts, args = self.getopt(argv, "u:")
        for opt, arg in opts:
            if opt == "-u":
                user = arg
        es, res = self._obj.run(" ".join(args), user=user)
        self._print(res)
        return es

    def spawn(self, argv):
        """spawn [-a] [-u <user>] <cmd>
    Runs the command on this client, and returns immediatly.  
        Options:
          -u  <user> run as given user account.
          -a run async (performs automatic reads of process output).  """
        user = None
        async = False
        opts, longopts, args = self.getopt(argv, "au:")
        for opt, arg in opts:
            if opt == "-u":
                user = arg
            elif opt == "-a":
                async = True
        pid = self._obj.spawn(" ".join(args), user=user, async=async)
        self._print(pid)
        return pid

    def waitpid(self, argv):
        """waitpid <pid>
    Wait on a spawned process."""
        pid = int(argv[1])
        es = self._obj.waitpid(pid)
        self._print(es)
        return es

    def plist(self, argv):
        """plist
    List available file object handles."""
        return self._generic_call(argv)

    def pstat(self, argv):
        """pstat
    Show the stat info for the PID."""
        pid = int(argv[1])
        stat = self._obj.pstat(pid)
        if stat == -errno.ENOENT:
            self._print("Process not found.")
        else:
            self._print(stat)
        return stat

    def ps(self, argv):
        """ps [<pid>...]
    Show info on current managed processes."""
        if len(argv) > 1:
            pidlist = argv[1:]
        else:
            pidlist = self._obj.plist()
        for sPid in pidlist:
            stat = self._obj.pstat(int(sPid))
            if stat == -errno.ENOENT:
                continue
            self._print("{stat.pid!s}: {stat.cmdline}".format(stat=stat))

    def kill(self, argv):
        """kill <pid>...
    Kills the given asyncronous processes."""
        for arg in argv[1:]:
            try:
                pid = int(arg)
            except ValueError, err:
                self._print(err)
            else:
                self._obj.kill(pid)

    def poll(self, argv):
        """poll <pid>
    Determine that status of a background process."""
        pid = int(argv[1])
        sts = self._obj.poll(pid)
        if sts == -errno.EAGAIN:
            self._print("running.")
        elif sts == -errno.ENOENT:
            self._print("No such process.")
        else:
            self._print(sts)
            self._print("Exited.")

    def interact(self, argv):
        """interact <pid>
    Interact with the raw file-like interface of a process. Provide the pid as
    supplied from plist."""
        args, kwargs = CLI.breakout_args(argv[1:], vars(self._obj))
        if args:
            pid = int(args[0])
        else:
            pid = self._obj.plist()[0]
        pid = self._obj.poll(pid)
        if pid:
            cmd = self.clone(ProcCommand)
            cmd._setup(self._obj, pid, "pid %s> " % (pid,))
            raise CLI.NewCommand, cmd
        else:
            self._print("No such pid on server.")

    # called when subcommand FileCommand closes a file
    def handle_subcommand(self, value):
        if type(value) is int:
            pass

    def fiddle(self, argv):
        """fiddle <handle>
    fiddle with a remote file object. Provide the handle id obtained from 'flist'."""
        args, kwargs = CLI.breakout_args(argv[1:], vars(self._obj))
        if args:
            handle = args[0]
        else:
            handle = self._obj.flist()[0]
        finfo = self._obj.get_handle_info(handle)
        if finfo:
            cmd = self.clone(FileCommand)
            cmd._setup(self._obj, handle, "%s> " % (finfo,))
            raise CLI.NewCommand, cmd 
        else:
            self._print("No such handle on server.")

    def fopen(self, argv):
        """fopen <fname> [mode="r"] [bufsize=-1]
    Opens a file object and returns a handle to it."""
        return self._generic_call(argv)

    def fclose(self, argv):
        """fclose <handle>
    Closes the file with the given handle."""
        return self._generic_call(argv)

    def fread(self, argv):
        """fread <handle> [amt]
    Reads data from the file object."""
        return self._generic_call(argv)

    def fwrite(self, argv):
        """fwrite <handle> <data>
    Writes the given data to the file."""
        return self._generic_call(argv)

    def fsync(self, argv):
        """fsync <handle>
    Syncs the file object to disk."""
        return self._generic_call(argv)

    def fseek(self, argv):
        """fseek <handle> <pos> [how=0]
    Seeks the file object to the given position."""
        return self._generic_call(argv)

    def ftell(self, argv):
        """ftell <handle>
    Tell where the file seek pointer is."""
        return self._generic_call(argv)

    def flist(self, argv):
        """flist
    List available file object handles."""
        return self._generic_call(argv)

    def fileno(self, argv):
        """fileno <handle>
    The file object's file descriptor."""
        return self._generic_call(argv)

    def unlink(self, argv):
        """unlink path
    Unlink (delete) a file."""
        return self._generic_call(argv)

    def rename(self, argv):
        """rename <src> <dst>
    Renames a file. """
        return self._generic_call(argv)

    def mkdir(self, argv):
        """mkdir <path> [mode=0777]
    Make a new directory."""
        return self._generic_call(argv)

    def chdir(self, argv):
        """chdir <path>
    Change current directory to given path."""
        return self._generic_call(argv)
    cd = chdir # alias

    def rmdir(self, argv):
        """rmdir <path>
    Remove the given directory."""
        return self._generic_call(argv)

    def pushd(self, argv):
        """pushd [<path>]
    Push the current directory onto the dirstack. Optionally change to a new directory as well."""
        return self._generic_call(argv)

    def popd(self, argv):
        """popd
    Pop the last directory from the dirstack (which changes to current directory to it)."""
        return self._generic_call(argv)

    def getcwd(self, argv):
        """getcwd
    Return the current working directory."""
        return self._generic_call(argv)
    pwd = getcwd # alias

    def getcwdu(self, argv):
        """getcwdu
    Return the current working directory as a Unicode string."""
        return self._generic_call(argv)

    def listdir(self, argv):
        """listdir <path>
    Return a list of entries in the given directory."""
        if len(argv) == 1:
            argv.append(".") # default to dot
        return self._generic_call(argv)
    ls = listdir # alias

    def listfiles(self, argv):
        """listfiles <path>
    Return a list of entries in the given directory that are plain files."""
        if len(argv) == 1:
            argv.append(".") # default to dot
        return self._generic_call(argv)

    def chmod(self, argv):
        """chmod <path> <mode>
    Change the mode of the path to <mode>."""
        return self._generic_call(argv)

    def chown(self, argv):
        """chown <path> <uid> <gid>
    Change the owner of a file to uid, with group gid."""
        return self._generic_call(argv)

    def stat(self, argv):
        """stat <path>
    Return a stat tuple for the path."""
        stat = self._obj.stat(argv[1])
        self._print("Stats for %s:" % (argv[1],))
        self._print("      inode = %s" % (stat.st_ino,))
        self._print("       mode = %o" % (stat.st_mode,))
        self._print(" hard links = %s" % (stat.st_nlink,))
        self._print("    user id = %s" % (stat.st_uid,))
        self._print("   group id = %s" % (stat.st_gid,))
        self._print("       size = %s" % (stat.st_size,))
        self._print("     device = %s" % (stat.st_dev,))
        self._print("access time = %s" % (time.ctime(stat.st_atime),))
        self._print("   mod time = %s" % (time.ctime(stat.st_mtime),))
        self._print("change time = %s" % (time.ctime(stat.st_ctime),))
        return stat

    def statvfs(self, argv):
        """statvfs <path>
    Return a statvfs tuple for the path. That is, the information of the volume."""
        vfsstat = self._obj.statvfs(argv[1])
        self._print("Volume stats for %s:" % (argv[1],))
        self._print("               fragment size = %s" % (vfsstat.f_frsize,))
        self._print("                      blocks = %s" % (vfsstat.f_blocks,))
        self._print("                 blocks free = %s" % (vfsstat.f_bfree,))
        self._print(" blocks available (non-root) = %s" % (vfsstat.f_bavail,))
        self._print("          no. files (inodes) = %s" % (vfsstat.f_files,))
        self._print("                 free inodes = %s" % (vfsstat.f_ffree,))
        self._print("      free inodes (non-root) = %s" % (vfsstat.f_favail,))
        self._print("     maximum filename length = %s" % (vfsstat.f_namemax,))
        self._print("                 mount flags = %s" % (vfsstat.f_flag,))
        return vfsstat

    def open(self, argv):
        """open fname flags [mode=0777]
    Low-level file open. Returns file descriptor."""
        return self._generic_call(argv)

    def close(self, argv):
        """close <fd>
    Low-level file close. Requires valid file descriptor."""
        return self._generic_call(argv)

    def write(self, argv):
        """write fd, data
    Write to a file descriptor some data."""
        return self._generic_call(argv)

    def read(self, argv):
        """read fd n
    Low-level read from file descriptor. Read N bytes."""
        return self._generic_call(argv)

    def system(self, argv):
        """system <command>
    Run the <command> through the 'system' function."""
        es = self._obj.system(" ".join(argv[1:]))
        self._print(es)
        return es

    def pipe(self, argv):
        """pipe <command>
    Run a remote co-process connected by a pipe. """
        es, res = self._obj.pipe(" ".join(argv[1:]))
        self._print(res)
        return es

    def pyeval(self, argv):
        """pyeval <snippet>
    Evaluate some arbitrary Python code on the agent. """
        rv = self._obj.python(" ".join(argv[1:]))
        self._print(rv)
        return rv

    def pyexec(self, argv):
        """pyexec [<snippet>]
    Execute some arbitrary Python code on the agent. """
        text = " ".join(argv[1:])
        if not text:
            text = cliutils.get_text("py> ")
        if text:
            return self._obj.pyexec(text)

    def copyfile(self, argv):
        """copyfile <src> <dst>
    Copy data from src to dst on agent machine."""
        return self._generic_call(argv)

    def copymode(self, argv):
        """copymode <src> <dst>
    Copy mode bits from src to dst."""
        return self._generic_call(argv)

    def copystat(self, argv):
        """copystat <src> <dst>
    Copy all stat info (mode bits, atime and mtime) from src to dst."""
        return self._generic_call(argv)

    def copy(self, argv):
        """copy <src> <dst>
    Copy data and mode bits ("cp src dst").  The destination may be a directory."""
        return self._generic_call(argv)

    def copy2(self, argv):
        """copy2 <src> <dst>
    Copy data and all stat info ("cp -p src dst"). The destination may be a directory."""
        return self._generic_call(argv)

    def copytree(self, argv):
        """copytree <src> <dst> [symlinks=False]
    Recursively copy a directory tree using copy2()."""
        return self._generic_call(argv)

    def move(self, argv):
        """move <src> <dst>
    Recursively move a file or directory to another location. You might want to run 'run mv' instead..."""
        return self._generic_call(argv)

    def rmtree(self, argv):
        """rmtree <path>
    Recursively delete a directory tree."""
        return self._generic_call(argv)

    def ospath(self, argv):
        """ospath <method> <arguments>
    Generic caller for os.path methods.
    e.g. 'ospath exists filename' return True if filename exists."""
        return self._generic_call(argv[1:])

    def clean(self, argv):
        """clean
        Reset the Agent server. Closes all open files and kills open
        processes."""
        return self._generic_call(argv)

    def md5sums(self, argv):
        """md5sums <path>
    Reads the md5sums.txt file in the given path and reports the number checked
    and failed files."""
        good, bad, failed = self._obj.md5sums(argv[1])
        self._print("Checked %d files, %d passed and %d failed." % (good+bad, good, bad))
        if failed:
            self._print("The following failed the md5 check:")
            for fn in failed:
                self._print("  ", fn)
        return good

    def push_tarball(self, argv):
        """push_tarball [<url>]
    Cause the Client to download the given url."""
        if len(argv) > 1:
            url = argv[1]
        else:
            url = self._environ.tarballurl
            self._print("Pushing %r to client." % (url,))
        es = self._obj.get_tarball(url)
        if es:
            self._print("Push successful.")
        else:
            self._print("Push not successful.")
            self._print(str(es))

    def hostname(self, argv):
        """hostname
    Print the server's host name."""
        name =  self._obj.hostname()
        self._print(name)
        return name

    def script(self, argv):
        """script [-f <filename>] [<text>]
    Run a script on the server."""
        fname = None
        opts, longopts, args = self.getopt(argv, "f:")
        for opt, arg in opts:
            if opt == "-f":
                fname = arg
        if fname:
            text = open(fname).read()
            return self._runscript(text)
        else:
            text = " ".join(args)
            if text:
                return self._runscript(text)
            else:
                text = cliutils.get_text("script> ")
                if text:
                    return self._runscript(text)
                else:
                    self._print(self.script.__doc__)
                    return

    # helper for script
    def _runscript(self, text):
        sts, out = self._obj.run_script(text)
        if sts:
            self._print(out)
        else:
            self._print(str(sts))
        return sts

    def rcopy(self, argv):
        """rcopy <remotefile> <localfile>
    Copies a file from the remote agent to the local file system."""
        src = argv[1]
        dest = argv[2]
        Client.remote_copy(self._obj, src, dest)


class PosixRemoteCLI(RemoteCLI):
    """PosixServer specific method interface."""

    def export(self, argv):
        """export <"add"|"del"> <pathname>
    Adds or deletes the named export to/from the server."""
        cmd = argv[1]
        pathname = argv[2]
        if cmd == "add":
            try:
                export = self._obj.add_export(pathname)
            except:
                ex, val, tb = sys.exc_info()
                self._print("Could not add export: %s (%s)" % (ex,val))
            else:
                self._print("Export %r created." % (export,))
                return
        elif cmd == "del":
            es = self._obj.del_export(pathname)
            if es:
                self._print("Export removed.")
            else:
                self._print("Did not remove export: %s" % (es,))
            return
        else:
            explist = self._obj.list_export()
            self._print(explist)
            return

class WindowsRemoteCLI(RemoteCLI):
    """WindowsServer specific method interface."""

    def shortname(self, argv):
        """shortname <path>...
    Print the short file name for the given paths."""
        for path in argv[1:]:
            self._print(self._obj.get_short_pathname(path))

    # windows methods under cygwin
    def net_use(self, argv):
        """net_use drive share
    On Windows only, map <drive> to the <share>."""
        return self._generic_call(argv)

    def net_use_delete(self, argv):
        """net_use_delete drive
    On Windows, unmap a drive."""
        return self._generic_call(argv)

    def share(self, argv):
        """share <"add"|"del"> <pathname>
    Adds or deletes the named disk share on the server."""
        cmd = argv[1]
        pathname = argv[2]
        if cmd == "add":
            try:
                sharename = self._obj.add_share(pathname)
            except:
                ex, val, tb = sys.exc_info()
                self._print("Could not add share: %s (%s)" % (ex,val))
            else:
                self._print("Share %r created, served from %r." % (sharename, pathname))
                return
        elif cmd == "del":
            rv = self._obj.del_share(pathname)
            if rv:
                self._print("Share removed.")
            else:
                self._print("Did not remove share.")
            return
        else:
            self._print(self.share.__doc__)
            return

    def copyfile(self, argv):
        """copyfile <src> <dst>
    Copies a file from src path the dst path."""
        src = argv[1]
        dst = argv[2]
        rv = self._obj.CopyFile(src, dst)
        return rv

    def win32(self, argv):
        """win32 <funcname> args...
    Calls the win32api function named <funcname> with the supplied arguments and return the results."""
        funcname = argv[1]
        args, kwargs = CLI.breakout_args(argv[2:], vars(self._obj))
        rv = self._obj.win32(funcname, *args, **kwargs)
        return rv

    def attributes(self, argv):
        """attributes <"list"|"get"|"set"|"clear"> <fname> [flags...]
    Get or show the files attributes. The possible attribute names may also be listed."""
        cmd = argv[1]
        attrmap = self._obj.GetFileAttributeFlags()
        if cmd == "list":
            self._print("Possible attributes:")
            for attrname in attrmap.keys():
                self._print("  %s" % (attrname,))
            return
        fname = argv[2]
        flags = self._obj.GetFileAttributes(fname)
        if cmd == "get":
            self._print("Attributes for %s:" % (fname,))
            for name, flag in attrmap.items():
                if flag & flags:
                    self._print(name)
        elif cmd == "set":
            newflags = flags
            toset = map(str.upper, argv[3:]) # this mess allows for abbreviated flag names
            for attrname, attrvalue in attrmap.items():
                for setflag in toset:
                    if attrname.startswith(setflag):
                        newflags |= attrvalue
            return self._obj.SetFileAttributes(fname, newflags)
        elif cmd == "clear":
            newflags = flags
            toset = map(str.upper, argv[3:])
            for attrname, attrvalue in attrmap.items():
                for setflag in toset:
                    if attrname.startswith(setflag):
                        newflags &= ~attrvalue
            return self._obj.SetFileAttributes(fname, newflags)
        else:
            self._print(self.attributes.__doc__)
            return


class TopLevelCLI(CLI.BaseCommands):
    def initialize(self):
        self._objs = {}
        Pyro.core.initClient(banner=0)
        self._rescan()

    def _rescan(self):
        locator = Pyro.naming.NameServerLocator()
        ns = locator.getNS()
        for name, isobject in ns.list("Agents"):
            if isobject:
                self._objs[name] = True
        agents = list(self._objs.keys())
        self.add_completion_scope("use", agents)
        self.add_completion_scope("ping", agents)
        self.add_completion_scope("whatis", agents)

    def finalize(self):
        self._objs = {}

    def except_hook(self, ex, val, tb):
        self._print(ex, val)

    def rescan(self, argv):
        """rescan
    Rescan for available remote clients."""
        self._rescan()
        self.ls(argv)

    def ls(self, argv):
        """ls
    Print available clients."""
        self._print("Currently available agents:")
        for name in self._objs:
            self._print("  %s" % (name,))
    dir = ls # alias

    def get_remote(self, name):
        return Client.get_remote(name)

    def use(self, argv):
        """use <name>
    Use the specified agent. """
        name = argv[1]
        clnt = self.get_remote(name)
        try:
            clnt.alive()
        except Pyro.errors.ConnectionClosedError:
            del self._objs[name]
            self._print("Remote agent has disconnected.")
            return
        cliclass = CLIManager.get(clnt)
        if cliclass is not None:
            cmd = self.clone(cliclass)
            cmd._setup(clnt, name)
            raise CLI.NewCommand, cmd
        else:
            self._ui.error("No CLI found for that agent!")

    def whatis(self, argv):
        """whatis <name>
    Tell what type of agent corresponds to the name."""
        name = argv[1]
        clnt = self.get_remote(name)
        try:
            clnt.alive()
        except Pyro.errors.ConnectionClosedError:
            del self._objs[name]
            self._print("Remote agent has disconnected.")
            return
        self._print(clnt.whatami())

    def ping(self, argv):
        """ping <name>
    Checks that the named server is alive."""
        host = argv[1]
        clnt = self.get_remote(name)
        try:
            if clnt.alive():
                self._print("%s is alive." % (host,))
            else:
                self._print("%s is NOT alive!" % (host,))
        except:
            ex, val, tb = sys.exc_info()
            self._print("Problem with client!")
            self._print(ex, "\r", val)


class CLIManager(object):
    """Manage a collection of CLI wrappers. 

    Maps agent implementation names to specific CLI wrappers.
    """
    _CLI = {}

    @classmethod
    def register(cls, agentname, cliclass):
        assert issubclass(cliclass, CLI.BaseCommands)
        cls._CLI[agentname] = cliclass

    @classmethod
    def remove(cls, agentname):
        try:
            del cls._CLI[agentname]
        except KeyError:
            pass

    @classmethod
    def get(cls, clnt):
        try:
            agenttype = clnt.whatami()
        except AttributeError: # old agent, possibly
            pass
        else:
            try:
                return cls._CLI[agenttype]
            except KeyError: # use defaults if no specific cli wrapper found.
                pass 
        # default to platform generic CLI
        plat = clnt.platform()
        if plat == "win32":
            return WindowsRemoteCLI
        elif plat in ("linux2", "cygwin"):
            return PosixRemoteCLI
        else:
            return None


CLIManager.register("PosixAgent", PosixRemoteCLI)
CLIManager.register("Win32Agent", WindowsRemoteCLI)


def remotecli(argv):
    """remotecli [-h|-?] [-g] [-s <script>]

Provides an interactive session to a remote agent object. Most of the
methods in the module remote.??????Server may be invoked with this tool.

"""
    from pycopia import getopt
    from pycopia.QA import config

    paged = False
    script = None
    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "s:?hg")
    except getopt.GetoptError:
            print remotecli.__doc__
            return
    for opt, val in optlist:
        if opt == "-?" or opt == "-h":
            print remotecli.__doc__
            return
        elif opt == "-g":
            paged = True
        elif opt == "-s":
            script = val

    # do runtime setup
    cf = config.get_config(initdict=longopts)
    # fake test module attributes
    cf.reportfile = "remotecli"
    cf.logbasename = "remotecli.log"
    cf.arguments = argv

    theme = UI.DefaultTheme(PROMPT)
    history=os.path.expandvars("$HOME/.hist_remotecli")
    parser = CLI.get_cli(TopLevelCLI, env=cf, paged=paged, theme=theme, historyfile=history)

    if script:
        try:
            parser.parse(script)
        except KeyboardInterrupt:
            pass
    else:
        parser.interact()


if __name__ == "__main__":
    remotecli(sys.argv)

