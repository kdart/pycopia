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
A client module to the bugzilla email interface.

"""


import ezmail

# keyword names mapping to mandatory flag
KEYWORDS = {
    "product":1,
    "component":1,
    "version":1,
    "short_desc":1,
    "rep_platform":0,
    "bug_severity":0,
    "priority":0,
    "op_sys":0,
    "assigned_to":0,
    "bug_file_loc":0,
    "status_whiteboard":0,
    "target_milestone":0,
    "groupset":0,
    "qa_contact":0,
}

SEVERITY_VALUES = [ "blocker", "critical", "major", "normal", 
        "minor", "trivial", "enhancement" ]

PRIORITY_VALUES = ["P1", "P2", "P3", "P4", "P5" ]

class BugzillaMessage(ezemail.AutoMessage):
    pass

class BugzillaBody(object):
    def __init__(self, **kwargs):
        self._keywords = {}
        self._body = []
        for key, value in kwargs.items():
            if key in KEYWORDS:
                self._keywords[key] = value
            else:
                raise ValueError, "invalid keyword %s" % (key,)

    def set_body(self, text):
        self._body = [str(text)]

    def write(self, text):
        self._body.append(str(text))

    def set_priority(self, pri):
        if type(pri) is int and pri in range(1, len(PRIORITY_VALUES)+1):
            self._keywords["priority"] = PRIORITY_VALUES[pri-1]
        elif type(pri) is str and pri in PRIORITY_VALUES:
            self._keywords["priority"] = pri
        else:
            raise ValueError, "%s: invalid priority '%s'" % (self.__class__.__name__, pri,)

    def set_severity(self, sev):
        if type(sev) is int and sev in range(1, len(SEVERITY_VALUES)+1):
            self._keywords["bug_severity"] = SEVERITY_VALUES[sev-1]
        elif type(sev) is str and sev in SEVERITY_VALUES:
            self._keywords["bug_severity"] = sev
        else:
            raise ValueError, "%s: invalid severity '%s'" % (self.__class__.__name__, sev,)

    def verify(self):
        for key, value in KEYWORDS.items():
            if value: # mandatory keyword
                if key not in self._keywords:
                    raise ValueError, "%s: mandatory keyword '%s' not present" % (self.__class__.__name__, key,)
        try:
            bs = self._keywords["bug_severity"]
        except KeyError:
            pass
        else:
            if bs not in SEVERITY_VALUES:
                raise ValueError, "%s: invalid severity '%s'" % (self.__class__.__name__, bs,)
        try:
            pv = self._keywords["priority"]
        except KeyError:
            pass
        else:
            if pv not in PRIORITY_VALUES:
                raise ValueError, "%s: invalid priority '%s'" % (self.__class__.__name__, pv,)


    def __setitem__(self, key, value):
        if key in KEYWORDS:
            self._keywords[key] = value
        else:
            raise TypeError, "invalid keyword %s" % (key,)

    def __getitem__(self, key):
        return self._keywords[key]

    def __repr__(self):
        return "<%s instance at 0x%x>" % (self.__class__.__name__, id(self))

    def __str__(self):
        self.verify()
        s = []
        for key, value in self._keywords.items():
            s.append("@%s = %s" % (key, value) )
        s.append("\n")
        s.extend(self._body)
        return "\n".join(s)


if __name__ == "__main__":
    bb = BugzillaBody(product="pynms", component="bugzillaclient", version="1.0")
    bb["short_desc"] = "some bug I found."
    bb.write("some description.")
    bb.write("more things.")
    print bb
