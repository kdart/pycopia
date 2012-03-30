#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2011  Keith Dart <keith@dartworks.biz>
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

If the ~/.pyinteractiverc file does not exist a default one will be created.

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
from __future__ import unicode_literals
from __future__ import division


import sys, os, types
import atexit
from pprint import pprint
from inspect import *
from dis import dis, distb
try:
    from importlib import import_module
except ImportError: # older python
    from pycopia.module import get_module as import_module


try:
    import rlcompleter2
except ImportError:
    import rlcompleter

from pycopia.cliutils import *
from pycopia.textutils import *
from pycopia.aid import add2builtin, callable, execfile


try:
    import readline
except ImportError:
    # dummy readline to make rest of this module happy.
    class Readline(object):
        def parse_and_bind(self, *args):
            pass
        def read_history_file(self, arg):
            pass
        def write_history_file(self, arg):
            pass
    readline = Readline()


if "DISPLAY" in os.environ:
    try:
        from pycopia import gtktools
    except ImportError:
        pass # no gtk? oh well...
    else:
        # gdk "magically" stuffs these in __main__ for some strange reason.
        # so this hack removes them.
        main = sys.modules["__main__"]
        del main.GInitiallyUnowned, main.GPollableInputStream, main.GPollableOutputStream
        del main
        choose = gtktools.list_picker # replace cliutils.choose

__all__ = ['info', 'run_config', 'pyterm', 'xterm', 'edit', 'get_editor',
'exec_editor', 'open_url', 'open_file', 'showdoc', 'dis', 'distb']

def _add_all(modname):
    mod = import_module(modname)
    __all__.extend([n for n in dir(mod) if n[0] != "_" and callable(getattr(mod, n))])

_add_all("pycopia.textutils")
_add_all("inspect")
del _add_all

# update environ with what's in the rc file.
if sys.platform == "win32":
    RCFILE = os.path.join(os.path.expandvars("$USERPROFILE"), "_pyinteractiverc")
else:
    RCFILE = os.path.join(os.path.expandvars("$HOME"), ".pyinteractiverc")

# Create default rc file if it doesn't exist.
if not os.path.exists(RCFILE):
    rcfo = open(RCFILE, "w")
    rcfo.write("""#!/usr/bin/python
# some configuration stuff primarily for the 'interactive' module.

PYPS1 = "Python> "
PYPS2 = ".more.> "

# programs
#XTERM = "urxvtc -title Python -name Python -e %s"
XTERM = "xterm -title Python -name Python -e %s"
EDITOR = '/usr/bin/vim'
XEDITOR = "/usr/bin/gvim"
VIEWER = "/usr/bin/view"
XVIEWER = "/usr/bin/gview"
BROWSER = '/usr/bin/epiphany "%s"'
CBROWSER = '/usr/bin/links "%s"'
CHMBOOK = '$HOME/.local/share/devhelp/books/python266.chm"
CHMVIEWER = 'kchmviewer --search %s "%s"'
""")
    rcfo.close()
    del rcfo

try:
    env = {}
    execfile(RCFILE, env, env) 
except:
    ex, val, tb = sys.exc_info()
    print ("warning: could not read config file:", RCFILE, file=sys.stderr)
    print (val, file=sys.stderr)
else:
    for name, val in env.items():
        if isinstance(val, basestring):
            os.environ[str(name)] = str(val)
del env

PYTHON = os.environ.get("PYTHONBIN", sys.executable) # set PYTHONBIN for alternate interpreter
sys.ps1 = os.environ.get("PYPS1", "Python{0}> ".format(sys.version_info[0]))
sys.ps2 = os.environ.get("PYPS2", "more...> ")


def info(obj=None):
    """Print some helpful information about the given object. Usually the
    docstring.  If no parameter given then provide some info on Python itself."""
    if obj is None:
        print ("Python keywords:")
        import keyword
        print (pprint(keyword.kwlist))
        print()
        plist = [] ; clist = []
        for bi_object in __builtins__.values():
            if callable(bi_object):
                if type(bi_object) is types.ClassType:
                    clist.append(bi_object.__name__)
                elif type(bi_object) is types.FunctionType:
                    plist.append(bi_object.func_code.co_name)
        plist.sort() ; clist.sort()
        print ("Python built-in functions:")
        pprint(plist)
        print()
        print ("Python built-in exceptions:")
        pprint(clist)
        print()
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

