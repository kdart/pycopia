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
some functions helpful in Python's interactive mode.

I use it like this. Create a file called ~/.pythonrc with the following contents:

----
#!/usr/bin/python
import interactive

----
This modules needs some environment variables to be set. You can also set these
in the .pythonrc file.

PYPS1          - primary interactive prompt
PYPS2          - "more" prompt
PYTHONDOCS     - base directory of the Python HTML documentation set.
PYHISTFILE     - name of the history file (defaults to $HOME/.pythonhist)

Some external program invocations should be defined. These may contain a
'%s' that will be expanded to a file name or url.

XTERM          - How to invoke xterm, e.g. "urxvtc -title Python -name Python -e %s"
EDITOR         - editor to use in the currrent terminal, 
VIEWER         - What terminal text viewer (e.g. "/usr/bin/view")
XEDITOR        - text editor for use in the X Windows System.
XVIEWER        - What X text viewer (e.g. "/usr/bin/mousepad")
BROWSER        - HTML browser for X GUI.
CBROWSER       - HTML browser for character terminals.

Now, create some shell aliases in your .bashrc file:

alias py='/usr/bin/env PYTHONSTARTUP=$HOME/.pythonrc python -i'

now, just type "py" at the command line to get a Python interactive mode shell
with enhanced functionality.

Alternatively, you can just 'import interactive' at the original Python prompt.

"""

# stock modules
import sys, os, types
from pprint import pprint
from pycopia.cliutils import *
from pycopia.aid import add2builtin, IF


try:
    import readline
except ImportError:
    # dummy readline to fake the rest of this module
    class Readline:
        def parse_and_bind(self, *args):
            pass
        def read_history_file(self, arg):
            pass
        def write_history_file(self, arg):
            pass
    readline = Readline()

# Big dictionary generated by the 'mkpydocindex' program. Contains
# the Python HTML documentation index dictionary. This is None now, it will be
# imported later if it is used by showdoc().
PYINDEX = None
PYDOCINDEXFILE = os.path.join("/", "var", "tmp", "pydocindex.py")

gtktools = None
if os.environ.has_key("DISPLAY"):
    try:
        from pycopia import gtktools
    except:
        pass # no gtk? oh well...

__all__ = ['info', 'run_config', 'pyterm', 'xterm', 'edit', 'get_editor',
'exec_editor', 'open_url', 'open_file', 'get_pydocindex', 'get_doc_urls',
'showdoc']
from pycopia.textutils import *
from pycopia import textutils
__all__.extend([n for n in dir(textutils) if n[0] != "_" and callable(getattr(textutils, n))])
del textutils

# update environ with what's in the rc file.
if sys.platform == "win32":
    RCFILE = os.path.join(os.path.expandvars("$USERPROFILE"), "_pyinteractiverc")
else:
    RCFILE = os.path.join(os.path.expandvars("$HOME"), ".pyinteractiverc")

try:
    env = {}
    execfile(RCFILE, env, env) 
except:
    ex, val, tb = sys.exc_info()
    print >>sys.stderr, "warning: could not read config file."
    print >>sys.stderr, ex, val
else:
    for name, val in env.items():
        if type(val) is str:
            os.environ[name] = val
del env

PYTHON = os.environ.get("PYTHONBIN", "python") # use for alternate interpreter
sys.ps1 = os.environ.get("PYPS1", "Python> ")
sys.ps2 = os.environ.get("PYPS2", ".more.> ")


def info(obj=None):
    """Print some helpful information about the given object. Usually the
    docstring.  If no parameter given then provide some info on Python itself."""
    if obj is None:
        print "Python keywords:"
        import keyword
        print pprint(keyword.kwlist)
        print
        plist = [] ; clist = []
        for bi_object in __builtins__.values():
            if callable(bi_object):
                if type(bi_object) is types.ClassType:
                    clist.append(bi_object.__name__)
                elif type(bi_object) is types.FunctionType:
                    plist.append(bi_object.func_code.co_name)
        plist.sort() ; clist.sort()
        print "Python built-in functions:"
        pprint(plist)
        print
        print "Python built-in exceptions:"
        pprint(clist)
        print
    elif hasattr(obj, "__doc__") and obj.__doc__ is not None:
            print "Documentation for %s :\n" % (obj.__name__)
            print obj.__doc__
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
        print >>sys.stderr, "No command string defined to run %s." % (param)
        return
    try:
        cmd = cfstring % param
    except TypeError: # no %s in cfstring, so just stick the param on the end
        cmd = "%s %s" % (cfstring, param)
    return os.system(cmd)

def pyterm(filename="", interactive=1):
    cmd = "%s %s %s " % (PYTHON, IF(interactive, "-i", ""), filename)
    if os.environ.has_key("DISPLAY"):
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)

def xterm(cmd="/bin/sh"):
    if os.environ.has_key("DISPLAY"):
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
        print >>sys.stderr, "Could not find source to %s." % modname

def view(modname):
    """
