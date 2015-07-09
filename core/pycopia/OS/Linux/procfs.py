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
Access to /proc/PID file system information.

"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
from signal import SIGTERM

from pycopia import textutils
from pycopia.aid import sortedlist

_CMDTRANS = textutils.maketrans("\0\n", "  ")

class ProcStat(object):
    """Status information about a process. """
    # Linux 2.4 /proc/PID/stat format
    _STATINDEX = {
    "pid": 0,
    "command": 1,
    "state":  2,
    "ppid":  3,
    "pgrp":  4,
    "session": 5,
    "tty_nr":  6,
    "tty_pgrp":  7,
    "flags":  8,
    "min_flt":  9,
    "cmin_flt": 10,
    "maj_flt": 11,
    "cmaj_flt": 12,
    "tms_utime": 13,
    "tms_stime": 14,
    "tms_cutime": 15,
    "tms_cstime":16,
    "priority": 17,
    "nice": 18,
    #"_removed": 19,
    "it_real_value": 20,
    "start_time": 21,
    "vsize": 22,
    "rss": 23,  # you might want to shift this left 3
    "rlim_cur": 24,
    "mm_start_code": 25,
    "mm_end_code": 26,
    "mm_start_stack": 27,
    "esp": 28,
    "eip": 29,
    "sig_pending": 30, # these are depricated, don't use
    "sig_blocked": 31,
    "sig_ignore": 32,
    "sig_catch": 33,
    "wchan": 34,
    "nswap": 35,
    "cnswap": 36,
    "exit_signal": 37,
    "processor": 38,
    }
    #   "RSDZTW"
    _STATSTR = {
    "R": "running",
    "S": "sleeping",
    "D": "uninterruptible disk sleep",
    "Z": "zombie/defunct",
    "T": "traced/stopped",
    "W": "paging"
    }
    _FF = "/proc/%d/stat"

    def __init__(self, pid=None):
        self.stats = None
        self.cmdline = None
        self.pid = None
        self.ttyname = None
        self.environment = None
        self.read(pid)

    def __getstate__(self):
        return (self.pid, self.stats, self.cmdline, self.ttyname)

    def __setstate__(self, t):
        self.pid, self.stats, self.cmdline, self.ttyname = t

    # so sorting works
    def __lt__(self, other):
        return self.pid < other.pid

    def __gt__(self, other):
        return self.pid > other.pid

    def __eq__(self, other):
        return self.pid == other.pid

    def __nonzero__(self):
        return bool(self.stats)
    __bool__ = __nonzero__

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
                self.stats = tuple(map(self._toint, open(self._FF % (self.pid)).read().split()))
                self.cmdline = self.get_cmdline()
                self.environment = self.get_environment()
                self.uid, self.gid = self._get_uid()
                self.ttyname = self._get_ttyname_linux()
            except IOError: # no such process
                self.stats = None
                self.cmdline = None
                self.ttyname = None
        else:
            self.stats = None
        return self

    def load(self, statstring):
        self.stats = tuple(map(self._toint, statstring.split()))
        self.pid = None
        self.cmdline = None
        self.ttyname = None
        self.uid = None
        self.gid = None

    def statestr(self):
        try:
            return self._STATSTR[self.stats[self._STATINDEX["state"]]]
        except:
            return "?"

    def RSS(self):
        try:
            return self.stats[self._STATINDEX["rss"]] << 3
        except:
            return 0

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.pid)

    def __str__(self):
        if self.stats is None:
            return "no stats - invalid pid?"
        else:
            s = ["%15s: %s" % ("cmdline", self.cmdline)]
            names = self._STATINDEX.keys()
            names.sort()
            for name in names:
                i = self._STATINDEX[name]
                s.append("%15s: %s" % (name, self.stats[i]))
            return "\n".join(s)

    def __iter__(self):
        if self.stats is None:
            return
        yield ("cmdline", self.cmdline)
        for name in self._STATINDEX.keys():
            i = self._STATINDEX[name]
            yield (name, self.stats[i])

    def get_attributes(self):
        return self._STATINDEX.keys()

    def get_cmdline(self):
        try:
            cmd = open("/proc/%d/cmdline" % (self.pid,)).read()
        except IOError as err:
            self.pid = None
            return "<unknown>"
        cmd = cmd.translate(_CMDTRANS).strip()
        if not cmd:
            return self.command
        else:
            return cmd

    def get_environment(self):
        env = {}
        rawenv = open("/proc/%d/environ" % (self.pid,)).read()
        for line in rawenv.split("\0"):
            if line:
                name, value = line.split("=", 1)
                env[name] = value
        return env

    def _get_ttyname_linux(self):
        tty_nr = self["tty_nr"]
        if tty_nr:
            try:
                name = os.readlink("/proc/%d/fd/0" % (self.pid))
            except OSError:
                minor = tty_nr & 0xff
                major = (tty_nr >> 8) & 0xff
                return "%d,%d" % (major, minor) # XXX
            else:
                return name[5:] # chop /dev
        else:
            return "?"

    def _get_uid(self):
        try:
            statuslines = open("/proc/%d/status" % (self.pid,)).readlines()
        except IOError as err:
            return 0, 0
        uid = 0
        gid = 0
        for line in statuslines:
            if line.startswith("Uid"):
                uid = int(line[5:].split()[0])
            elif line.startswith("Gid"):
                gid = int(line[5:].split()[0])
        return uid, gid

    def get_stat(self, name):
        if not self.stats:
            raise ValueError("no stats - run read(pid)")
        try:
            val =  self.stats[self._STATINDEX[name]]
        except KeyError:
            raise ValueError("no attribute %s" % name)
        # ugly hack to work around Linux having "(,)" around command name
        if name == "command":
            return val[1:-1]
        else:
            return val

    def __getattr__(self, name):
        try:
            return self.get_stat(name)
        except ValueError as err:
            raise AttributeError(err)

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as err:
            raise KeyError(err)


