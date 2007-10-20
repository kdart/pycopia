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
Provides a standard command line interpreter for programs needing one.
Supports different command contexts, customizable user interface, generic
object CLI's, and other neat stuff.

"""

__all__ = ['CLIException', 'CommandQuit', 'CommandExit', 'NewCommand',
'BaseCommands', 'DictCLI', 'ListCLI', 'GenericCLI', 'FileCLI',
'Completer', 'Shell', 'CommandParser', 'globargv', 'breakout_args',
'clieval', 'get_generic_cmd', 'get_generic_clone', 'get_generic_cli',
'get_history_file', 'run_cli_wrapper', 'run_cli', 'run_generic_cli',
'get_cli', 'get_terminal_ui', 'get_ui']

import sys, os
from cStringIO import StringIO
import traceback

try:
    import readline # readline is very, very important to us...
except ImportError:
    readline = None # ...but try to live without it if it is not available.

import timelib
import environ
from types import MethodType

from pycopia import tty
from pycopia import getopt
from pycopia.IO import ConsoleIO
from pycopia.UI import DefaultTheme, UserInterface, method_repr, safe_repr
from pycopia.fsm import FSM, ANY
from pycopia.aid import IF, Print, removedups

# global timer for timing methods
from pycopia import scheduler
timer = scheduler.get_scheduler()
del scheduler

_DEBUG = False


class CLIException(Exception):
    def __init__(self, value=None):
        self.value = value

class CLISyntaxError(CLIException):
    """You may raise this if parsing argv doesn't make sense to you. """
    pass

class CommandQuit(CLIException):
    """An exception that is used to signal quiting from a command object. """
    pass

class CommandExit(CLIException):
    """An exception that is used to signal exiting from the command object. The
    command is not popped.  """
    pass

class NewCommand(CLIException):
    """Used to signal the parser to push a new command object.
Raise this with an instance of BaseCommands as a value."""
    pass


