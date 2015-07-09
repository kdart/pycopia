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