class CPUMeasurer(object):
    """Helper to measure CPU utilization of a process."""
    def __init__(self, pid=None):
        self._ps = ProcStat(pid)

    def start(self, timestamp, statstring=None):
        ps = self._ps
        self._starttime = timestamp
        if statstring:
            ps.load(statstring)
        else:
            ps.reread()
        self._start_tics = ps.tms_stime + ps.tms_utime

    def end(self, timestamp, statstring=None):
        ps = self._ps
        if statstring:
            ps.load(statstring)
        else:
            ps.reread()
        end_tics = ps.tms_stime + ps.tms_utime
        return float(end_tics - self._start_tics) / (timestamp - self._starttime)



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


##### useful shell-command-like functions.

def pidof(procname):
    """pidof(procname) Returns a list of PIDs (integers) that match the given process name."""
    rv = []
    ps = ProcStat() # use the ProcStat object as a parser.
    for pfile in os.listdir("/proc"):
        try:
            pid = int(pfile) # also filters out non-numeric entries in /proc
        except ValueError:
            continue
        ps.read(pid)
        if ps.command == procname:
            rv.append(ps.pid)
    return rv

def ps(argv=None):
    if not argv:
        t = ProcStatTable()
        t.read()
        print (t)
    else:
        for spid in argv:
            try:
                pid = int(spid)
            except:
                continue
            print()
            print (ProcStat(pid))

def pstree():
    t = ProcStatTable()
    print (t.tree())

def killall(procname, sig=SIGTERM):
    """killall(procname, [signal]) Sends a signal (default SIGTERM) to all processes that match the given name."""
    for pid in pidof(procname):
        os.kill(pid, sig)

def _test(argv):
    #ps()
    import time
    measurer = CPUMeasurer(os.getpid())
    measurer.start(time.time())
    for x in range(10000000):
        x = x*2
    time.sleep(1)
    print (measurer.end(time.time()))

if __name__ == "__main__":
    import sys
    _test(sys.argv)

