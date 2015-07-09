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
User Interface base classes and themes.

"""

import sys
import os
import time
from io import BytesIO

from pycopia import environ
from pycopia import cliutils
from pycopia import tty

from pycopia.fsm import FSM, ANY

# set the PROMPT ignore depending on whether or not readline module is
# available.
try:
    import readline
    PROMPT_START_IGNORE = '\001'
    PROMPT_END_IGNORE = '\002'
except ImportError:
    readline = None
    PROMPT_START_IGNORE = ''
    PROMPT_END_IGNORE = ''

from types import MethodType, FunctionType

class UIError(Exception):
    pass

class UIFindError(UIError):
    pass

# themes define some basic "look and feel" for a CLI. This includes prompt
# srtrings and color set.

class Theme(object):
    NORMAL = RESET = ""
    BOLD = BRIGHT = ""
    BLACK = ""
    RED = ""
    GREEN = ""
    YELLOW = ""
    BLUE = ""
    MAGENTA = ""
    CYAN = ""
    WHITE = ""
    DEFAULT = ""
    GREY = ""
    BRIGHTRED = ""
    BRIGHTGREEN = ""
    BRIGHTYELLOW = ""
    BRIGHTBLUE = ""
    BRIGHTMAGENTA = ""
    BRIGHTCYAN = ""
    BRIGHTWHITE = ""
    UNDERSCORE = ""
    BLINK = ""
    help_local = WHITE
    help_inherited = YELLOW
    help_created = GREEN
    def __init__(self, ps1="> ", ps2="more> ", ps3="choose", ps4="-> "):
        self._ps1 = ps1 # main prompt
        self._ps2 = ps2 # more input needed
        self._ps3 = ps3 # choose prompt
        self._ps4 = ps4 # input prompt
        self._setcolors()
    def _set_ps1(self, new):
        self._ps1 = str(new)
    def _set_ps2(self, new):
        self._ps2 = str(new)
    def _set_ps3(self, new):
        self._ps3 = str(new)
    def _set_ps4(self, new):
        self._ps4 = str(new)
    _setcolors = classmethod(lambda c: None)
    ps1 = property(lambda s: s._ps1, _set_ps1, None, "primary prompt")
    ps2 = property(lambda s: s._ps2, _set_ps2, None, "more input needed")
    ps3 = property(lambda s: s._ps3, _set_ps3, None, "choose prompt")
    ps4 = property(lambda s: s._ps4, _set_ps4, None, "text input prompt")

class BasicTheme(Theme):
    def _setcolors(cls):
        "Base class for themes. Defines interface."
        cls.NORMAL = cls.RESET = "\x1b[0m"
        cls.BOLD = cls.BRIGHT = "\x1b[1m"
        cls.BLACK = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.WHITE = ""
        cls.DEFAULT = ""
        cls.GREY = ""
        cls.BRIGHTRED = ""
        cls.BRIGHTGREEN = ""
        cls.BRIGHTYELLOW = ""
        cls.BRIGHTBLUE = ""
        cls.BRIGHTMAGENTA = ""
        cls.BRIGHTCYAN = ""
        cls.BRIGHTWHITE = ""
        cls.UNDERSCORE = "\x1b[4m"
        cls.BLINK = "\x1b[5m"
        cls.help_local = cls.WHITE
        cls.help_inherited = cls.YELLOW
        cls.help_created = cls.GREEN
    _setcolors = classmethod(_setcolors)

class ANSITheme(BasicTheme):
    """Defines tunable parameters for the UserInterface, to provide
    different color schemes and prompts.
    """
    def _setcolors(cls):
        # ANSI escapes for color terminals
        cls.NORMAL = cls.RESET = "\x1b[0m"
        cls.BOLD = cls.BRIGHT = "\x1b[01m"
        cls.BLACK = "\x1b[30m"
        cls.RED = "\x1b[31m"
        cls.GREEN = "\x1b[32m"
        cls.YELLOW = "\x1b[33m"
        cls.BLUE = "\x1b[34m"
        cls.MAGENTA = "\x1b[35m"
        cls.CYAN = "\x1b[36m"
        cls.WHITE = "\x1b[37m"
        cls.GREY = "\x1b[30;01m"
        cls.BRIGHTRED = "\x1b[31;01m"
        cls.BRIGHTGREEN = "\x1b[32;01m"
        cls.BRIGHTYELLOW = "\x1b[33;01m"
        cls.BRIGHTBLUE = "\x1b[34;01m"
        cls.BRIGHTMAGENTA = "\x1b[35;01m"
        cls.BRIGHTCYAN = "\x1b[36;01m"
        cls.BRIGHTWHITE = "\x1b[37;01m"
        cls.DEFAULT = "\x1b[39;49m"
        cls.UNDERSCORE = "\x1b[4m"
        cls.BLINK = "\x1b[5m"
        cls.help_local = cls.BRIGHTWHITE
        cls.help_inherited = cls.YELLOW
        cls.help_created = cls.GREEN
    _setcolors = classmethod(_setcolors)


DefaultTheme = ANSITheme


class UserInterface(object):
    """An ANSI terminal user interface for CLIs.  """
    def __init__(self, io, env=None, theme=None):
        self.set_IO(io)
        self._env = env or environ.Environ()
        assert hasattr(self._env, "get")
        self._env["_"] = None
        self._cache = {}
        self.set_theme(theme)
        self._initfsm()
        self.initialize()

    def set_IO(self, io):
        self._io = io
        if io.isatty():
            self._termlen, self._termwidth, x, y = tty.get_winsize(io.fileno())
        else:
            self._termlen, self._termwidth = 24, 80
    def get_IO(self):
        return self._io
    def _del_IO(self):
        self._io = None
    IO = property(get_IO, set_IO, _del_IO)

    def __del__(self):
        try:
            self.finalize()
        except:
            pass

    def initialize(self, *args):
        pass

    def finalize(self):
        pass

    def close(self):
        if self._io is not None:
            self._io.close()
            self._io = None

    def set_environ(self, env):
        assert hasattr(env, "get")
        self._env = env
        self._env["_"] = None

    def set_theme(self, theme):
        self._theme = theme or DefaultTheme()
        assert isinstance(self._theme, Theme), "must supply a Theme object."
        self._env.setdefault("PS1", self._theme.ps1)
        self._env.setdefault("PS2", self._theme.ps2)
        self._env.setdefault("PS3", self._theme.ps3)
        self._env.setdefault("PS4", self._theme.ps4)

    def clone(self, theme=None):
        return self.__class__(self._io, self._env.copy(), theme or self._theme)

    # output methods
    def Print(self, *objs):
        wr = self._io.write
        if objs:
            try:
                for obj in objs[:-1]:
                    wr(str(obj))
                    wr(" ")
                last = objs[-1]
                if last is not None: # don't NL if last value is None (works like trailing comma).
                    wr(str(last))
                    wr("\n")
            except tty.PageQuitError:
                return
        else:
            wr("\n")
        self._io.flush()

    def pprint(self, obj):
        self._format(obj, 0, 0, set(), 0)
        self._io.write("\n")
        self._io.flush()

    def print_obj(self, obj, nl=1):
        if nl:
            self._io.write("%s\n" % (obj,))
        else:
            self._io.write(str(obj))
        self._io.flush()

    def print_list(self, clist, indent=0):
        if clist:
            width = self._termwidth - 9
            indent = min(max(indent,0),width)
            ps = " " * indent
            try:
                for c in clist[:-1]:
                    cs = "%s, " % (c,)
                    if len(ps) + len(cs) > width:
                        self.print_obj(ps)
                        ps = "%s%s" % (" " * indent, cs)
                    else:
                        ps += cs
                self.print_obj("%s%s" % (ps, clist[-1]))
            except tty.PageQuitError:
                pass

    def write(self, text):
        self._io.write(text)

    def printf(self, text):
        "Print text run through the expansion formatter."
        self.Print(self.format(text))

    def error(self, text):
        self.printf("%%r%s%%N" % (text,))

    def warning(self, text):
        self.printf("%%Y%s%%N" % (text,))

    # user input
    def _get_prompt(self, name, prompt=None):
        return self.prompt_format(prompt or self._env[name])

    def user_input(self, prompt=None):
        return self._io.raw_input(self._get_prompt("PS1", prompt))

    def more_user_input(self):
        return self._io.raw_input(self._get_prompt("PS2"))

    def choose(self, somelist, defidx=0, prompt=None):
        return cliutils.choose(somelist,
                    defidx,
                    self._get_prompt("PS3", prompt),
                    input=self._io.raw_input, error=self.error)

    def choose_value(self, somemap, default=None, prompt=None):
        return cliutils.choose_value(somemap,
                    default,
                    self._get_prompt("PS3", prompt),
                    input=self._io.raw_input, error=self.error)

    def choose_key(self, somemap, default=None, prompt=None):
        return cliutils.choose_key(somemap,
                    default,
                    self._get_prompt("PS3", prompt),
                    input=self._io.raw_input, error=self.error)

    def choose_multiple(self, somelist, chosen=None, prompt=None):
        return cliutils.choose_multiple(somelist,
                    chosen,
                    self._get_prompt("PS3", prompt),
                    input=self._io.raw_input, error=self.error)

    def choose_multiple_from_map(self, somemap, chosen=None, prompt=None):
        return cliutils.choose_multiple_from_map(somemap,
                    chosen,
                    self._get_prompt("PS3", prompt),
                    input=self._io.raw_input, error=self.error)

    def get_text(self, msg=None):
        return cliutils.get_text(self._get_prompt("PS4"), msg, input=self._io.raw_input)

    def get_value(self, prompt, default=None):
        return cliutils.get_input(self.prompt_format(prompt), default, self._io.raw_input)

    def edit_text(self, text, prompt=None):
        return cliutils.edit_text(text, self._get_prompt("PS4", prompt))

    def get_int(self, prompt="", default=None):
        return cliutils.get_int(prompt, default, input=self._io.raw_input, error=self.error)

    def get_float(self, prompt="", default=None):
        return cliutils.get_float(prompt, default, input=self._io.raw_input, error=self.error)

    def get_bool(self, prompt="", default=None):
        return cliutils.get_bool(prompt, default, input=self._io.raw_input, error=self.error)

    def yes_no(self, prompt, default=True):
        while 1:
            yesno = cliutils.get_input(self.prompt_format(prompt), "Y" if default else "N", self._io.raw_input)
            yesno = yesno.upper()
            if yesno.startswith("Y"):
                return True
            elif yesno.startswith("N"):
                return False
            else:
                self.Print("Please enter yes or no.")

    def get_key(self, prompt=""):
        return tty.get_key(prompt)

    def get_password(self, prompt="Password: "):
        return tty.getpass(prompt)

    def get_winsize(self):
        rows, cols, xpixel, ypixel = tty.get_winsize(self._io.fileno())
        return rows, cols

    # docstring/help formatters
    def _format_doc(self, s, color):
        i = s.find("\n")
        if i > 0:
            return color + s[:i] + self._theme.NORMAL + self.format(s[i:]) + "\n"
        else:
            return color + s + self._theme.NORMAL + "\n"

    def help_local(self, text):
        self.Print(self._format_doc(text, self._theme.help_local))

    def help_inherited(self, text):
        self.Print(self._format_doc(text, self._theme.help_inherited))

    def help_created(self, text):
        self.Print(self._format_doc(text, self._theme.help_created))

    def prompt_format(self, ps):
        "Expand percent-exansions in a string for readline prompts."
        self._fsm.process_string(ps)
        return self._getarg()

    def format(self, ps):
        "Expand percent-exansions in a string and return the result."
        self._ffsm.process_string(ps)
        if self._ffsm.arg:
            arg = self._ffsm.arg
            self._ffsm.arg = ''
            return arg
        else:
            return None

    def format_wrap(self, obj, formatstring):
        return FormatWrapper(obj, self, formatstring)

    def register_prompt_expansion(self, key, func):
        """Register a percent-expansion function for the prompt format method. The
        function must take one argument, and return a string. The argument is
        the character expanded on.
        """
        key = str(key)[0]
        if not key in self._PROMPT_EXPANSIONS:
            self._PROMPT_EXPANSIONS[key] = func
        else:
            raise ValueError("expansion key %r already exists." % (key, ))

    def register_format_expansion(self, key, func):
        """Register a percent-expansion function for the format method. The
        function must take one argument, and return a string. The argument is
        the character expanded on.
        """
        key = str(key)[0]
        if key not in self._FORMAT_EXPANSIONS:
            self._FORMAT_EXPANSIONS[key] = func
        else:
            raise ValueError("expansion key %r already exists." % (key, ))

    def unregister_format_expansion(self, key):
        key = str(key)[0]
        try:
            del self._FORMAT_EXPANSIONS[key]
        except KeyError:
            pass

    # FSM for prompt expansion
    def _initfsm(self):
        # maps percent-expansion items to some value.
        theme = self._theme
        self._PROMPT_EXPANSIONS = { # used in prompt strings given to readline library.
                    "I":PROMPT_START_IGNORE + theme.BRIGHT + PROMPT_END_IGNORE,
                    "N":PROMPT_START_IGNORE + theme.NORMAL + PROMPT_END_IGNORE,
                    "D":PROMPT_START_IGNORE + theme.DEFAULT + PROMPT_END_IGNORE,
                    "R":PROMPT_START_IGNORE + theme.BRIGHTRED + PROMPT_END_IGNORE,
                    "G":PROMPT_START_IGNORE + theme.BRIGHTGREEN + PROMPT_END_IGNORE,
                    "Y":PROMPT_START_IGNORE + theme.BRIGHTYELLOW + PROMPT_END_IGNORE,
                    "B":PROMPT_START_IGNORE + theme.BRIGHTBLUE + PROMPT_END_IGNORE,
                    "M":PROMPT_START_IGNORE + theme.BRIGHTMAGENTA + PROMPT_END_IGNORE,
                    "C":PROMPT_START_IGNORE + theme.BRIGHTCYAN + PROMPT_END_IGNORE,
                    "W":PROMPT_START_IGNORE + theme.BRIGHTWHITE + PROMPT_END_IGNORE,
                    "r":PROMPT_START_IGNORE + theme.RED + PROMPT_END_IGNORE,
                    "g":PROMPT_START_IGNORE + theme.GREEN + PROMPT_END_IGNORE,
                    "y":PROMPT_START_IGNORE + theme.YELLOW + PROMPT_END_IGNORE,
                    "b":PROMPT_START_IGNORE + theme.BLUE + PROMPT_END_IGNORE,
                    "m":PROMPT_START_IGNORE + theme.MAGENTA + PROMPT_END_IGNORE,
                    "c":PROMPT_START_IGNORE + theme.CYAN + PROMPT_END_IGNORE,
                    "w":PROMPT_START_IGNORE + theme.WHITE + PROMPT_END_IGNORE,
                    "n":"\n", "l":self._tty, "h":self._hostname, "u":self._username,
                    "$": self._priv, "d":self._cwd, "L": self._shlvl, "t":self._time,
                    "T":self._date}
        self._FORMAT_EXPANSIONS = {
                    "I": theme.BRIGHT,
                    "N": theme.NORMAL,
                    "D": theme.DEFAULT,
                    "R": theme.BRIGHTRED,
                    "G": theme.BRIGHTGREEN,
                    "Y": theme.BRIGHTYELLOW,
                    "B": theme.BRIGHTBLUE,
                    "M": theme.BRIGHTMAGENTA,
                    "C": theme.BRIGHTCYAN,
                    "W": theme.BRIGHTWHITE,
                    "r": theme.RED,
                    "g": theme.GREEN,
                    "y": theme.YELLOW,
                    "b": theme.BLUE,
                    "m": theme.MAGENTA,
                    "c": theme.CYAN,
                    "w": theme.WHITE,
                    "n":"\n", "l":self._tty, "h":self._hostname, "u":self._username,
                    "$": self._priv, "d":self._cwd, "L": self._shlvl, "t":self._time,
                    "T":self._date}

        fp = FSM(0)
        fp.add_default_transition(self._error, 0)
        # add text to args
        fp.add_transition(ANY, 0, self._addtext, 0)
        # percent escapes
        fp.add_transition("%", 0, None, 1)
        fp.add_transition("%", 1, self._addtext, 0)
        fp.add_transition("{", 1, self._startvar, 2)
        fp.add_transition("}", 2, self._endvar, 0)
        fp.add_transition(ANY, 2, self._vartext, 2)
        fp.add_transition(ANY, 1, self._prompt_expand, 0)
        fp.arg = ''
        self._fsm = fp

        ff = FSM(0)
        ff.add_default_transition(self._error, 0)
        # add text to args
        ff.add_transition(ANY, 0, self._addtext, 0)
        # percent escapes
        ff.add_transition("%", 0, None, 1)
        ff.add_transition("%", 1, self._addtext, 0)
        ff.add_transition("{", 1, self._startvar, 2)
        ff.add_transition("}", 2, self._endvar, 0)
        ff.add_transition(ANY, 2, self._vartext, 2)
        ff.add_transition(ANY, 1, self._format_expand, 0)
        ff.arg = ''
        self._ffsm = ff

    def _startvar(self, c, fsm):
        fsm.varname = ""

    def _vartext(self, c, fsm):
        fsm.varname += c

    def _endvar(self, c, fsm):
        fsm.arg += str(self._env.get(fsm.varname, fsm.varname))

    def _prompt_expand(self, c, fsm):
        return self._expand(c, fsm, self._PROMPT_EXPANSIONS)

    def _format_expand(self, c, fsm):
        return self._expand(c, fsm, self._FORMAT_EXPANSIONS)

    def _expand(self, c, fsm, mapping):
        try:
            arg = self._cache[c]
        except KeyError:
            try:
                arg = mapping[c]
            except KeyError:
                arg = c
            else:
                if callable(arg):
                    arg = str(arg(c))
        fsm.arg += arg

    def _username(self, c):
        un = os.environ.get("USERNAME") or os.environ.get("USER")
        if un:
            self._cache[c] = un
        return un

    def _shlvl(self, c):
        return str(self._env.get("SHLVL", ""))

    def _hostname(self, c):
        hn = os.uname()[1]
        self._cache[c] = hn
        return hn

    def _priv(self, c):
        if os.getuid() == 0:
            arg = "#"
        else:
            arg = ">"
        self._cache[c] = arg
        return arg

    def _tty(self, c):
        n = os.ttyname(self._io.fileno())
        self._cache[c] = n
        return n

    def _cwd(self, c):
        return os.getcwd()

    def _time(self, c):
        return time.strftime("%H:%M:%S", time.localtime())

    def _date(self, c):
        return time.strftime("%m/%d/%Y", time.localtime())

    def _error(self, input_symbol, fsm):
        self._io.errlog('Prompt string error: %s\n%r' % (input_symbol, fsm.stack))
        fsm.reset()

    def _addtext(self, c, fsm):
        fsm.arg += c

    def _getarg(self):
        if self._fsm.arg:
            arg = self._fsm.arg
            self._fsm.arg = ''
            return arg
        else:
            return None

    # pretty printing
    def _format(self, obj, indent, allowance, context, level):
        level = level + 1
        objid = id(obj)
        if objid in context:
            self._io.write(_recursion(obj))
            return
        rep = self._repr(obj, context, level - 1)
        typ = type(obj)
        sep_lines = len(rep) > (self._termwidth - 1 - indent - allowance)
        write = self._io.write

        if sep_lines:
            if typ is dict:
                write('{\n  ')
                length = len(obj)
                if length:
                    context[objid] = 1
                    indent = indent + 2
                    items  = obj.items()
                    items.sort()
                    key, ent = items[0]
                    rep = self._repr(key, context, level)
                    write(rep)
                    write(': ')
                    self._format(ent, indent + len(rep) + 2, allowance + 1, context, level)
                    if length > 1:
                        for key, ent in items[1:]:
                            rep = self._repr(key, context, level)
                            write(',\n%s%s: ' % (' '*indent, rep))
                            self._format(ent, indent + len(rep) + 2, allowance + 1, context, level)
                    indent = indent - 2
                    del context[objid]
                write('\n}')
                return

            if typ is list:
                write('[\n')
                self.print_list(obj, 2)
                write(']')
                return

            if typ is tuple:
                write('(\n')
                self.print_list(obj, 2)
                if len(obj) == 1:
                    write(',')
                write(')')
                return

        write(rep)

    def _repr(self, obj, context, level):
        return self._safe_repr(obj, context.copy(), None, level)

    def _safe_repr(self, obj, context, maxlevels, level):
        return _safe_repr(obj, context, maxlevels, level)


class FormatWrapper(object):
    """Wrap any object with a format. 

    The format string should have an '%O' component that will be expanded to
    the stringified object given here.
    """
    def __init__(self, obj, ui, format):
        self.value = obj
        self._ui = ui
        self._format = format

    def __str__(self):
        self._ui.register_format_expansion("O", self._str_value)
        try:
            return self._ui.format(self._format)
        finally:
            self._ui.unregister_format_expansion("O")

    def _str_value(self, c):
        return str(self.value)

    def __len__(self):
        return len(str(self.value))

    def __repr__(self):
        return _safe_repr(self.value, set(), None, 0)

    def __cmp__(self, other):
        if type(other) is FormatWrapper:
            return cmp(self.value, other.value)
        else:
            return cmp(self.value, other)


def safe_repr(value):
    """Return a representational string of the given object. 

    Large or recursive objects or detected and clipped.
    """
    return _safe_repr(value, set(), None, 0)

# Return repr_string
def _safe_repr(obj, context, maxlevels, level):
    typ = type(obj)
    if typ is str:
        if 'locale' not in sys.modules:
            return repr(obj)
        if "'" in obj and '"' not in obj:
            closure = '"'
            quotes = {'"': '\\"'}
        else:
            closure = "'"
            quotes = {"'": "\\'"}
        qget = quotes.get
        sio = BytesIO()
        write = sio.write
        for char in obj:
            if char.isalpha():
                write(char)
            else:
                write(qget(char, repr(char)[1:-1]))
        return ("%s%s%s" % (closure, sio.getvalue(), closure))

    if typ is dict:
        if not obj:
            return "{}"
        objid = id(obj)
        if maxlevels and level > maxlevels:
            return "{...}"
        if objid in context:
            return _recursion(obj)
        context[objid] = 1
        components = []
        append = components.append
        level += 1
        saferepr = _safe_repr
        for k, v in obj.iteritems():
            krepr = saferepr(k, context, maxlevels, level)
            vrepr = saferepr(v, context, maxlevels, level)
            append("%s: %s" % (krepr, vrepr))
        del context[objid]
        return "{%s}" % ", ".join(components)

    if typ is list or typ is tuple:
        if typ is list:
            if not obj:
                return "[]"
            format = "[%s]"
        elif len(obj) == 1:
            format = "(%s,)"
        else:
            if not obj:
                return "()"
            format = "(%s)"
        objid = id(obj)
        if maxlevels and level > maxlevels:
            return format % "..."
        if objid in context:
            return _recursion(obj)
        context[objid] = 1
        components = []
        append = components.append
        level += 1
        for o in obj:
            orepr = _safe_repr(o, context, maxlevels, level)
            append(orepr)
        del context[objid]
        return format % ", ".join(components)

    if typ is MethodType:
        return method_repr(obj)

    if typ is FunctionType:
        return function_repr(obj)

    return repr(obj)

def _recursion(obj):
    return ("<Recursion on %s with id=%s>" % (type(obj).__name__, id(obj)))

def method_repr(method):
    methname = method.im_func.func_name
    # formal names
    varnames = list(method.im_func.func_code.co_varnames)[:method.im_func.func_code.co_argcount]
    if method.im_func.func_defaults:
        ld = len(method.im_func.func_defaults)
        varlist = [", ".join(varnames[:-ld]),
                   ", ".join(["%s=%r" % (n, v) for n, v in zip(varnames[-ld:], method.im_func.func_defaults)])]
        return "%s(%s)" % (methname, ", ".join(varlist))
    else:
        return "%s(%s)" % (methname, ", ".join(varnames))

def function_repr(func):
    methname = func.func_name
    # formal names
    argcount = func.func_code.co_argcount
    varnames = list(func.func_code.co_varnames)[:argcount]
    if func.func_defaults:
        ld = len(func.func_defaults)
        varlist = varnames[:-ld]
        varlist.extend(["%s=%r" % (n, v) for n, v in zip(varnames[-ld:], func.func_defaults)])
        return "%s(%s)" % (methname, ", ".join(varlist))
    else:
        return "%s(%s)" % (methname, ", ".join(varnames))


def _get_object(name):
    try:
        return getattr(sys.modules[__name__], name)
    except AttributeError:
        i = name.rfind(".")
        if i >= 0:
            modname = name[:i]
            try:
                mod = sys.modules[modname]
            except KeyError:
                try:
                    mod = __import__(modname, globals(), locals(), ["*"])
                except ImportError as err:
                    raise UIFindError("Could not find UI module %s: %s" % (modname, err))
            try:
                return getattr(mod, name[i+1:])
            except AttributeError:
                raise UIFindError("Could not find UI object %r in module %r." % (name, modname))
        else:
            raise UIFindError("%s is not a valid object path." % (name,))

# construct a user interface from object names given as strings.
def get_userinterface(uiname="UserInterface",
                ioname="IO.ConsoleIO", themename=None):
    if type(ioname) is str:
        ioobj = _get_object(ioname)
    elif hasattr(ioname, "write"):
        ioobj = ioname
    else:
        raise ValueError("ioname not a valid type")
    if not hasattr(ioobj, "close"):
        raise UIFindError("not a valid IO object: %r" % (ioobj,))

    uiobj = _get_object(uiname)
    if not hasattr(uiobj, "Print"):
        raise UIFindError("not a valid UI object: %r" % (uiobj,))
    if themename is not None:
        themeobj = _get_object(themename)
        if not issubclass(themeobj, Theme):
            raise UIFindError("not a valid Theme object: %r." % (themeobj,))
        return uiobj(ioobj(), theme=themeobj())
    else:
        return uiobj(ioobj())

def _test(argv):
    ui = get_userinterface()
    ui.Print("Hello world!")
    inp = ui.user_input("Type something> ")
    ui.Print("You typed:", inp)
    return ui

if __name__ == "__main__":
    ui = _test(sys.argv)