def run_config(cfstring, param):
    if not cfstring:
        print ("No command string defined to run {0}.".format(param), file=sys.stderr)
        return
    try:
        cmd = cfstring % param
    except TypeError: # no %s in cfstring, so just stick the param on the end
        cmd = "%s %s" % (cfstring, param)
    print("CMD:", repr(cmd))
    return os.system(cmd)

def pyterm(filename="", interactive=1):
    cmd = "%s %s %s " % (PYTHON, "-i" if interactive else "", filename)
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)

def xterm(cmd="/bin/sh"):
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)

def edit(modname):
    """
Opens the $XEDITOR with the given module source file (if found).
    """
    filename = find_source_file(modname)
    if filename:
        ed = get_editor()
        return run_config(ed, filename)
    else:
        print ("Could not find source to {0}.".format(modname), file=sys.stderr)

def view(modname):
    """
Opens the $[X]VIEWER with the given module source file (if found).
    """
    filename = find_source_file(modname)
    if filename:
        ed = get_viewer()
        return run_config(ed, filename)
    else:
        print ("Could not find source to %s." % modname, file=sys.stderr)

def get_editor():
    if "DISPLAY" in os.environ:
        ed = os.environ.get("XEDITOR", None)
    else:
        ed = os.environ.get("EDITOR", None)
    if ed is None:
        ed = get_input("Use which editor?", "/bin/vi")
    return ed

def get_viewer():
    if "DISPLAY" in os.environ:
        ed = os.environ.get("XVIEWER", None)
    else:
        ed = os.environ.get("VIEWER", None)
    if ed is None:
        ed = get_input("Use which viewer?", "/usr/bin/view")
    return ed

def exec_editor(*names):
    """Runs your configured editor on a supplied list of files. Uses exec,
there is no return!"""
    ed = get_editor()
    if ed.find("/") >= 0:
        os.execv(ed, (ed,)+names)
    else:
        os.execvp(ed, (ed,)+names)

def open_url(url):
    """Opens the given URL in an external viewer. """
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("BROWSER"), url)
    else:
        return run_config(os.environ.get("CBROWSER"), url)

def find_source_file(modname):
    try:
        return getsourcefile(modname)
    except TypeError:
        return None

def open_chm(search):
    """Opens the given search term with a CHM viewer. """
    if "DISPLAY" in os.environ:
        book = os.path.expandvars(os.environ.get("CHMBOOK", 
                '$HOME/.local/share/devhelp/books/python321rc1.chm'))
        return run_config(os.environ.get("CHMVIEWER", 'kchmviewer --search %s "%s"'), (search, book))
    else:
        print ("open_chm: No CHM viewer for text mode.", file=sys.stderr)

def open_file(filename):
    return open_url("file://"+filename)


def get_object_name(object):
    objtype = type(object)
    if objtype is str:
        return object
    elif objtype is types.ModuleType or objtype is types.BuiltinFunctionType:
        return object.__name__
    else:
        print ("get_object_name: can't determine object name", file=sys.stderr)
        return None


def show_chm_doc(object, chooser=None):
    name = get_object_name(object)
    if name is None:
        return
    open_chm(name)

showdoc = show_chm_doc

def mydisplayhook(obj):
    pprint(obj)
    setattr(sys.modules["__main__"], "_", obj)
setattr(sys.modules["__main__"], "_", None)

sys.displayhook = mydisplayhook

# Add some functions useful for interactive use to builtins.
# This is done to provide better interactive functionality without
# cluttering the __main__ namespace.
def _add_builtins(names=__all__):
    for name in names:
        add2builtin(name, getattr(sys.modules[__name__], name))

_add_builtins()

if sys.platform == "win32":
    _default_hist = os.path.join(os.environ["USERPROFILE"], "_pythonhist")
else:
    _default_hist = os.path.join(os.environ["HOME"], ".pythonhist")
PYHISTFILE = os.environ.get("PYHISTFILE", _default_hist)

try:
    readline.read_history_file(PYHISTFILE)
except IOError:
    pass
def savehist():
    readline.write_history_file(PYHISTFILE)
atexit.register( savehist )
readline.parse_and_bind("tab: complete")

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

