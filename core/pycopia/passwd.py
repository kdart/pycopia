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
User objects from passwd entries. Funtionally enchanced PWEntry object is
better than the pwd_passwd structure, and is pickle-able as well.

"""

import pwd
import grp
import os

class PWEntry(object):
    def __init__(self, _ut):
        self.name = _ut[0]
        self.passwd = _ut[1]
        self.uid = _ut[2]
        self.gid = _ut[3]
        self.group = _ut[3] # alias
        self.gecos = _ut[4]
        self.fullname = _ut[4]  # alias
        self.home = _ut[5]
        self.shell = _ut[6]
        self._INDEX = {0:self.name, 1:self.passwd, 2:self.uid, 3:self.gid, 
                       4:self.gecos, 5:self.home, 6:self.shell}
        self._groups = None

    def __repr__(self):
        return "%s:%s:%s:%s:%s:%s:%s" % (self.name, self.passwd, 
                     self.uid, self.gid, self.gecos, self.home, self.shell)

    def __str__(self):
        return self.name

    def __int__(self):
        return self.uid

    # pwd compatibility - sequence interface
    def __getitem__(self, idx):
        return self._INDEX[idx]

    groupname = property(lambda self: grp.getgrgid(self.gid)[0], 
               doc="Primary group name.")

    def _get_groups(self):
        grplist = []
        if self._groups is None:
            # Is there a better/faster way than this?
            name = self.name
            for gent in grp.getgrall():
                if name in gent.gr_mem:
                    grplist.append(gent.gr_gid)
            self._groups = grplist
        return self._groups

    groups = property(_get_groups)

def getpwuid(uid):
    return PWEntry(pwd.getpwuid(uid))

def getpwnam(name):
    return PWEntry(pwd.getpwnam(name))

def getpwall():
    rv = []
    for pw in pwd.getpwall():
        rv.append(PWEntry(pw))
    return rv

def getpwself():
    return PWEntry(pwd.getpwuid(os.getuid()))