class BaseCommands(object):
    """A base class that defines a holder object for command methods. It dispatches
the methods when you call it with an argv-style list of arguments. The first
argument must match a name of a method.
"""
    def __init__(self, ui, aliases=None):
        # initialize local variables
        self._aliases = aliases or {}
        self._command_list = None
        self._repeater = None
        self._completion_scopes = {}
        self._completers = []
        self._obj = None # may be in instance of some interface commands may use.
        self.set_userinterface(ui)
        self.initialize()

    def __del__(self):
        self.stop(None)

    # optional extra initialization. Override in subclass if desired.
    def initialize(self):
        pass

    # optional finalize method. called when CLI quits.
    def finalize(self):
        pass

    def set_userinterface(self, ui):
        self._ui = ui
        # map in user interface input and output for speed
        self._user_input = ui.user_input
        self._more_user_input = ui.more_user_input
        self._print = ui.Print
        self._pprint = ui.pprint
        self._format = ui.format
        self._print_list = ui.print_list
        self._set_theme = ui.set_theme
        self._environ = ui._env

    # override this and call it for command sets the need post-instantiation setup.
    def _setup(self, obj, prompt="> "):
        self._obj = obj # an object to call methods on, if needed
        self._environ["PS1"] = str(prompt)
        self._reset_scopes()

    def _reset_scopes(self):
        pass

    # overrideable exception hook method - do something with command exceptions.
    def except_hook(self, ex, val, tb):
        self._ui.error("%s (%s)" % (ex, val))

    # override this if your subcommand passes something useful back
    # via a parameter to the CommandQuit exception. 
    def handle_subcommand(self, value):
        pass

    # override this for default actions
    def default_command(self, argv):
        self._ui.error("unknown command: %r" % (argv[0]))
        return 2

    # completer management methods
    def add_completion_scope(self, name, complist):
        self._completion_scopes[name] = list(complist)

    def get_completion_scope(self, name="commands"):
        return self._completion_scopes.get(name, [])

    def remove_completion_scope(self, name):
        del self._completion_scopes[name]

    def push_completer(self, namespace):
        if readline:
            orig = readline.get_completer()
            if orig is not None:
                self._completers.append(orig)
            readline.set_completer(Completer(namespace).complete)

    def pop_completer(self):
        if readline:
            if self._completers:
                c = self._completers.pop()
                readline.set_completer(c)

    # convenient access to option parsing.
    def getopt(self, argv, shortopts):
        return getopt.getopt(argv[1:], shortopts)
        # returns: optlist, longoptdict, args

    # dispatch commands by calling the instance
    def __call__(self, argv):
        if not argv or not argv[0] or argv[0].startswith("_"):
            return 2
        argv = self._expand_aliases(argv)
        # special escape characters...
        if argv[0].startswith("!"): # bang-escape reads pipe
            argv[0] = argv[0][1:]
            argv.insert(0, "pipe")
        elif argv[0].startswith("%"): # percent-escape spawns pty
            argv[0] = argv[0][1:]
            argv.insert(0, "spawn")
        elif argv[0].startswith("#"): # comment
            return 0
        elif argv[0].startswith("@"): # python exec escape
            argv[0] = argv[0][1:]
            argv.insert(0, "pyexec")
        elif argv[0].startswith("="): # python eval escape
            argv[0] = argv[0][1:]
            argv.insert(0, "pyeval")
        # ok, now fetch the real method...
        try:
            meth = getattr(self, argv[0])
        except AttributeError:
            meth = self.default_command
        # ...and exec it.
        try:
            rv = meth(argv) # call the method
        except (NewCommand, CommandQuit, CommandExit, KeyboardInterrupt):
            raise # pass these through to parser
        except (CLISyntaxError, IndexError): # tried to get non-existent argv value
            self._print("Parsing error.")
            self._print(meth.__doc__)
        except getopt.GetoptError, err:
            self._print("option %r: %s" % (err.opt, err.msg))
        except:
            ex, val, tb = sys.exc_info()
            if _DEBUG:
                from pycopia import debugger # import here due to circular dependency
                debugger.post_mortem(tb, ex, val)
            else:
                self.except_hook(ex, val, tb)
        else:
            try:
                self._environ["?"] = int(rv)
            except (ValueError, TypeError, AttributeError):
                self._environ["?"] = -1
            self._environ["_"] = rv
            return rv

    def _expand_aliases(self, argv):
        seen = {}
        while 1:
            alias = self._aliases.get(argv[0], None)
            if alias:
                if alias[0] in seen:
                    break # alias loop
                seen[alias[0]] = True
                # do the substitution
                del argv[0]
                rl = alias[:]
                rl.reverse()
                for arg in rl:
                    argv.insert(0, arg)
            else:
                break
        return argv

    def _export(self, name, val):
        """put a name-value pair in the environment."""
        self._environ[name] = val

    # Start a new BaseCommands (or subclass), with the same environment.
    # The new command object gets a copy of the environment, but the same aliases.
    def clone(self, cliclass=None, theme=None):
        if cliclass is None:
            cliclass = self.__class__
        newui = self._ui.clone(theme)
        return cliclass(newui, self._aliases)

    def subshell(self, io, env=None, aliases=None, theme=None):
        cliclass = self.__class__
        newui = UserInterface(io, env or self._environ.copy(), theme)
        aliases = aliases or self._aliases
        return cliclass(newui, aliases)

    def get_commands(self):
        if self._command_list is None:
            hashfilter = {}
            for name in filter(self._command_filt, dir(self)):
                ## this filters out aliases (same function id)
                meth = getattr(self, name)
                hashfilter[id(meth.im_func)] = meth.im_func.func_name
            self._command_list = hashfilter.values()
            self._command_list.sort()
        return self._command_list

    # user visible commands are methods that don't have a leading underscore,
    # and do have a docstring.
    def _command_filt(self, objname):
        if objname.startswith("_"):
            return 0
        obj = getattr(self, objname)
        if type(obj) is MethodType and obj.__doc__:
            return 1
        else:
            return 0

    def commandlist(self, argv):
        self._print_list(self.get_commands())

    ################################
    # actual commands follow (no leading '_' and has a docstring.)
    #
    def debug(self, argv):
        """debug ["on"|"off"]
    Enables debugging for CLI code. 
    Enters the debugger if an exception occurs."""
        global _DEBUG
        if len(argv) > 1:
            cmd = argv[1]
            if cmd == "on":
                _DEBUG = True
            else:
                _DEBUG = False
        else:
            self._ui.printf(
                 "Debugging is currently %%I%s%%N." % (IF(_DEBUG, "on", "off"),))

    def printf(self, argv):
        """printf [<format>] <args>....
    Print the arguments according to the format, 
    or all arguments if first is not a format string."""
        if argv[1].find("%") >= 0:
            try:
                ns = vars(self._obj)
            except:
                ns = globals()
            args, kwargs = breakout_args(argv[2:], ns)
            self._print(str(argv[1]) % args)
        else:
            self._print(" ".join(argv[1:]))

    def exit(self, argv):
        """exit
    Exits this command interpreter instance.  """
        raise CommandQuit
    quit = exit

    def printenv(self, argv):
        """printenv [name ...]
    Shows the shell environment that processes will run with.  """
        if len(argv) == 1:
            names = self._environ.keys()
            names.sort()
            ms = reduce(max, map(len, names))
            for name in names:
                value = self._environ[name]
                self._print("%*s = %s" % (ms, name, safe_repr(value)))
        else:
            s = []
            for name in argv[1:]:
                try:
                    s.append("%s = %s" % (name, safe_repr(self._environ[name])))
                except KeyError:
                    pass
            self._print("\n".join(s))

    def history(self, argv):
        """history [<index>]
    Display the current readline history buffer."""
        if not readline:
            self._print("The readline library is not available.")
            return
        if len(argv) > 1:
            idx = int(argv[1])
            self._print(readline.get_history_item(idx))
        else:
            for i in xrange(readline.get_current_history_length()):
                self._print(readline.get_history_item(i))

    def export(self, argv):
        """export NAME=VAL
    Sets environment variable that new processes will inherit.
    """
        for arg in argv[1:]:
            try:
                self._environ.export(arg)
            except:
                ex, val = sys.exc_info()[:2]
                self._print("** could not set value: %s (%s)" % (ex, val))

    def unset(self, argv):
        """unset <envar>
    Unsets the environment variable."""
        try:
            del self._environ[argv[1]]
        except:
            return 1

    def setenv(self, argv):
        """setenv NAME VALUE
    Sets the environment variable NAME to VALUE, like C shell.  """
        if len(argv) < 3:
            self._print(self.setenv.__doc__)
            return
        self._environ[argv[1]] = argv[2]
        return self._environ["_"]

    def echo(self, argv):
        """echo ...
    Echoes arguments back.  """
        self._print(" ".join(argv[1:]))
        return self._environ["_"]

    def pipe(self, argv):
        """pipe <command>
    Runs a shell command via a pipe, and prints its stdout and stderr. You may
    also prefix the command with "!" to run "pipe". """
        import proctools
        argv = globargv(argv)
        proc = proctools.spawnpipe(" ".join(argv))
        text = proc.read()
        self._print(text)
        proc.close()
        return proc.wait()

    def spawn(self, argv):
        """spawn <command>...
    Spawn another process (uses a pty). You may also prefix the command
    with "%" to run spawn."""
        import proctools
        argv = globargv(argv)
        proc = proctools.spawnpty(" ".join(argv))
        cmd = self.clone(FileCLI)
        cmd._setup(proc, "Process:%s> " % (proc.cmdline.split()[0],))
        raise NewCommand, cmd

    def help(self, argv):
        """help [-lLcia] [<commandname>]...
    Print a list of available commands, or information about a command,
    if the name is given.  Options:
        -l Shows only local (object specific) commands.
        -c Shows only the dynamic commands.
        -L shows only local and dynamic commands.
        -i Shows only the inherited commands from the parent context.
        -a Shows all commands (default)
        """
        local=True ; created=True ; inherited=True
        opts, longs, args = self.getopt(argv, "lLcia")
        for opt, optarg in opts:
            if opt =="-i":
                local=False ; created=False ; inherited=True
            elif opt == "-c":
                local=False ; created=True ; inherited=False
            elif opt == "-l":
                local=True ; created=False ; inherited=False
            elif opt == "-a":
                local=True ; created=True ; inherited=True
            elif opt == "-L":
                local=True ; created=True ; inherited=False
        if not args:
            args = self.get_commands()
        for name in args:
            try:
                doc = getattr(self, name).__doc__
            except AttributeError:
                self._print("No command named %r found." % (name,))
                continue
            if not doc:
                self._print("No docs for %r." % (name,))
            elif local and self.__class__.__dict__.has_key(name):
                self._ui.help_local(doc)
            elif created and "*" in doc: # dynamic method from generic_cli
                self._ui.help_created(doc)
            elif inherited:
                self._ui.help_inherited(doc)

    def unalias(self, argv):
        """unalias <alias>
    Remove the named alias from the alias list."""
        if len(argv) < 2:
            self._print(self.unalias.__doc__)
            return
        try:
            del self._aliases[argv[1]]
        except:
            self._print("unalias: %s: not found" % argv[1])

    def alias(self, argv):
        """alias [newalias]
    With no argument prints the current set of aliases. With an argument of the
    form alias ..., sets a new alias.  """
        if len(argv) == 1:
            for name, val in self._aliases.items():
                self._print("alias %s='%s'" % (name, " ".join(val)))
            return 0
        elif len(argv) == 2 and '=' not in argv[1]:
            name = argv[1]
            try:
                self._print("%s=%s" % (name, " ".join(self._aliases[name])))
            except KeyError:
                self._print("undefined alias.")
            return 0
        # else
        try: # this icky code to handle different permutations of where the '=' is.
            argv.pop(0) # discard 'alias'
            name = argv.pop(0)
            if "=" in name:
                name, rh = name.split("=", 1)
                argv.insert(0,rh)
            elif argv[0].startswith("="):
                if len(argv[0]) > 1: # if argv[1] is '=something'
                    argv[0] = argv[0][1:]
                else:
                    del argv[0] # remove the '='
            self._aliases[name] = argv
        except:
            ex, val = sys.exc_info()[:2]
            self._print("alias: Could not set alias. Usage: alias name=value")
            self._print("%s (%s)" % (ex, val))
            return 1

    def sleep(self, argv):
        """sleep <secs>
    Sleeps for <secs> seconds."""
        secs = int(argv[1])
        timer.sleep(secs)
    delay = sleep # alias

    def stty(self, argv):
        """stty <args>
    Sets or clears tty flags. May also use "clear", "reset", "sane". """
        self._print(tty.stty(self._ui._io.fileno(), *tuple(argv[1:])))

    def repeat(self, argv):
        """repeat <interval> <command> [<args>...]
    Repeats a command every <interval> seconds. If <interval> is zero then
    loop forever (or until interrupted). If <interval> is negative then loop
    with a count of the absolute value of <interval>."""
        if self._repeater:
            self._print("Repeat command already defined. Run 'stop' first.")
            return
        argv.pop(0) # eat name
        interval = int(argv.pop(0))
        argv = self._expand_aliases(argv)
        meth = getattr(self, argv[0])
        if interval > 0:
            wr = _RepeatWrapper(self._ui._io, meth, (argv,))
            self._repeater = timer.add(interval, 0, wr, repeat=1)
        elif interval == 0:
            try:
                while 1:
                    apply(meth, (argv,))
                    # OOO cheat a little. This is need to keep PagedIO
                    # from asking to press a key.
                    self._ui._io.read(0)
            except KeyboardInterrupt:
                pass
        else:
            for i in xrange(-interval):
                apply(meth, (argv,))

    def cycle(self, argv):
        """cycle <range> <command> [<arg>...]
    Cycle the % variable through range, and re-evaluate the command for
    each value.
    Range is of the form [start':']end[':' step]
      Where start defaults to zero and step defaults to one.
    Or, range is a list of values separated by ','."""
        argv.pop(0) # eat name
        rangetoken = argv.pop(0)
        argv = self._expand_aliases(argv)
        meth = getattr(self, argv[0])
        for sloc, arg in enumerate(argv):
            if arg.find("%") >= 0:
                break
        else:
            self._ui.error("No %% substitution found.")
            return
        try:
            therange = self._parse_range(rangetoken)
        except ValueError, err:
            raise CLISyntaxError, err
        for i in therange:
            newargs = argv[:]
            newargs[sloc] = newargs[sloc].replace("%", str(i))
            self._ui.Print(" ".join(newargs))
            apply(meth, (newargs,))

    def stop(self, argv):
        """stop
    Stops a repeating command."""
        if self._repeater:
            timer.remove(self._repeater)
            self._repeater = None

    def schedule(self, argv):
        """schedule <delay> <command> [<args>...]
    Schedules a command to run <delay> seconds from now."""
        argv.pop(0) # eat name
        delay = int(argv.pop(0))
        argv = self._expand_aliases(argv)
        meth = getattr(self, argv[0])
        timer.add(delay, 0, meth, (argv,), repeat=0)

    def time(self, argv):
        """time <command> [<args>...]
    Display the time, in ms, a command takes to run. Result also stored in
    LASTTIME environment variable.  """
        argv.pop(0)
        argv = self._expand_aliases(argv)
        meth = getattr(self, argv[0])
        start = timelib.now()
        rv = apply(meth, (argv,))
        end = timelib.now()
        elapsed = (end-start)*1000.0
        self._environ["LASTTIME"] = elapsed
        self._ui.printf("%%G%.3f ms%%N" % (elapsed,))
        return rv

    def date(self, argv):
        """date [FORMAT]
    Display the current time and date. Optionally supply a format
    string."""
        if len(argv) > 1:
            fmt = " ".join(argv[1:])
            self._ui.Print(timelib.localtimestamp(fmt=fmt))
        else:
            self._ui.Print(timelib.localtimestamp())

    def _parse_range(self, token):
        if token.find(":") >= 0:
            starts, ends = token.split(":", 1)
            if ends.find(":") >= 0:
                ends, steps = ends.split(":")
                return range(int(starts), int(ends), int(steps))
            else:
                return range(int(starts), int(ends))
        else:
            if token.find(",") >= 0:
                return token.split(",")
            else:
                return range(0, int(token))

    def _get_ns(self):
        try:
            name = self._obj.__class__.__name__.lower()
        except:
            name = "object"
        return {name:self._obj, "environ":self._environ}

    # 'hidden' commands (no doc string) follow
    def pyeval(self, argv):
        snippet = " ".join(argv[1:]).strip()+"\n"
        ns = self._get_ns()
        try:
            code = compile(snippet, '<CLI>', 'eval')
            rv = eval(code, globals(), ns)
        except:
            t, v, tb = sys.exc_info()
            self._print('*** %s (%s)' % (t, v))
        else:
            self._print(rv)
            return rv

    def pyexec(self, argv):
        snippet = " ".join(argv[1:]).strip()+"\n"
        ns = self._get_ns()
        try:
            code = compile(snippet, '<CLI>', 'exec')
            exec code in globals(), ns
        except:
            t, v, tb = sys.exc_info()
            self._print('*** %s (%s)' % (t, v))

    def python(self, argv):
        import code
        ns = self._get_ns()
        console = code.InteractiveConsole(ns)
        console.raw_input = self._ui.user_input
        try:
            saveps1, saveps2 = sys.ps1, sys.ps2
        except AttributeError:
            saveps1, saveps2 = ">>> ", "... "
        sys.ps1, sys.ps2 = "%%GPython%%N:%s> " % (self._obj.__class__.__name__,), "more> "
        if readline:
            oc = readline.get_completer()
            readline.set_completer(Completer(ns).complete)
        console.interact("You are now in Python. ^D exits.")
        if readline:
            readline.set_completer(oc)
        sys.ps1, sys.ps2 = saveps1, saveps2
        self._reset_scopes()


