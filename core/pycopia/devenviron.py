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
Update environ with what's in the $HOME/.pyinteractiverc file.  Child processes
such as interactive module and vim environment uses this.

If the ~/.pyinteractiverc file does not exist a default one will be created.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


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

