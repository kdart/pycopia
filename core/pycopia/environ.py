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
Then environ module defines the Environ class. The Environ class simulates a
shell environment that provides methods analogous to shell commands that
manipulate the environment. Also, variable expansion is performed when setting
new values.

"""

import os

import re
_var_re = re.compile(r'\$([a-zA-Z0-9_\?]+|\{[^}]*\})')
del re

class Environ(dict):
    """Environ is a dictionary (like os.environ) that does automatic variable
expansion when setting new elements. It supports an extra method called
'export' that takes strings of the form 'name=value' that may be used to set
assign variable names.  The 'expand' method will return a string with variables
expanded from the values contained in this object.  """

    def __setitem__(self, name, value):
        super(Environ, self).__setitem__(name, value)

    def __getattr__(self, name):
        return super(Environ, self).__getitem__(name)

    __setattr__ = __setitem__

    def __delattr__(self, key):
        return super(Environ, self).__delitem__(key)

    def inherit(self, env=None):
        """inherit([dict])
Works like the 'update' method, but defaults to updating from the system
environment (os.environ)."""
        if env is None:
            env = os.environ
        self.update(env)
    
    def set(self, val):
        self.__setitem__(name, self.expand(str(val)))

    def export(self, nameval):
        """export('name=value')
Works like the export command in the bash shell. assigns the name on the left
of the equals sign to the value on the right, performing variable expansion if
necessary.  """
        name, val = nameval.split("=", 1)
        self.__setitem__(name, self.expand(str(val)))
        return name

    def __str__(self):
        s = map(lambda nv: "%s=%s" % (nv[0], nv[1]), self.items())
        s.sort()
        return "\n".join(s)

    def expand(self, value):
        """expand(string)
Pass in a string that might have variable expansion to be performed
(e.g. a section that has $NAME embedded), and return the expanded
string.  """
        i = 0
        while 1:
            m = _var_re.search(value, i)
            if not m:
                return value
            i, j = m.span(0)
            vname = m.group(1)
            if vname[0] == '{':
                vname = vname[1:-1]
            tail = value[j:]
            tv = self.get(vname)
            if tv is not None: # exand to empty if not found or val is None
                value = value[:i] + str(tv) 
            else:
                value = value[:i]
            i = len(value)
            value = value + tail

    def copy(self):
        return Environ(self)

if __name__ == "__main__":
    d = Environ()
    #d.inherit()
    d.export("HOME=/home/user")
    d.export("PKGHOME=/opt/pkg")
    d.export("PATH=$HOME/bin")
    d.export("PATH=$PATH:${PKGHOME}/bin")
    print d
    print "-----"
    d["?"] = 0
    print d.expand("Here is the PATH: $PATH")
    print d.expand("$?")