# This is needed to reset PagedIO so background events don't cause the pager to activate.
class _RepeatWrapper(object):
    def __init__(self, io, meth, args):
        self.io = io
        self.meth = meth
        self.args = args
    def __call__(self):
        apply(self.meth, self.args)
        self.io.read(0) 

def globargv(argv):
    if len(argv) > 2:
        import glob
        l = []
        map(lambda gl: l.extend(gl), map(lambda arg: glob.has_magic(arg) and glob.glob(arg) or [arg], argv[2:]))
        argv = argv[0:2] + l
    return argv[1:]

# TODO: should be able to specify value's object type
def breakout_args(argv, namespace=None):
    """convert a list of string arguments (with possible keyword=arg pairs) to
    the most likely objects."""
    args = []
    kwargs = {}
    if namespace:
        assert isinstance(namespace, dict), "namespace must be dict"
        pass
    else:
        namespace = locals()
    for argv_arg in argv:
        if argv_arg.find("=") > 0:
            [kw, kwarg] = argv_arg.split("=")
            kwargs[kw.strip()] = _convert(kwarg, namespace)
        else:
            args.append(_convert(argv_arg, namespace))
    return tuple(args), kwargs

def _convert(val, namespace):
    try:
        return eval(val, globals(), namespace)
    except:
        return val

