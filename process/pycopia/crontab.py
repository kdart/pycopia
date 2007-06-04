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
Interface to crontab. You can read, add, change, and submit crontab files
to the cron system.

"""


import sys, os
import re
from cStringIO import  StringIO
from pycopia import proctools

DOW = {
    0: "Sun",
    1: "Mon",
    2: "Tue",
    3: "Wed",
    4: "Thu",
    5: "Fri",
    6: "Sat",
    7: "Sun"
}
#DOW_REV = dict([(t[1], t[0]) for t in DOW.iteritems()])

MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}
#MONTHS_REV = dict([(t[1], t[0]) for t in MONTHS.iteritems()])

class Comment(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return "# %s" % (self.text,)

    def match(self, pattern):
        if re.match(pattern, self.text):
            return True
        return False


class Variable(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return '%s=%r' % (self.name, self.value)

    def match(self, value=None, name=None):
        nv = vv = False
        if value:
            if re.search(value, self.value):
                vv = True
            else:
                vv = False
        if name:
            if re.search(name, self.name):
                nv = True
            else:
                nv = False
        # Name and value expressions must match if both given.
        if name and value: 
            return nv and vv
        # If only name expression given, return match for it.
        if name and not value:
            return nv
        # If only value expression given, return match for it.
        if not name and value:
            return vv
        # If no expression given it's always false.
        if not name and not value:
            return False


class BlankLine(object):
    def __str__(self):
        return ""

    def match(self, pattern=None):
        return False


# Crontab fields:
#              field          allowed values
#              -----          --------------
#              minute         0-59
#              hour           0-23
#              day of month   1-31
#              month          1-12 (or names, see below)
#              day of week    0-7 (0 or 7 is Sun, or use names)

class CrontabLine(object):
    def __init__(self, cmd, minute=None, hour=None, day_of_month=None,
                  month=None, day_of_week=None):
        self.minute = Minutes(minute)
        self.hour = Hours(hour)
        self.day_of_month = DayOfMonth(day_of_month)
        self.month = Month(month)
        self.day_of_week = DayOfWeek(day_of_week)
        self.command = cmd

    def __str__(self):
        return "%s %s %s %s %s %s" % (
            self.minute,
            self.hour,
            self.day_of_month,
            self.month,
            self.day_of_week,
            self.command)

    def match(self, command=None, minute=None, hour=None, day_of_month=None,
                  month=None, day_of_week=None):
        if command:
            if re.search(command, self.command) is None:
                return False
        for attr, check in ((self.minute, minute), (self.hour, hour), 
                            (self.day_of_month, day_of_month), 
                            (self.month, month), (self.day_of_week, day_of_week)):
            if check is not None:
                checker = attr.new(check)
                if checker != attr:
                    return False
        return True


class Selection(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end


class CrontabFile(object):
    """Represents a user crontab file. You can edit it with the editing
    methods. It also has list-like methods.
    """
    BLANK_RE = re.compile(r"^\s*$")
    VARIABLE_RE = re.compile(r"^(\w+)\s*=\s*['\"]*([^'\"]+)['\"]*$")
    COMMENT_RE = re.compile(r"^\s*#(.*)$")

    def __init__(self, text=None, filename=None, username=None):
        self.filename = filename
        self.username = username
        if text:
            self._lines = self.parse(text)
        else:
            self._lines = []

    def __str__(self):
        return "\n".join(map(str, self._lines))+"\n"

    def __getitem__(self, index):
        return self._lines[index]

    def __setitem__(self, index, value):
        self._lines[index] = value

    def __delitem__(self, index):
        del self._lines[index]

    def __iter__(self):
        return iter(self._lines)

    def parse(self, text):
        lines = []
        for line in text.splitlines():
            if line.startswith("no crontab"):
                continue

            mo = CrontabFile.COMMENT_RE.match(line)
            if mo:
                lines.append(Comment(mo.group(1).strip()))
                continue

            mo = CrontabFile.VARIABLE_RE.match(line)
            if mo:
                lines.append(Variable(mo.group(1), mo.group(2)))
                continue

            mo = CrontabFile.BLANK_RE.match(line)
            if mo:
                lines.append(BlankLine())
                continue
            # crontabline
            try:
                [minute, hour, dom, month, dow, cmd] = line.split(None, 5)
            except ValueError: # some strange line, ignore it.
                pass
            else:
                lines.append(CrontabLine(cmd, minute, hour, dom, month, dow))
        return lines

    def add_comment(self, text, lineno=None):
        cmnt = Comment(text)
        if lineno is None:
            self._lines.append(cmnt)
        else:
            self._lines.insert(lineno, cmnt)

    def add_variable(self, name, value, lineno=None):
        var = Variable(name, value)
        if lineno is None:
            self._lines.append(var)
        else:
            self._lines.insert(lineno, var)

    def add_blank(self, lineno=None):
        if lineno is None:
            self._lines.append(BlankLine())
        else:
            self._lines.insert(lineno, BlankLine())

    def add_crontab(self, cmd, minute=None, hour=None, day_of_month=None,
                   month=None, dow=None, lineno=None):
        ctl = CrontabLine(cmd, minute, hour, day_of_month, month, dow)
        if lineno is None:
            self._lines.append(ctl)
        else:
            self._lines.insert(lineno, ctl)

    def add_event(self, ical):
        """Add and event from a iCal entry object. The body of the entry is the
        command-line to run.
        """
        raise NotImplementedError

    def append(self, obj, lineno=None):
        """Append any crontab object.  """
        if isinstance(obj, (CrontabLine, BlankLine, Variable, Comment)):
            if lineno is None:
                self._lines.append(obj)
            else:
                self._lines.insert(lineno, obj)
        else:
            raise ValueError("You may only add crontab objects.")

    def insert(self, lineno, obj):
        self.append(obj, lineno)

    def extend(self, objlist):
        for obj in objlist:
            self.append(obj)

    def _find(self, start, end, **kwargs):
        for entry in self._lines[start:end]:
            if entry.match(**kwargs):
                return entry
        return None # no match

    def _find_i(self, start, end, cttype, **kwargs):
        for i, entry in enumerate(self._lines[start:end]):
            if type(entry) is cttype and entry.match(**kwargs):
                return i+start
        return -1 # no match

    def find(self, pattern, start=0, end=-1):
        """Return a crontab line matching the given pattern.
        """
        return self._find(start, end, command=pattern)

    def find_variable(self, namepattern=None, valuepattern=None, start=0):
        for i, obj in enumerate(self._lines[start:]):
            if type(obj) is Variable:
                if obj.match(valuepattern, namepattern):
                    return i, obj
        return -1, None # not found

    def find_crontab(self, command=None, minute=None, hour=None, day_of_month=None,
                  month=None, day_of_week=None, start=0):
        for i, obj in enumerate(self._lines[start:]):
            if type(obj) is CrontabLine:
                if obj.match(command=command, minute=minute, hour=hour, 
                        day_of_month=day_of_month, month=month, 
                        day_of_week=day_of_week):
                    return i, obj
        return -1, None

    def find_comment(self, pattern, start=0):
        for i, obj in enumerate(self._lines[start:]):
            if type(obj) is Comment:
                if obj.match(pattern):
                    return i, obj
        return -1, None

    def findall(self, pattern, start=0, end=None):
        rv = []
        for entry in self._lines[start:end]:
            if entry.match(pattern):
                rv.append(entry)
        return rv

    def select(self, start, end):
        """Select a range of the crontab lines.
        """
        if not isinstance(start, int):
            start = self._find_i(0, -1, CrontabLine, command=start)
        if not isinstance(end, int):
            if end == "$":
                end = len(self._lines)
            end = self._find_i(start, -1, CrontabLine, command=end)
        return Selection(start, end)

    def replace(self, selection, cronobjects):
        """Replace a line matching pattern with a new CrontabLine object.
        """
        self._lines[selection.start:selection.end] = cronobjects

    def delete(self, start, end):
        del self._lines[start:end]

    def delete_crontab(self, **kwargs):
        """Delete the CrontabLine matching pattern.  """
        i, line = self.find_crontab(**kwargs)
        if line:
            del self._lines[i]
        return i

    def delete_all_crontab(self, **kwargs):
        pos = kwargs.get("start", 0)
        while pos >= 0:
            pos = self.delete_crontab(**kwargs)

    def delete_variable(self, **kwargs):
        """Delete the variable matching pattern.
        """
        i, line = self.find_variable(**kwargs)
        if line:
            del self._lines[i]
        return i

    def replace_variable(self, name, value):
        i, line = self.find_variable(namepattern=name)
        if line:
            del self._lines[i]
        var = Variable(name, value)
        self._lines.insert(i, var)

    def delete_comment(self, **kwargs):
        """Delete the variable matching pattern.
        """
        i, line = self.find_comment(**kwargs)
        if line:
            del self._lines[i]
        return i

    def write(self, filename=None):
        name = filename or self.filename
        if name:
            fo = open(name, "w")
            try:
                fo.write(str(self))
            finally:
                fo.close()
        else:
            submit(self)

    def submit(self, username=None):
        username = username or self.username
        return submit(self, username=username)


def make_crontab(self, filename=None):
    return CrontabFile(name=filename)


# Get the crontab file from a file, or the active crontab from the crontab
# command.
def open(filename=None, username=None):
    if filename is None:
        cmd = "crontab -l"
        if username:
            cmd += " -u %s" % (username,)
        ct = proctools.spawnpipe(cmd)
        text = ct.read()
        ct.close()
    else:
        text = open(filename).read()
    return CrontabFile(text, filename, username)


def submit(crontab, username=None, password=None):
    """Submit a crontab via the crontab program. 
    Supply a crontab object. If it is to be installed for a different user
    supply the `username` parameter. If this is not run as root, then sudo is
    used and you must supply your own password for sudo."""
    if username is None:
        ct = proctools.spawnpipe("crontab -")
        ct.write(str(crontab))
        ct.close()
        return ct.wait()
    else:
        if os.getuid() == 0:
            ct = proctools.spawnpipe("crontab -u %s -" % (username,))
            ct.write(str(crontab))
            ct.close()
            return ct.wait()
        else:
            from pycopia import sudo
            if password is None:
                from pycopia import tty
                password = tty.getpass("Your password:")
            ct = sudo.sudo("crontab -u %s -" % (username,), password=password)
            ct.write(str(crontab))
            ct.close()
            return ct.wait()


# A useful integer set class ripped from the mhlib module. Thanks!

class IntSet(object):
    """Class implementing sets of integers.

    This is an efficient representation for sets consisting of several
    continuous ranges, e.g. 1-100,200-400,402-1000 is represented
    internally as a list of three pairs: [(1,100), (200,400),
    (402,1000)].  The internal representation is always kept normalized.

    The constructor has up to three arguments:
    - the string used to initialize the set (default ''),
    - the separator between ranges (default ',')
    - the separator between begin and end of a range (default '-')
    The separators must be strings (not regexprs) and should be different.

    """
    MIN = 0
    MAX = sys.maxint
    def __init__(self,data=None, sep = ',', rng='-'):
        self.pairs = []
        self.sep = sep
        self.rng = rng
        if data: 
            self.parse(str(data))
        else:
            self.pairs.append((self.MIN, self.MAX))

    def reset(self):
        self.pairs = []

    def __hash__(self):
        return hash(self.pairs)

    def __eq__(self, other):
        return self.pairs == other.pairs

    def __ne__(self, other):
        return self.pairs != other.pairs

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__, 
                                           self.__str__(), self.sep, self.rng)
    def __str__(self):
        if (len(self.pairs) == 1
                and self.pairs[0][0] == self.MIN 
                and self.pairs[0][1] == self.MAX):
            return "*"
        s = ''
        for lo, hi in self.pairs:
            if lo == hi: 
                t = repr(lo)
            else: 
                t = repr(lo) + self.rng + repr(hi)
            if s: 
                s += (self.sep + t)
            else: 
                s = t
        return s

    def normalize(self):
        self.pairs.sort()
        i = 1
        while i < len(self.pairs):
            alo, ahi = self.pairs[i-1]
            blo, bhi = self.pairs[i]
            if ahi >= blo-1:
                self.pairs[i-1:i+1] = [(alo, max(ahi, bhi))]
            else:
                i = i+1

    def tolist(self):
        l = []
        for lo, hi in self.pairs:
            m = range(lo, hi+1)
            l.extend(m)
        return l

    def fromlist(self, list):
        for i in list:
            self.append(i)

    def copy(self):
        new = self.__class__(sep=self.sep, rng=self.rng)
        new.pairs = self.pairs[:]
        return new

    def new(self, data=None, sep=None, rng=None):
        return self.__class__(data, sep or self.sep, rng or self.rng)

    def min(self):
        return self.pairs[0][0]

    def max(self):
        return self.pairs[-1][-1]

    def contains(self, x):
        for lo, hi in self.pairs:
            if lo <= x <= hi: 
                return True
        return False
    __contains__ = contains

    def append(self, x):
        for i in range(len(self.pairs)):
            lo, hi = self.pairs[i]
            if x < lo: # Need to insert before
                if x+1 == lo:
                    self.pairs[i] = (x, hi)
                else:
                    self.pairs.insert(i, (x, x))
                if i > 0 and x-1 == self.pairs[i-1][1]:
                    # Merge with previous
                    self.pairs[i-1:i+1] = [
                            (self.pairs[i-1][0],
                             self.pairs[i][1])
                          ]
                return
            if x <= hi: # Already in set
                return
        i = len(self.pairs) - 1
        if i >= 0:
            lo, hi = self.pairs[i]
            if x-1 == hi:
                self.pairs[i] = lo, x
                return
        self.pairs.append((x, x))

    def addpair(self, xlo, xhi):
        if xlo > xhi: 
            return
        self.pairs.append((xlo, xhi))
        self.normalize()

    def parse(self, data):
        new = []
        for part in data.split(self.sep):
            if part == "*":
                new.append((self.MIN, self.MAX))
                break
            tmplist = []
            for subp in part.split(self.rng):
                s = subp.strip()
                tmplist.append(int(s))
            if len(tmplist) == 1:
                new.append((tmplist[0], tmplist[0]))
            elif len(tmplist) == 2 and tmplist[0] <= tmplist[1]:
                new.append((tmplist[0], tmplist[1]))
            else:
                raise ValueError("Unable to parse: %r" % (data,))
        self.pairs.extend(new)
        self.normalize()


class Minutes(IntSet):
    MIN=0
    MAX=59


class Hours(IntSet):
    MIN=0
    MAX=23


class DayOfMonth(IntSet):
    MIN=1
    MAX=31


class Month(IntSet):
    MIN=1
    MAX=12


class DayOfWeek(IntSet):
    MIN=0
    MAX=7