Opens the $[X]VIEWER with the given module source file (if found).
    """
    filename = find_source_file(modname)
    if filename:
        ed = get_viewer()
        return run_config(ed, filename)
    else:
        print >>sys.stderr, "Could not find source to %s." % modname

def get_editor():
    if os.environ.has_key("DISPLAY"):
        ed = os.environ.get("XEDITOR", None)
    else:
        ed = os.environ.get("EDITOR", None)
    if ed is None:
        ed = get_input("Use which editor?", "/bin/vi")
    return ed

def get_viewer():
    if os.environ.has_key("DISPLAY"):
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
    if os.environ.has_key("DISPLAY"):
        return run_config(os.environ.get("BROWSER"), url)
    else:
        return run_config(os.environ.get("CBROWSER"), url)

def open_file(filename):
    return open_url("file://"+filename)

def get_pydocindex():
    global PYINDEX # from pydocindex.py file
    if not PYINDEX: # lazy import
        try:
            execfile(PYDOCINDEXFILE, globals())
        except IOError:
            print >>sys.stdout, "no file pydocindex.py. Run mkpydocindex to generate it."
            return None

def get_doc_urls(keyword):
    global PYINDEX
    if not PYINDEX: # lazy import
        get_pydocindex()
    if PYINDEX:
        return PYINDEX.get(keyword, None)
    else:
        return None

def showdoc(object, chooser=None):
    """Opens your browser with the HTML documentation for the Python object.
Choose from a list if more than one document is found."""
    if not chooser:
        if gtktools:
            chooser = gtktools.list_picker
        else:
            chooser = choose

    objtype = type(object)
    if objtype is str:
        name = object
    elif objtype is types.ModuleType or objtype is types.BuiltinFunctionType:
        name = object.__name__
    else:
        print >>sys.stderr, "showdoc: can't determine object name"
        return
    docuri = get_doc_urls(name)
    if docuri:
        if len(docuri) == 1:
            open_url("file:///%s/%s" % (os.environ.get("PYTHONDOCS"), docuri[0]))

        else:
            uri = chooser(docuri)
            if uri:
                open_url("file:///%s/%s" % (os.environ.get("PYTHONDOCS"), uri))
    else:
        print >>sys.stderr, "showdoc: No documentation found."



def mydisplayhook(obj):
    pprint(obj)
    setattr(sys.modules["__main__"], "_", obj)
    #__builtins__._ =  obj
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

## readline key bindings
##readline.parse_and_bind("tab: menu-complete")
#readline.parse_and_bind("tab: complete")
#readline.parse_and_bind('"?": possible-completions')
readline.parse_and_bind('"\M-h": "help()\n"')
readline.parse_and_bind('"\eOP": "help()\n"')
readline.parse_and_bind('"\M-?": possible-completions')
readline.parse_and_bind('"\M-f": dump-functions')
readline.parse_and_bind('"\M-v": dump-variables')
readline.parse_and_bind('"\M-m": dump-macros')
# additional readline options
##readline.parse_and_bind("set editing-mode vi")
#readline.parse_and_bind("set show-all-if-ambiguous on")
#readline.parse_and_bind("set meta-flag on")
#readline.parse_and_bind("set input-meta on")
#readline.parse_and_bind("set output-meta on")
#readline.parse_and_bind("set convert-meta off")
#