# public "safe" evaluator
def clieval(val):
    try:
        return eval(val)
    except:
        return val # just assume some string otherwise

###### Specialized, but generally useful, command sets follow

class DictCLI(BaseCommands):
    """Wrap a dictionary-like object and edit it."""
    def initialize(self):
        self._environ["PS1"] = "Dict> "

    def _reset_scopes(self):
        names = map(str, self._obj.keys())
        self.add_completion_scope("get", names)
        self.add_completion_scope("set", names)
        self.add_completion_scope("pop", names)
        self.add_completion_scope("delete", names)
    
    def set(self, argv):
        """set [-t <type>] <name> <value>
    Set the mapping key to value. Specify a type of the value with the -t
    option. If not provided the value is simply evaluated."""
        t = clieval
        optlist, longoptdict, args = self.getopt(argv, "t:")
        name = args[0]
        for opt, optarg in optlist:
            if opt == "-t":
                t = eval(optarg, globals(), globals())
                assert type(t) is type, "Argument to -t is not a type"
        value = t(*tuple(args[1:]))
        self._obj[name] = value
        self._reset_scopes()

    def get(self, argv):
        """get <key>
    Gets and prints the named value."""
        args, kwargs = breakout_args(argv[1:])
        key = args[0]
        v = self._obj.get(key)
        self._print(v)
        return v

    def delete(self, argv):
        """delete <key>
    Deletes the given key from the mapping."""
        key = argv[1]
        del self._obj[key]
        self._reset_scopes()

    def clear(self, argv):
        """clear
    Clears the mapping."""
        self._obj.clear()
        self._reset_scopes()
    
    def has_key(self, argv):
        """has_key <key>
    Report whether or not the mapping has the given key."""
        args, kwargs = breakout_args(argv[1:])
        key = args[0]
        if self._obj.has_key(key):
            self._print("Mapping does contain the key %r." % (key,))
            return True
        else:
            self._print("Mapping does NOT contain the key %r." % (key,))
            return False

    def keys(self, argv):
        """keys
    Show all mapping keys."""
        keys = self._obj.keys()
        self._print_list(map(repr, keys))
        return keys

    def values(self, argv):
        """values
    Show all mapping values."""
        vals = self._obj.values()
        self._print_list(vals)
        return vals

    def items(self, argv):
        """items
    Show mapping items."""
        for name, val in self._obj.items():
            self._print("%25.25r: %s" % (name, safe_repr(val)))
        
    def pop(self, argv):
        """pop <key>
    Pops the given key from the mapping."""
        args, kwargs = breakout_args(argv[1:])
        key = args[0]
        obj = self._obj.pop(key)
        self._print("Popped: ", repr(obj))
        self._reset_scopes()
        return obj
    
    def length(self, argv):
        """length
    Display the length of this mapping object."""
        self._print(len(self._obj))

