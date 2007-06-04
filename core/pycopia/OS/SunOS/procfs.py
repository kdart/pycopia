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
Procfs for SunOS.

"""

import os
import struct

from pycopia.aid import sortedlist

# from man -s 4 proc
#     typedef struct psinfo {
#          int pr_flag;              /* process flags */
#          int pr_nlwp;              /* number of lwps in the process */
#          pid_t pr_pid;             /* process id */
#          pid_t pr_ppid;            /* process id of parent */
#          pid_t pr_pgid;            /* process id of process group leader */
#          pid_t pr_sid;             /* session id */
#          uid_t pr_uid;             /* real user id */
#          uid_t pr_euid;            /* effective user id */
#          gid_t pr_gid;             /* real group id */
#          gid_t pr_egid;            /* effective group id */
#          uintptr_t pr_addr;        /* address of process */
#          size_t pr_size;           /* size of process image in Kbytes */
#          size_t pr_rssize;         /* resident set size in Kbytes */
#          dev_t pr_ttydev;          /* controlling tty device (or PRNODEV) */
#          ushort_t pr_pctcpu;       /* % of recent cpu time used by all lwps */
#          ushort_t pr_pctmem;       /* % of system memory used by process */
#          timestruc_t pr_start;     /* process start time, from the epoch */
#          timestruc_t pr_time;      /* cpu time for this process */
#          timestruc_t pr_ctime;     /* cpu time for reaped children */
#          taskid_t pr_taskid;       /* task id */
#          projid_t pr_projid;       /* project id */
#          char pr_fname[PRFNSZ];    /* name of exec'ed file */
#          char pr_psargs[PRARGSZ];  /* initial characters of arg list */
#          int pr_wstat;             /* if zombie, the wait() status */
#          int pr_argc;              /* initial argument count */
#          uintptr_t pr_argv;        /* address of initial argument vector */
#          uintptr_t pr_envp;        /* address of initial environment vector */
#          char pr_dmodel;           /* data model of the process */
#          lwpsinfo_t pr_lwp;        /* information for representative lwp */
#     } psinfo_t;



class ProcStat(object):
    """Status information about a process. """
    _FF = "/proc/%d/psinfo"
    _STATINDEX = {
    "command": 0,
    "pid": 1,
    "ppid": 2,
    "pgid": 3,
    "sid": 4,
    "ctty": 5,
    "flags": 6,
    "start": 7,
    "ut": 8,
    "st": 9,
    "wchan": 10,
    "euid": 11,
    "ruid": 12,
    "groups": 13,
    }

    def __init__(self, pid=None):
        self.pid = None
        self.read(pid)

    # so sorting works
    def __lt__(self, other):
        return self.pid < other.pid

    def __gt__(self, other):
        return self.pid > other.pid

    def __eq__(self, other):
        return self.pid == other.pid

    def _toint(self, it):
        try:
            return int(it)
        except ValueError:
            return it

    def reread(self):
        self.read(self.pid)
        return self

    def read(self, pid=None):
        if pid is not None:
            self.pid = int(pid)
        if self.pid is not None:
            try:
                self.stats = self._get_psinfo(pid)
            except IOError: # no such process
                self.pid = None
                self.stats = None
        else:
            self.stats = None
        return self

    def _get_psinfo(self, pid):
        return None # XXX

    def statestr(self):
        return NotImplemented

    def RSS(self):
        return NotImplemented

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.pid)

    def __str__(self):
        if self.stats is None:
            return "no stats - invalid pid?"
        else:
            s = ["%15s: %s" % ("cmdline", self.get_cmdline())]
            names = self._STATINDEX.keys()
            names.sort()
            #for name, i in self._STATINDEX.items():
            for name in names:
                i = self._STATINDEX[name]
                s.append("%15s: %s" % (name, self.stats[i]))
            return "\n".join(s)

    def get_attributes(self):
        return NotImplemented

    def get_cmdline(self):
        return NotImplemented
    cmdline = property(get_cmdline, None, None, "Command line")

#   ttyname = property(_get_ttyname, None, None, None)

    def get_stat(self, name):
        if not self.stats:
            raise ValueError, "no stats - run read(pid)"
        try:
            return self.stats[self._STATINDEX[name]]
        except KeyError:
            raise ValueError, "no attribute %s" % name

    def __getattr__(self, name):
        try:
            return self.get_stat(name)
        except ValueError, err:
            raise AttributeError, err

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError, err:
            raise KeyError, err


class ProcStatTable(object):
    """ProcStatTable()
A collection of all processes running, like the standard 'ps' command. """
    def __init__(self, fmt="%(pid)6s %(ppid)6s %(ttyname)6.6s %(cmdline).55s"):
        self.fmt = fmt
        self._ptable = None

    def read(self):
        rv = self._ptable = {}
        for pfile in os.listdir("/proc"):
            try:
                pid = int(pfile) # filter out non-numeric entries in /proc
            except ValueError:
                continue
            rv[pid] = ProcStat(pid)

    def __len__(self):
        return len(self._ptable)

    def __getitem__(self, pid):
        return self._ptable[pid]

    def __iter__(self):
        return self._ptable.itervalues()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.fmt)

    def __str__(self):
        self.read()
        s = []
        k = self._ptable.keys()
        k.sort()
        for pid in k:
            s.append(self.fmt % self._ptable[pid])
        return "\n".join(s)

    # this is here because $#%@# FreeBSD ps can't print a tree of procs (a
    # helpful debugging aid)
    def tree(self):
        class _pholder:
            pass
        self.read()
        if not self._ptable.has_key(0):
            p0 = self._ptable[0] = _pholder()
            p0.pid = p0.ppid = 0
            p0.cmdline = "<kernel>"
        for p in self._ptable.values():
            try: 
                self._ptable[p.ppid]._children.append(p.pid)
            except AttributeError: # no child list yet
                self._ptable[p.ppid]._children = sortedlist([p.pid])

        pslist = self._tree_helper(self._ptable[0], 0, [])
        return "\n".join(pslist)

    # recursive helper to indent according to child depth
    def _tree_helper(self, obj, level, rv):
        rv.append("%s%6d %.60s" % ("  "*level, obj.pid, obj.cmdline) )
        if not hasattr(obj, "_children"):
            return rv
        for cpid in obj._children:
            if cpid != obj.pid:
                self._tree_helper(self._ptable[cpid], level+1, rv)
        return rv


def _test(argv):
    pass # XXX

if __name__ == "__main__":
    import sys
    _test(sys.argv)

