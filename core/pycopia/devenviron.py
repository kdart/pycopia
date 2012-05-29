#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

"""
Update environ with what's in the $HOME/.pyinteractiverc file.  Child processes
such as interactive module and vim environment uses this.

If the ~/.pyinteractiverc file does not exist a default one will be created.
"""

import sys
import os

if sys.platform == "win32":
    RCFILE = os.path.join(os.path.expandvars("$USERPROFILE"), "_pyinteractiverc")
else:
    RCFILE = os.path.join(os.path.expandvars("$HOME"), ".pyinteractiverc")

# Create default rc file if it doesn't exist.
if not os.path.exists(RCFILE):
    with open(RCFILE, "w") as rcfo:
        rcfo.write("""#!/usr/bin/python
# some configuration stuff primarily for the 'interactive' module.

PYPS1 = "Python> "
PYPS2 = ".more.> "

# programs
#XTERM = "urxvtc -title Python -name Python -e %s"
XTERM = "xterm -title Python -name Python -e %s"
#EDITOR = '/usr/bin/vim'
XEDITOR = "/usr/bin/gvim"
VIEWER = "/usr/bin/view"
XVIEWER = "/usr/bin/gview"
#BROWSER = '/usr/bin/firefox "%s"'
CBROWSER = '/usr/bin/links "%s"'
CHMBOOK = '$HOME/.local/share/devhelp/books/python266.chm'
CHMVIEWER = 'kchmviewer --search %s "%s"'
""")
    del rcfo

try:
    env = { # default values if not set anywhere else.
            b"EDITOR": os.environ.get("EDITOR", "/usr/bin/vi"),
            b"BROWSER": os.environ.get("BROWSER", '/usr/bin/firefox "%s"'),
          }
    execfile(RCFILE, env, env)
except:
    ex, val, tb = sys.exc_info()
    print ("warning: could not read config file:", RCFILE, file=sys.stderr)
    print (val, file=sys.stderr)
    del ex, val, tb
else:
    for name, val in env.items():
        if type(val) is str:
            os.environ[name] = val.encode("ascii")
    del name, val
del env