class ListCLI(BaseCommands):
    """Wrap a list-like object and edit it."""
    def initialize(self):
        self._environ["PS1"] = "List> "
    
    def show(self, argv):
        """show
    Display list contents."""
        for i, obj in enumerate(self._obj):
            self._print("%5.5s: %s" % (i, safe_repr(obj)))
    ls = show

    def set(self, argv):
        """set [-t <type>] <i> <value>
    Set the list index to value. Specify a type of the value with the -t
    option. If not provided the value is simply evaluated."""
        t = clieval
        optlist, longoptdict, args = self.getopt(argv, "t:")
        i = args[0]
        for opt, optarg in optlist:
            if opt == "-t":
                t = eval(optarg, globals(), globals())
                assert type(t) is type, "Argument to -t is not a type"
        value = t(*tuple(args[1:]))
        self._obj[i] = value

    def append(self, argv):
        """append <object>...
    Append object to end of list.  """
        args, kwargs = breakout_args(argv[1:])
        for arg in args:
            self.obj.append(arg)

    def count(self, argv):
        """count <object>
    Show number of occurences of <object>.  """
        args, kwargs = breakout_args(argv[1:])
        if args:
            c = self._obj.count(args[0])
            self._print(c)
            return c

    def extend(self, argv):
        """extend <object>...
    Extend list by appending elements from the given items."""
        args, kwargs = breakout_args(argv[1:])
        if args:
            self.obj.extend(list(args))

    def index(self, argv):
        """index value [start [stop]]
    Show first index of value.  """
        args, kwargs = breakout_args(argv[1:])
        la = len(args)
        if la >= 3:
            stop = args[2]
        else:
            stop = -1
        if la >= 2:
            start = args[1]
        else:
            start = 0
        i = self._obj.index(args[0], start, stop)
        self._print(i)
        return i

    def insert(self, argv):
        """insert <index> <object>
    Insert object before index."""
        args, kwargs = breakout_args(argv[1:])
        la = len(args)
        if la >= 2:
            obj = args[1]
            i = args[0]
            self._obj.insert(i, obj)

    def pop(self, argv):
        """pop [<index>]
    Remove and print item at index (default last)."""
        args, kwargs = breakout_args(argv[1:])
        la = len(args)
        if la >= 1:
            i = args[0]
        else:
            i = -1
        obj = self._obj.pop(i)
        self._print(obj)
        return obj

    def remove(self, argv):
        """remove <value>
    Remove first occurrence of <value>"""
        args, kwargs = breakout_args(argv[1:])
        if args:
            self._obj.remove(args[0])

    def delete(self, argv):
        """delete <index>
    Remove <index> node."""
        args, kwargs = breakout_args(argv[1:])
        if args:
            del self._obj[args[0]]

    def reverse(self, argv):
        """reverse
    Reverse list, in place."""
        self._obj.reverse()

    def sort(self, argv):
        """sort
    Sort list, in place."""
        self._obj.sort()


### objects for creating quick and dirty (generic) CLI objects that let
#you interact with another object's methods.
class GenericCLI(BaseCommands):
    """GenericCLI() Generic Object editor commands.
Wraps any object and allows inspecting and altering it. Use the
get_generic_cli() factory function to get one of these with extra
methods/commands that correspond to the wrapped objects methods.  """

    def _generic_call(self, argv):
        meth = getattr(self._obj, argv[0])
        args, kwargs = breakout_args(argv[1:], vars(self._obj))
        rv = apply(meth, args, kwargs)
        self._print(rv)
    
    def _reset_scopes(self):
        names = filter(lambda n: not n.startswith("__"), dir(self._obj))
        self.add_completion_scope("show", names)
        self.add_completion_scope("call", [n for n in names if callable(getattr(self._obj, n))])
        self.add_completion_scope("set", names)
        self.add_completion_scope("get", names)
        self.add_completion_scope("delete", names)

    def subshell(self, io, env=None, aliases=None, theme=None):
        cliclass = self.__class__
        newui = UserInterface(io, env or self._environ.copy(), theme)
        aliases = aliases or self._aliases
        cmd  = cliclass(newui, aliases)
        cmd._obj = self._obj
        return cmd

    def call(self, argv):
        """call <name> <arg1>...
    Calls the named method with the following arguments converted to "likely types"."""
        self._generic_call(argv[1:])

    def show(self, argv):
        """show [<name>]
    Shows a named attribute of the object, or the object itself if no argument given."""
        if len(argv) > 1:
            v = getattr(self._obj, argv[1])
            self._print(v)
            return v
        else:
            self._print(self._obj)

    def ls(self, argv):
        """ls
    Display a list of the wrapped objects attributes and their types."""
        d = dir(self._obj)
        s = []
        ms = []
        for name in d:
            if name.startswith("__") or name.startswith("_p_"): # hide class-private and persistence overhead objects.
                continue
            attr = getattr(self._obj, name)
            if type(attr) is MethodType:
                ms.append("%22.22s : %s" % (name, method_repr(attr)))
            else:
                s.append("%22.22s : %r" % (name, attr))
        self._print("Methods:")
        self._print("\n".join(ms))
        self._print("Attributes:")
        self._print("\n".join(s))
        return d
    dir = ls # alias

    def set(self, argv):
        """set [-t <type>] <name> <value>
    Sets the named attribute to a new value. The value will be converted into a
    likely suspect, but you can specify a type with the -t flag.  """
        t = clieval
        optlist, longoptdict, args = self.getopt(argv, "t:")
        name = args[0]
        for opt, optarg in optlist:
            if opt == "-t":
                t = eval(optarg, globals(), vars(self._obj))
                assert type(t) is type, "Argument to -t is not a type"
        value = t(*tuple(args[1:]))
        setattr(self._obj, name, value)
        self._reset_scopes()

    def get(self, argv):
        """get <name>
    Gets and prints the named attribute."""
        name = argv[1]
        v = getattr(self._obj, name)
        self._print(v)
        return v

    def delete(self, argv):
        """delete <name>
    Delete the named attribute."""
        name = argv[1]
        delattr(self._obj, name)
        self._reset_scopes()


# used to interact with file-like objects.
class FileCLI(GenericCLI):
    """Commands for file-like objects."""
    def read(self, argv):
        """read [amt]
    Read <amt> bytes of data."""
        args, kwargs = breakout_args(argv[1:], vars(self._obj))
        data = self._obj.read(*args)
        self._print(data)
        return data

    def write(self, argv):
        """write <data>
    Writes the arguments to the file."""
        writ = self._obj.write(" ".join(argv[1:]))
        writ += self._obj.write("\r")
        self._print("wrote %d bytes." % (writ,))
        return writ

    def interact(self, argv):
        """interact
    Read and write to the file object. Works best with Process objects."""
        io = self._ui._io
        import select
        from errno import EINTR
        escape = chr(29) # ^]
        self._print("\nEntering interactive mode.")
        self._print("Type ^%s to stop interacting." % (chr(ord(escape) | 0x40)))
        # save tty state and set to raw mode
        stdin_fd = io.fileno()
        fo_fd = self._obj.fileno()
        ttystate = tty.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
        while 1:
            try:
                rfd, wfd, xfd = select.select([fo_fd, stdin_fd], [], [])
            except select.error, errno:
                if errno[0] == EINTR:
                    continue
            if fo_fd in rfd:
                try:
                    text = self._obj.read(1)
                except (OSError, EOFError), err:
                    tty.tcsetattr(stdin_fd, tty.TCSAFLUSH, ttystate)
                    self._print( '*** EOF ***' )
                    self._print( err)
                    break
                if text:
                    io.write(text)
                    io.flush()
                else:
                    break
            if stdin_fd in rfd:
                char = io.read(1)
                if char == escape: 
                    break
                else:
                    try:
                        self._obj.write(char)
                    except:
                        tty.tcsetattr(stdin_fd, tty.TCSAFLUSH, ttystate)
                        extype, exvalue, tb = sys.exc_info()
                        io.errlog("%s: %s\n" % (extype, exvalue))
                        tty.setraw(stdin_fd)
        tty.tcsetattr(stdin_fd, tty.TCSAFLUSH, ttystate)

