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
Procfs for Win32. Simulates a proc fs for Win32 Python. 

"""

import os

from pycopia.aid import sortedlist

class ProcStat(object):
    """Status information about a process. """
    _STATINDEX = {
    "command": 0,
    "pid": 1,
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
            self.stats = [] # XXX get proc stats from win32 calls...
        else:
            self.stats = None
        return self

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
            s = ["%15s: %s" % ("cmdline", self.get_cmdline())]
            names = self._STATINDEX.keys()
            names.sort()
            for name in names:
                i = self._STATINDEX[name]
                s.append("%15s: %s" % (name, self.stats[i]))
            return "\n".join(s)

    def get_attributes(self):
        return self._STATINDEX.keys()

    def get_cmdline(self):
        return "<not implemented>"

    cmdline = property(get_cmdline, None, None, "Command line")

    def _get_ttyname_win32(self):
        return "?"

    ttyname = property(_get_ttyname_win32, None, None, None)

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

    def _pidlist(self):
        return [] # XXX use enum procs...

    def read(self):
        rv = self._ptable = {}
        for pid in self._pidlist():
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
        self.read()
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

