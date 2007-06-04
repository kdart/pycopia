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
IO module for use with the CLI framework that uses the curses library for IO.

XXX not finished.

"""

__all__ = ['BasicCursesIO', 'CursesIO', 'CursesTheme', 'UserInterface',
'get_text', 'get_input', 'choose', 'yes_no', 'print_menu_list',
'get_curses_ui']

import sys, os
from curses import *

from pycopia import environ
from pycopia.fsm import FSM, ANY
from pycopia import tty
from pycopia import UI
from pycopia.aid import IF

import curses.textpad
import curses.panel


class BasicCursesIO(object):
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        # reading methods
        self.read = self.stdin.read
        self.readline = self.stdin.readline
        self.readlines = self.stdin.readlines
        self.xreadlines = self.stdin.xreadlines
        # writing methods
        self.write = self.stdout.write
        self.flush = self.stdout.flush
        self.writelines = self.stdout.writelines
        self.set_size(inputsize)
    
    def set_win(self, win, inputsize=6):
        ass

    def raw_input(self, prompt=""):
        return raw_input(prompt)

    def __del__(self):
        if not self.closed:
            self.close()

    def close(self):
        if not self.closed:
            self.stdout = None
            self.stdin = None
            self.closed = 1
            del self.read, self.readlines, self.xreadlines, self.write
            del self.flush, self.writelines

    def fileno(self):
        return self.stdout.fileno()

    def isatty(self):
        return self.stdin.isatty() and self.stdout.isatty()

    def errlog(self, text):
        self.stderr.write("%s\n" % (text,))
        self.stderr.flush()

    def set_size(self, insize=6):
        self.rows, self.cols, x, y = tty.get_winsize(self.stdout.fileno())


class CursesIO(object):
    def __init__(self, errfile=sys.stderr):
        self.mode = "rw"
        self.closed = 0
        self.softspace = 0
        self.stderr = errfile
        self._win = None

    def set_win(self, win, inputsize=7):
        self._win = win
        self.set_size(inputsize)

    def _init_outwin(self, insize):
        self._outwin = self._win.subwin(self.rows-insize, self.cols, 0, 0)
        self._outwin.scrollok(1)
        self._outwin.idlok(1)

    def _init_inwin(self, insize):
        self._inwinborder = self._win.subwin(insize, self.cols, self.rows-insize, 0)
        self._inwinborder.box()
        self._inwin = self._win.subwin(insize-2, self.cols-2, self.rows-insize+2, 2)
        self._inwin.scrollok(0)
        self._inwin.idlok(0)

    def set_size(self, insize=7):
        self.rows, self.cols = self._win.getmaxyx()
        self._win.setscrreg(0, self.rows-insize)
        self._init_outwin(insize)
        self._init_inwin(insize)

    outputwin = property(lambda s: s._outwin)
    inputwin = property(lambda s: s._inwin)
    root = property(lambda s: curses.panel.new_panel(s._outwin))

    def __del__(self):
        self.close()

    # delegate to main output window
    def __getattr__(self, key):
        return getattr(self._outwin, key)

    def close(self):
        if not self.closed:
            self.closed = 1
            self._outwin = None
            self._inwin = None
            self._win.attrset(0)
            self._win.clrtobot()
            self._win.refresh()
            self._win = None
            reset_shell_mode()

    def read(self, n):
        if self.closed:
            raise IOError, "read on closed file object"
        return self._win.getstr()

    def write(self, text, attr=0):
        if self.closed:
            raise IOError, "write on closed file object"
        self._outwin.addstr(text, attr)
        self._outwin.refresh()

    def readline(self, hint=-1):
        return self.raw_input()+"\n"

    def readlines(self):
        if self.closed:
            raise IOError, "readlines on closed file object"
        rv = []
        t = self.readline()
        while t:
            rv.append(t)
            t = self.readline()
        return rv

    def flush(self):
        self._win.refresh()

    def writelines(self, lines):
        for line in lines:
            self.writeline(line)

    def writeline(self, line, attr=0):
        if self.closed:
            raise IOError, "writeline on closed file object"
        self._outwin.addstr(line, attr)
        self._outwin.addstr("\n", 0)
        self._outwin.refresh()

    def fileno(self): # ??? punt, since this uses stdio
        return sys.stdout.fileno()

    def isatty(self):
        return sys.stdout.isatty()

    def errlog(self, text):
        self.stderr.write("%s\n" % (text,))
        self.stderr.flush()

    # user input
    def raw_input(self, prompt="", attr=0):
        self._inwin.clear()
        self._inwinborder.box()
        self._inwin.addstr(0,0,prompt, attr)
        self._inwin.refresh()
        return self._inwin.getstr()
    user_input = raw_input

    def getkey(self):
        return self._inwin.getkey()


class CursesTheme(UI.Theme):
    "Base class for themes. Defines interface."
    def _setcolors(cls):
        afstr = tigetstr("setaf")
        cls.NORMAL = cls.RESET = tigetstr("sgr0")
        cls.BOLD = cls.BRIGHT = tigetstr("bold")
        cls.BLACK = tparm(afstr, COLOR_BLACK)
        cls.RED = tparm(afstr, COLOR_RED)
        cls.GREEN = tparm(afstr, COLOR_GREEN)
        cls.YELLOW = tparm(afstr, COLOR_YELLOW)
        cls.BLUE = tparm(afstr, COLOR_BLUE)
        cls.MAGENTA = tparm(afstr, COLOR_MAGENTA)
        cls.CYAN = tparm(afstr, COLOR_CYAN)
        cls.WHITE = tparm(afstr, COLOR_WHITE)
        cls.DEFAULT = tigetstr("op")
        cls.GREY = cls.BLACK+cls.BOLD
        cls.BRIGHTRED = cls.RED+cls.BOLD
        cls.BRIGHTGREEN = cls.GREEN+cls.BOLD
        cls.BRIGHTYELLOW = cls.YELLOW+cls.BOLD
        cls.BRIGHTBLUE = cls.BLUE+cls.BOLD
        cls.BRIGHTMAGENTA = cls.MAGENTA+cls.BOLD
        cls.BRIGHTCYAN = cls.CYAN+cls.BOLD
        cls.BRIGHTWHITE = cls.WHITE+cls.BOLD
        cls.UNDERSCORE = tigetstr("smul")
        cls.BLINK = tigetstr("blink")
        cls.help_local = COLOR_WHITE
        cls.help_inherited = COLOR_YELLOW
        cls.help_created = COLOR_GREEN
    _setcolors = classmethod(_setcolors)



class UserInterface(UI.UserInterface):
    """An curses terminal user interface for CLIs.  """

    def printf(self, text):
        "Print text run through the prompt formatter."
        self.Print(self.format(text))
    
    def error(self, text):
        self._io.errlog(text) # XXX error pane

    def add_heading(self, text, level=1):
        s = ["\n"]
        s.append("%s%s" % ("  "*(level-1), text))
        s.append("%s%s" % ("  "*(level-1), "-"*len(text)))
        s.append("\n")
        self.Print("\n".join(s))

    def add_title(self, title):
        self.add_heading(title, 0)

    # called with the name of a logfile to report
    def logfile(self, filename):
        self._io.write("LOGFILE: <%s>\n" % (filename,))

    def add_message(self, msgtype, msg, level=1, attr=0):
        self._io.addstr("%s%s" % ("  "*(level-1), msgtype), attr)
        self._io.addstr(": %s\n" % msg)
        self._io.refresh()

    def add_summary(self, text):
        self._io.write(text)

    def add_text(self, text):
        self._io.write(text)

    def add_url(self, text, url):
        self._io.write("%s: <%s>\n" % (text, url))

    def passed(self, msg="", level=1):
        return self.add_message(self.format("PASSED"), msg, level, color_pair(COLOR_GREEN) | A_BOLD)

    def failed(self, msg="", level=1):
        return self.add_message(self.format("FAILED"), msg, level, color_pair(COLOR_RED) | A_BOLD)

    def incomplete(self, msg="", level=1):
        return self.add_message(self.format("INCOMPLETE"), msg, level, color_pair(COLOR_YELLOW))

    def abort(self, msg="", level=1):
        return self.add_message(self.format("ABORT"), msg, level, color_pair(COLOR_YELLOW) | A_BOLD)

    def info(self, msg, level=1):
        return self.add_message("INFO", msg, level)

    def diagnostic(self, msg, level=1):
        return self.add_message(self.format("DIAGNOSTIC"), msg, level, color_pair(COLOR_YELLOW))

    def newpage(self):
        self._io.write("\x0c") # FF

    def newsection(self):
        self._io.write("\x0c") # FF

    # user input
    def _get_prompt(self, name, prompt=None):
        return prompt or self._env[name]

    def user_input(self, prompt=None):
        return self._io.raw_input(self._get_prompt("PS1", prompt))

    def more_user_input(self):
        return self._io.raw_input(self._get_prompt("PS2"))

    def choose(self, somelist, defidx=0, prompt=None):
        return choose(self._io, somelist, defidx, self._get_prompt("PS3", prompt))
    
    def get_text(self, msg=None):
        return get_text(self._io, self._get_prompt("PS4"), msg)

    def get_value(self, prompt, default=None):
        return get_input(self._io, prompt, default)

    def yes_no(self, prompt, default=True):
        return yes_no(self._io, prompt, default)

    def get_key(prompt=""):
        if prompt:
            self._io.write(prompt)
        return self._io.getkey()

    # docstring/help formatters
    def _print_doc(self, s, color):
        i = s.find("\n")
        if i > 0:
            self._io.addstr(s[:i], color_pair(color))
            self._io.addstr(s[i:])
            self._io.addstr("\n\n")
        else:
            self._io.addstr(s)
            self._io.addstr("\n\n")
        self._io.refresh()

    def help_local(self, text):
        return self._print_doc(text, self._theme.help_local)

    def help_inherited(self, text):
        return self._print_doc(text, self._theme.help_inherited)
    
    def help_created(self, text):
        return self._print_doc(text, self._theme.help_created)



def get_text(io, prompt="", msg=None):
    """Prompt user to enter multiple lines of text."""
    py, px = io.getmaxyx()
    outwin = io.derwin(py-3,px-20, 3,10)
    outwin.box()
    outwin.addstr(0,5, (msg or "Enter text.") +" End with ^G.")
    outwin.refresh()
    win = outwin.derwin(py-5,px-22, 2,2)
    tb = curses.textpad.Textbox(win)
    text = tb.edit()
    win.erase()
    outwin.erase()
    del tb, win, outwin
    return text


def get_input(io, prompt="", default=None):
    """Get user input with an optional default value."""
    if default:
        ri = io.raw_input("%s [%s]> " % (prompt, default))
        if not ri:
            return default
        else:
            return ri
    else:
        return io.raw_input("%s> " % (prompt, ))

def choose(io, somelist, defidx=0, prompt="choose"):
    """Select an item from a list."""
    if len(somelist) == 0:
        return None

    root = io.root
    root.bottom()
    py, px = io.getmaxyx()

    outwin = io.derwin(py-3,px-10, 3,5)
    outwin.box()
    outwin.refresh()
    win = outwin.derwin(py-5,px-12, 1,1)
    panel = curses.panel.new_panel(outwin)

    print_menu_list(somelist, win, py)
    panel.top()
    panel.show()

    defidx = int(defidx)
    if defidx < 0:
        defidx = 0
    if defidx >= len(somelist):
        defidx = len(somelist)-1
    try:
        try:
            ri = get_input(io, prompt, defidx+1) # menu list starts at one
        except EOFError:
            return None
        if ri:
            try:
                idx = int(ri)-1
            except ValueError:
                io.errlog("Bad selection. Type in the number.")
                return None
            else:
                try:
                    return somelist[idx]
                except IndexError:
                    io.errlog("Bad selection. Selection out of range.")
                    return None
        else:
            return None
    finally:
        panel.hide()
        win.erase() ; outwin.clear()
        root.show()


def yes_no(io, prompt, default=True):
    yesno = get_input(io, prompt, IF(default, "Y", "N"))
    return yesno.upper().startswith("Y")

def print_menu_list(clist, win, lines=20):
    """Print a list with leading numeric menu choices. Use two columns in necessary."""
    y, x = win.getbegyx()
    h = max((len(clist)/2)+1, lines)
    i1, i2 = 1, h+1
    for c1, c2 in map(None, clist[:h], clist[h:]):
        if c2:
            win.addstr(y+i1,1, "%2d: %-33.33s | %2d: %-33.33s\n" % (i1, c1, i2, c2))
        else:
            win.addstr(y+i1,1, "%2d: %-74.74s" % ( i1, c1))
        i1 += 1
        i2 += 1
    win.refresh()



def get_curses_ui(ioc=CursesIO, uic=UserInterface, inputsize=7, env=None):
    """Constructor function to return a window in full-screen mode. Sets up
    returning terminal to "standard" mode when Python exits."""
    tty.save_state(sys.stdout.fileno()) # auto-cleans at Python exit
    win=initscr()
    def_shell_mode()
    try:
        start_color()
    except:
        pass
    else:
        init_pair(COLOR_RED, COLOR_RED, COLOR_BLACK)
        init_pair(COLOR_BLUE, COLOR_BLUE, COLOR_BLACK)
        init_pair(COLOR_CYAN, COLOR_CYAN, COLOR_BLACK)
        init_pair(COLOR_GREEN, COLOR_GREEN, COLOR_BLACK)
        init_pair(COLOR_MAGENTA, COLOR_MAGENTA, COLOR_BLACK)
        init_pair(COLOR_RED, COLOR_RED, COLOR_BLACK)
        init_pair(COLOR_WHITE, COLOR_WHITE, COLOR_BLACK)
        init_pair(COLOR_YELLOW, COLOR_YELLOW, COLOR_BLACK)
    #noecho() ; cbreak() ; win.keypad(1)
    io = ioc()
    io.set_win(win, inputsize)
    theme = CursesTheme()
    ui = uic(io, env, theme)
    return ui