# The object's public interface is defined to be the methods that don't
# have a leading underscore, and do have a docstring.
def _get_methodnames(obj):
    for name in dir(obj):
        if name[0] == "_":
            continue
        obj_obj = getattr(obj, name)
        if type(obj_obj) is MethodType and obj_obj.__doc__:
            yield name


# a completer object for readline and python method. Safer than the stock one (no eval).
class Completer(object):
    def __init__(self, namespace):
        assert type(namespace) is dict, "namespace must be a dict type"
        self.namespace = namespace
        self.globalNamespace = Completer.get_globals()
        self.globalNamespace.extend(map(str, namespace.keys()))
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            self.matches = []
            if "." in text:
                for name, obj in self.namespace.items():
                    for key in dir(obj):
                        if key.startswith("__"):
                            continue
                        lname = "%s.%s" % (name, key)
                        if lname.startswith(text):
                            self.matches.append(lname)
            else:
                for key in self.globalNamespace:
                    if key.startswith(text):
                        self.matches.append(key)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def get_globals():
        import keyword, __builtin__
        rv = keyword.kwlist + dir(__builtin__)
        rv = removedups(rv)
        return rv
    get_globals = staticmethod(get_globals)

    def get_class_members(klass, rv=None):
        if rv is None:
            rv = dir(klass)
        else:
            rv.extend(dir(klass))
        if hasattr(klass, '__bases__'):
            for base in klass.__bases__:
                Completer.get_class_members(base, rv)
        return rv
    get_class_members = staticmethod(get_class_members)

def get_generic_cmd(obj, ui, cliclass=GenericCLI, aliases=None, gbl=None):
    """get a GenericCLI (or other) command set wrapping any class instance
    object. The wrapped objects public methods have CLI command counterparts
    automatically created."""
    import new
    from methodholder import MethodHolder
    cmd = cliclass(ui, aliases)
    if gbl is None:
        gbl = globals()
    hashfilter = {}
    for name in _get_methodnames(obj):
        if hasattr(cmd, name):
            continue # don't override already defined methods
        # all this mess does is introspect the object methods and map it to a CLI
        # object method of the same name, with a docstring showing the attributes
        # and their default values, and the actual code mirroring the
        # _generic_call method in the GenericCLI class.
        else:
            obj_meth = getattr(obj, name)
            if id(obj_meth.im_func) in hashfilter: # filter out aliases
                continue
            else:
                hashfilter[id(obj_meth.im_func)] = True
            mh = MethodHolder(obj_meth)
            doc = "%s  *\n%s" % (mh, obj_meth.__doc__ or "")
            code = cliclass._generic_call.func_code
            nc = new.code(code.co_argcount, code.co_nlocals, code.co_stacksize, 
                code.co_flags, code.co_code, 
                (doc,)+code.co_consts[1:], # replace docstring
                code.co_names, code.co_varnames, code.co_filename, 
                code.co_name, code.co_firstlineno, code.co_lnotab)
            f = new.function(nc, gbl, name)
            m = new.instancemethod(f, cmd, cliclass)
            setattr(cmd, name, m)
    cmd._setup(obj, "Object:%s> " % (obj.__class__.__name__,))
    return cmd

def get_generic_clone(obj, cli, cliclass=GenericCLI, theme=None):
    "Return a generic clone of an existing Command object."
    newui = cli._ui.clone(theme)
    return get_generic_cmd(obj, newui, cliclass, aliases=cli._aliases)

def get_generic_cli(obj, cliclass=GenericCLI, env=None, aliases=None, theme=None, logfile=None, historyfile=None):
    """ get_generic_cli(obj, cliclass=GenericCLI, env=None, aliases=None)
Returns a generic CLI object with command methods mirroring the public
methods in the supplied object.  Ready to interact() with! """
    io = ConsoleIO()
    ui = UserInterface(io, env, theme)
    cmd = get_generic_cmd(obj, ui, cliclass, aliases)
    cmd._export("PS1", "%s> " % (obj.__class__.__name__,))
    cli = CommandParser(cmd, logfile, historyfile)
    return cli

# this class is indended to be wrapped by GenericCLI as a general Python CLI.
# It does nothing but allow GenericCLI to pass through its basic functionality.
class Shell(object):
    """A simple class for testing object wrappers."""
    def __init__(self, *iargs, **ikwargs):
        self.initargs = iargs
        self.initkwargs = ikwargs

    def callme(self, *args, **kwargs):
        Print("args:", args)
        Print("kwargs:", kwargs)

#######

def _reset_readline():
    if readline:
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set horizontal-scroll-mode on")
        readline.parse_and_bind("set page-completions on")
        readline.set_history_length(500)

def get_history_file(obj):
    "Utility to form a useful history file name from an object instance."
    return os.path.join(os.environ["HOME"], ".hist_%s" % (obj.__class__.__name__,))

