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

r"""
some functions helpful in Python's interactive mode.

This modules uses some environment variables. You can also set these
in the ~/.pyinteractiverc file.

PYPS1          - primary interactive prompt
PYPS2          - "more" prompt
PYHISTFILE     - name of the history file (defaults to $HOME/.pythonhist)

Some external program invocation templates should be defined. These may contain a
'%s' that will be expanded to a file name or url.

XTERM          - How to invoke xterm, e.g. "urxvtc -title Python -name Python -e %s"
EDITOR         - editor to use in the currrent terminal,
VIEWER         - What terminal text viewer (e.g. "/usr/bin/view")
XEDITOR        - text editor for use in the X Windows System.
XVIEWER        - What X text viewer (e.g. "/usr/bin/gvim")
BROWSER        - HTML browser for X GUI.
CBROWSER       - HTML browser for character terminals.
CHMBOOK        - File name of CHM help file.
CHMVIEWER      - A GUI CHM viewer taking search and book replacements. e.g. 'kchmviewer --search %s %s'

You can also create some shell aliases in your .bashrc file, like so:

alias py='python -i -c "from pycopia import interactive"'

now, just type "py" at the command line to get a Python interactive mode shell
with enhanced functionality.

Alternatively, you can just invoke 'from pycopia import interactive' at the
"stock" Python prompt.

This modules places many helpful, convenience functions in the builtins
namespace for quck access without cluttering the __main__ namespace.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, os, types
from pprint import pprint
from inspect import *

from pycopia import devenviron


try:
    import readline
except ImportError:
    # dummy readline to make rest of this module happy in case readline is not available.
    class Readline(object):
        def parse_and_bind(self, *args):
            pass
        def read_history_file(self, arg):
            pass
        def write_history_file(self, arg):
            pass
    readline = Readline()

try:
    from importlib import import_module
except ImportError: # older python
    from pycopia.module import get_module as import_module

if sys.platform == "win32":
    _default_hist = os.path.join(os.environ["USERPROFILE"], "_pythonhist")
else:
    _default_hist = os.path.join(os.environ["HOME"], ".pythonhist")
PYHISTFILE = os.environ.get("PYHISTFILE", _default_hist)
del _default_hist

# Prefer rlcompleter2, if installed.
try:
    import rlcompleter2
    rlcompleter2.setup(PYHISTFILE, verbose=0)
except ImportError:
    import rlcompleter
    import atexit
    try:
        readline.read_history_file(PYHISTFILE)
    except IOError:
        pass
    def savehist():
        readline.write_history_file(PYHISTFILE)
    atexit.register( savehist )
    readline.parse_and_bind("tab: complete")


# import some pycopia functions that are helpful for interactive use.
from pycopia.cliutils import *
from pycopia.textutils import *
from pycopia.aid import add2builtin, execfile
from pycopia.devhelpers import *

__all__ = ['info']

def _add_all(modname):
    mod = import_module(modname)
    __all__.extend([n for n in dir(mod) if n[0] != "_" and callable(getattr(mod, n))])

_add_all("pycopia.textutils")
_add_all("pycopia.cliutils")
_add_all("pycopia.devhelpers")
_add_all("inspect")
del _add_all

sys.ps1 = os.environ.get("PYPS1", "Python{0}> ".format(sys.version_info[0]))
sys.ps2 = os.environ.get("PYPS2", "more...> ")

def info(obj=None):
    """Print some helpful information about the given object. Usually the
    docstring.  If no parameter given then provide some info on Python itself."""
    if obj is None:
        print ("Python keywords:")
        import keyword
        for kwname in keyword.kwlist:
            print ("  ", kwname)
        print("Built in objects:")
        for bi_object_name in sorted(__builtins__.keys()):
            bi_object = __builtins__[bi_object_name]
            if callable(bi_object):
                if type(bi_object) is types.ClassType:
                    print("  {} (class)".format(bi_object.__name__))
                elif type(bi_object) is types.FunctionType:
                    print("  {} (function)".format(bi_object.__name__))
    elif hasattr(obj, "__doc__") and obj.__doc__ is not None:
            print ("Documentation for %s :\n" % (obj.__name__))
            print (obj.__doc__)
    elif type(obj) is types.ModuleType:
        pprint(dir(obj))
    elif type(obj) is types.ClassType:
        pprint(dir(obj))
    elif type(obj) is types.InstanceType:
        pprint(dir(obj))
        pprint(dir(obj.__class__))
    return ""


def mydisplayhook(obj):
    pprint(obj)
    setattr(sys.modules["__main__"], "_", obj)
sys.displayhook = mydisplayhook
setattr(sys.modules["__main__"], "_", None)



# Add some functions useful for interactive use to builtins.
# This is done to provide better interactive functionality without
# cluttering the __main__ namespace.
def _add_builtins(names=__all__):
    for name in names:
        try:
            add2builtin(name, getattr(sys.modules[__name__], name))
        except AttributeError:
            pass

_add_builtins()
del _add_builtins


## readline key bindings
##readline.parse_and_bind("tab: menu-complete")
#readline.parse_and_bind('"?": possible-completions')
readline.parse_and_bind('"\M-?": possible-completions')
#readline.parse_and_bind('"\M-h": "help()\n"')
#readline.parse_and_bind('"\eOP": "help()\n"')
#readline.parse_and_bind('"\M-f": dump-functions')
#readline.parse_and_bind('"\M-v": dump-variables')
#readline.parse_and_bind('"\M-m": dump-macros')
# additional readline options
##readline.parse_and_bind("set editing-mode vi")
#readline.parse_and_bind("set show-all-if-ambiguous on")
#readline.parse_and_bind("set meta-flag on")
#readline.parse_and_bind("set input-meta on")
#readline.parse_and_bind("set output-meta on")
#readline.parse_and_bind("set convert-meta off")