class CommandParser(object):
    """Reads an IO stream and parses input similar to Bourne shell syntax.
    Calls command methods for each line. Handles readline completer."""
    VARCHARS = r'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_?'
    _SPECIAL = {"r":"\r", "n":"\n", "t":"\t", "b":"\b"}
    def __init__(self, cmdobj=None, logfile=None, historyfile=None):
        self.reset(cmdobj)
        self._logfile = logfile
        if historyfile:
            self._historyfile = os.path.expanduser(os.path.expandvars(str(historyfile)))
        else:
            self._historyfile = None
        self.initialize()
        if readline:
            if self._historyfile:
                try:
                    readline.read_history_file(self._historyfile)
                except:
                    pass

    def _rl_completer(self, text, state):
        if state == 0:
            curr = readline.get_line_buffer()
            b = readline.get_begidx()
            if b == 0:
                complist = self._cmd.get_completion_scope("commands")
            else: # complete based on scope keyed on previous word
                word = curr[:b].split()[-1]
                complist = self._cmd.get_completion_scope(word)
            self._complist = filter(lambda s: s.startswith(text), complist)
        try:
            return self._complist[state]
        except IndexError:
            return None

    def close(self):
        self.reset()

    def __del__(self):
        if readline:
            if self._historyfile:
                try:
                    readline.write_history_file(self._historyfile)
                except:
                    pass

    def reset(self, newcmd=None):
        self._cmds = []
        self._cmd = None
        self.arg_list = []
        self._buf = ""
        if newcmd:
            self.push_command(newcmd)
    
    commands = property(lambda s: s._cmd, None, None)

    def push_command(self, newcmd):
        lvl = int(newcmd._environ.setdefault("SHLVL", 0))
        newcmd._environ["SHLVL"] = lvl+1
        self._cmds.append(newcmd)
        self._cmd = newcmd # current command holder
        cmdlist = newcmd.get_commands()
        newcmd.add_completion_scope("commands", cmdlist )
        newcmd.add_completion_scope("help", cmdlist )

    def pop_command(self, returnval=None):
        cmd = self._cmds.pop()
        cmd.finalize()
        if self._cmds:
            self._cmd = self._cmds[-1]
            if returnval:
                self._cmd.handle_subcommand(returnval)
        else:
            raise CommandQuit, "last command object quit."

    def command_setup(self, obj, prompt=None):
        if self._cmd:
            self._cmd._setup(obj, prompt)

    def parse(self, url):
        import urllib
        fo = urllib.urlopen(url)
        self.parseFile(fo)
        fo.close()

    def parseFile(self, fo):
        data = fo.read(4096)
        while data:
            self.feed(data)
            data = fo.read(4096)

    def interact(self, cmd=None):
        _reset_readline()
        if cmd and isinstance(cmd, BaseCommands):
            self.push_command(cmd)
        if readline:
            oc = readline.get_completer()
            readline.set_completer(self._rl_completer)
        try:
            try:
                while 1:
                    ui = self._cmd._ui
                    try:
                        line = ui.user_input()
                        if not line:
                            continue
                        while self.feed(line+"\n"):
                            line = ui.more_user_input()
                    except EOFError:
                        self._cmd._print()
                        self.pop_command()
            except (CommandQuit, CommandExit): # last command does this
                pass
        finally:
            if readline:
                readline.set_completer(oc)
                if self._historyfile:
                    try:
                        readline.write_history_file(self._historyfile)
                    except:
                        pass

    def feed(self, text):
        if self._logfile:
            self._logfile.write(text)
        text = self._buf + text
        i = 0 
        for c in text:
            i += 1
            try:
                self._fsm.process(c)
                while self._fsm.stack:
                    self._fsm.process(self._fsm.pop())
            except EOFError:
                self.pop_command()
            except CommandQuit:
                val = sys.exc_info()[1]
                self.pop_command(val.value)
            except NewCommand, cmdex:
                self.push_command(cmdex.value)
        if self._fsm.current_state: # non-zero, stuff left
            self._buf = text[i:]
        return self._fsm.current_state

    def initialize(self):
        """initializer.
        
        Responsible for setting self._fsm to a parser FSM implementing the
        CLI syntax.
        """
        f = FSM(0)
        f.arg = ""
        f.add_default_transition(self._error, 0)
        # normally add text to args
        f.add_transition(ANY, 0, self._addtext, 0)
        f.add_transition_list(" \t", 0, self._wordbreak, 0)
        f.add_transition_list(";\n", 0, self._doit, 0)
        # slashes
        f.add_transition("\\", 0, None, 1)
        f.add_transition("\\", 3, None, 6)
        f.add_transition(ANY, 1, self._slashescape, 0)
        f.add_transition(ANY, 6, self._slashescape, 3)
        # vars 
        f.add_transition("$", 0, self._startvar, 7)
        f.add_transition("{", 7, self._vartext, 9)
        f.add_transition_list(self.VARCHARS, 7, self._vartext, 7)
        f.add_transition(ANY, 7, self._endvar, 0)
        f.add_transition("}", 9, self._endvar, 0)
        f.add_transition(ANY, 9, self._vartext, 9)
        # vars in singlequote
        f.add_transition("$", 3, self._startvar, 8)
        f.add_transition("{", 8, self._vartext, 10)
        f.add_transition_list(self.VARCHARS, 8, self._vartext, 8)
        f.add_transition(ANY, 8, self._endvar, 3)
        f.add_transition("}", 10, self._endvar, 3)
        f.add_transition(ANY, 10, self._vartext, 10)

        # single quotes quote all
        f.add_transition("'", 0, None, 2)
        f.add_transition("'", 2, self._singlequote, 0)
        f.add_transition(ANY, 2, self._addtext, 2)
        # double quotes allow embedding word breaks and such
        f.add_transition('"', 0, None, 3)
        f.add_transition('"', 3, self._doublequote, 0)
        f.add_transition(ANY, 3, self._addtext, 3)
        # single-quotes withing double quotes
        f.add_transition("'", 3, None, 5)
        f.add_transition("'", 5, self._singlequote, 3)
        f.add_transition(ANY, 5, self._addtext, 5)
        # back-tick substitution
        f.add_transition("`", 0, None, 12)
        f.add_transition(ANY, 12, self._addtext, 12)
        f.add_transition("`", 12, self._do_backtick, 0)
        self._fsm = f

    def _startvar(self, c, fsm):
        fsm.varname = c

    def _vartext(self, c, fsm):
        fsm.varname += c

    def _endvar(self, c, fsm):
        if c == "}":
            fsm.varname += c
        else:
            fsm.push(c)
        try:
            val = self._cmd._environ.expand(fsm.varname)
        except:
            ex, val, tb = sys.exc_info()
            self._cmd._ui.error("Could not expand variable %r: %s (%s)" % (fsm.varname, ex, val))
        else:
            if val is not None:
                fsm.arg += str(val)

    def _error(self, input_symbol, fsm):
        self._cmd._ui.error('Syntax error: %s\n%r' % (input_symbol, fsm.stack))
        fsm.reset()

    def _addtext(self, c, fsm):
        fsm.arg += c

    def _wordbreak(self, c, fsm):
        if fsm.arg:
            self.arg_list.append(fsm.arg)
            fsm.arg = ''

    def _slashescape(self, c, fsm):
        fsm.arg += CommandParser._SPECIAL.get(c, c)

    def _singlequote(self, c, fsm):
        self.arg_list.append(fsm.arg)
        fsm.arg = ''

    def _doublequote(self, c, fsm):
        self.arg_list.append(fsm.arg)
        fsm.arg = ''

    def _doit(self, c, fsm):
        if fsm.arg:
            self.arg_list.append(fsm.arg)
            fsm.arg = ''
        args = self.arg_list
        self.arg_list = []
        self._cmd(args) # call command object with argv

    def _do_backtick(self, c, fsm):
        if fsm.arg:
            self.arg_list.append(fsm.arg)
            fsm.arg = ''
        io = StringIO()
        sys.stdout.flush()
        sys.stdout = sys.stdin = io
        try:
            subcmd = self._cmd.subshell(io)
            subparser = CommandParser(subcmd, self._logfile)
            try:
                subparser.feed(self.arg_list.pop()+"\n")
            except:
                ex, val, tb = sys.exc_info()
                print >>sys.stderr, "  *** %s (%s)" % (ex, val)
        finally:
            sys.stdout = sys.__stdout__
            sys.stdin = sys.__stdin__
        fsm.arg += io.getvalue().strip()

# get a cli built from sys.argv
def run_cli_wrapper(argv, wrappedclass=Shell, cliclass=GenericCLI, theme=None):
    """Instantiate a class object (the wrappedclass), and run a CLI wrapper on it."""
    import getopt # use standard getopt here
    logfile = sourcefile = None
    paged = False
    try:
        optlist, args = getopt.getopt(argv[1:], "?hgs:", ["help", "script="])
    except getopt.GetoptError:
            print wrappedclass.__doc__
            return
    for opt, val in optlist:
        if opt in ("-?", "-h", "--help"):
            print run_cli_wrapper.__doc__
            return
        elif opt == "-s" or opt == "--script":
            sourcefile = val
        elif opt == "-g":
            paged = True
        elif opt == "-l" or opt == "--logfile":
            logfile = open(val, "w")
    if args:
        targs, kwargs = breakout_args(args)
    else:
        targs, kwargs = (), {}
    try:
        obj = apply(wrappedclass, targs, kwargs)
    except (ValueError, TypeError):
        print "Bad parameters."
        print wrappedclass.__doc__
        return
    if paged:
        io = tty.PagedIO()
    else:
        io = ConsoleIO()
    ui = UserInterface(io, None, theme)
    cmd = get_generic_cmd(obj, ui, cliclass)
    cmd._export("PS1", "%%I%s%%N(%s%s%s)> " % (wrappedclass.__name__,
                ", ".join(map(repr, targs)),  IF(kwargs, ", ", ""),
                ", ".join(map(lambda t: "%s=%r" % t, kwargs.items()))) )
    cli = CommandParser(cmd, logfile)
    if sourcefile:
        cli.parse(sourcefile)
    else:
        cli.interact()


def run_cli(cmdclass, io, env=None, logfile=None, theme=None, historyfile=None):
    ui = UserInterface(io, env, theme)
    cmd = cmdclass(ui)
    parser = CommandParser(cmd, logfile, historyfile)
    parser.interact()

def run_generic_cli(cmdclass=BaseCommands):
    env = environ.Environ()
    env.inherit()
    io = ConsoleIO()
    run_cli(cmdclass, io, env)

# factory for Command classes. Returns a parser.
def get_cli(cmdclass, env=None, aliases=None, logfile=None, paged=False, theme=None, historyfile=None):
    if paged:
        io = tty.PagedIO()
    else:
        io = ConsoleIO()
    ui = UserInterface(io, env, theme)
    cmd = cmdclass(ui, aliases)
    parser = CommandParser(cmd, logfile, historyfile)
    return parser

def get_terminal_ui(env=None, paged=False, theme=None):
    if paged:
        io = tty.PagedIO()
    else:
        io = ConsoleIO()
    return UserInterface(io, env, theme)

def get_ui(ioc=ConsoleIO, uic=UserInterface, themec=DefaultTheme, env=None):
    io = ioc()
    theme = themec()
    return uic(io, env, theme)


#### self test

# models a BaseCommands class, but only prints argv (used to test parser)
class _CmdTest(BaseCommands):

    def __call__(self, argv):
        self._print("argv: ")
        self._print(str(argv))
        self._print("\n")
        return 0


if __name__ == "__main__":
    env = environ.Environ()
    env.inherit()
    io = ConsoleIO()
    #io = tty.PagedIO()
    print "======================="
    run_cli(_CmdTest, io, env)
    print "======================="
    env["PS1"] = "CLItest> "
    ui = UserInterface(io, env, DefaultTheme())
    cmd = BaseCommands(ui)
    cmd = cmd.clone(DictCLI)
    cmd._setup({"testkey":"testvalue"}, "dicttest> ")
    parser = CommandParser(cmd)
    parser.interact()


    f = UserInterface(ConsoleIO(), env, DefaultTheme())
    print f.format("%T %t")
    print f.format("%Ibright%N")

    print f.format("%rred%N")
    print f.format("%ggreen%N")
    print f.format("%yyellow%N")
    print f.format("%bblue%N")
    print f.format("%mmagenta%N")
    print f.format("%ccyan%N")
    print f.format("%wwhite%N")

    print f.format("%Rred%N")
    print f.format("%Ggreen%N")
    print f.format("%Yyellow%N")
    print f.format("%Bblue%N")
    print f.format("%Mmagenta%N")
    print f.format("%Ccyan%N")
    print f.format("%Wwhite%N")

    print f.format("%Ddefault%N")
    print f.format("wrapped%ntext")
    print f.format("%l tty %l")
    print f.format("%h hostname %h")
    print f.format("%u username %u")
    print f.format("%$ priv %$")
    print f.format("%d cwd %d")
    print f.format("%L SHLVL %L")
    print f.format("%{PS4}")

