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
Virtual terminal objects. Thanks to Noah Spurrier for original code ideas, and
inspiration.

Note that this terminal emulation is not 100% complete.

If you are interested in using this please consider that the rxvt-unicode
program now has features to enable generic terminal emulation mode. But I
haven't tried it yet.

"""

__all__ = ["Screen", "Printer", "NullPrinter", "ReprPrinter", 
    "Keyboard", "Terminal", "get_terminal"]

import sys
import array
import string
import bisect
from errno import EAGAIN

from pycopia import fsm
from pycopia import asyncinterface
from pycopia.aid import Stack, IF

NUL = 0    # Fill character; ignored on input.
ENQ = 5    # Transmit answerback message.
BEL = 7    # Ring the bell.
BS  = 8    # Move cursor left.
HT  = 9    # Move cursor to next tab stop.
LF = 10    # Line feed.
VT = 11    # Same as LF.
FF = 12    # Same as LF.
CR = 13    # Move cursor to left margin or newline.
SO = 14    # Invoke G1 character set.
SI = 15    # Invoke G0 character set.
XON = 17   # Resume transmission.
XOFF = 19  # Halt transmission.
CAN = 24   # Cancel escape sequence.
SUB = 26   # Same as CAN.
ESC = 27   # Introduce a control sequence.
DEL = 127  # Fill character; ignored on input.
SPACE = chr(32) # Space or blank character.


def constrain(x, minx, maxx):
    return max(min(x, maxx), minx)

# buffer cells are stored as packed integers. 
# char is the ASCII character. attr is a bitfield of attributes
# fg is foreground color
# bg is background color
def encode(char, attr=0, fg=0, bg=0):
    return ((attr & 0x7f) << 24) + ((fg & 0xff) << 16) + ((bg & 0xff) << 8) + (ord(char) & 0xff)

def decode(i):
    # return char, attr, fg, bg
    return chr(i & 0xff), i >> 24, (i & 0xff0000) >> 16, (i & 0xff00) >> 8

BLANK = encode(SPACE, 0, 7, 0)

# cursors and Screens are origin zero.
class Cursor(object):
    def __init__(self, scr):
        self.row = 0
        self.col = 0
        self._saved = Stack()
        self.adjust(scr)

    def __call__(self):
        return self.row, self.col

    def __str__(self):
        return "(%d, %d)"% (self.row, self.col)

    def adjust(self, scr):
        self.rows = scr.rows-1
        self.cols = scr.cols-1
        self.constrain()

    def constrain(self):
        self.row = constrain(self.row, 0, self.rows)
        self.col = constrain(self.col, 0, self.cols)

    def save(self):
        self._saved.push((self.row, self.col))

    def restore(self):
        try:
            self.row, self.col = self._saved.pop()
        except IndexError: # no prior save
            self.row, self.col = 0,0

    def reset(self, r=0, c=0):
        self.row = r
        self.col = c
    home = reset

    def set(self, r=None, c=None):
        if r is not None:
            self.row = r
        if c is not None:
            self.col = c

    def up(self, count=1):
        if self.row == 0:
            return 1
        else:
            self.row = constrain(self.row - count, 0, self.rows)
            return 0

    def down(self, count=1):
        if self.row == self.rows:
            return 1
        else:
            self.row = constrain(self.row + count, 0, self.rows)
            return 0

    def back(self, count=1):
        if self.col == 0:
            return 1
        else:
            self.col = constrain(self.col - count, 0, self.cols)
            return 0

    def forward(self, count=1):
        if self.col == self.cols:
            return 1
        else:
            self.col = constrain(self.col + count, 0, self.cols)
            return 0


class Screen(object):
    def __init__ (self, rows=24, cols=80):
        self.rows = rows
        self.cols = cols
        b = []
        for r in range(rows):
            b.append(self._new_row(cols))
        self.buf = b
        self.cursor = Cursor(self)
        self.reset()
        self.initialize()

    def initialize(self):
        return NotImplemented

    def finalize(self):
        return NotImplemented

    def errorlog(self, text):
        return NotImplemented

    def __str__(self):
        scr = ["%s  attr: %d  fg: %d  bg: %d wrap: %s" % (self.cursor, self.attr, self.fg, self.bg, IF(self._wrap, "ON", "OFF"))]
        scr.append("+%s+" % ("-"*self.cols,))
        for r in self.buf:
            chars = map(lambda t: t[0], map(decode, r))
            scr.append("|%s|" % ("".join(chars),))
        scr.append("+%s+\n" % ("-"*self.cols,))
        return "\n".join(scr)

    def _new_row(self, cols):
        a = array.array("i")
        for c in range(cols):
            a.append(BLANK)
        return a

    def dump(self, fo):
        """Write screen contents to file object."""
        for r in self.buf:
            rowvals = map(decode, r)
            for char, attr, fg, bg in rowvals:
                fo.write(char) # XXX handle attributes and color?
            fo.write("\n")

    def reset(self):
        self.scroll_row_start = 0
        self.scroll_row_end = self.rows-1
        self._tabs = range(0,132,8)
        self.attr = 0
        self.fg = 7
        self.bg = 0
        self._wrap = 1
        self._do_wrap = 0
        self._linefeed_mode = 0
        self._insert = 0
        self.fill()
        self.cursor_home()

    def set_columns(self, cols):
        if cols == self.cols:
            return # short ciruit if setting the same
        self.cols = cols
        b = []
        for r in range(self.rows):
            b.append(self._new_row(cols))
        self.buf = b
        self.scroll_row_start = 0
        self.scroll_row_end = self.rows-1
        self.cursor.adjust(self)
        self.cursor.home(0,0)

    # control methods
    def set_scroll_rows(self, rs, re): # <ESC>[{start};{end}r
        '''Enable scrolling from row {start} to row {end}.'''
        if rs > re:
            rs, re = re, rs
        self.scroll_row_start = rs % self.rows
        self.scroll_row_end = re % self.rows
        self.cursor_home()

    def scroll_screen(self): # <ESC>[r
        '''Enable scrolling for entire display.'''
        self.scroll_row_start = 0
        self.scroll_row_end = self.rows-1

    def set(self, row, col, char):
        col = col % self.cols
        row = row % self.rows
        self.buf[row][col] = encode(char, self.attr, self.fg, self.bg)
    put = set # alias

    def putchar(self, ch):
        r, c = self.cursor()
        self.set(r, c, ch)

    def insert(self, ch):
        """This inserts a character at cursor. Everything under
        and to the right is shifted right one character.
        The last character of the line is lost.  """
        r, c = self.cursor()
        row = self.buf[r]
        row[c+1:] = row[c:-1]
        row[c] = encode(ch, self.attr, self.fg, self.bg)

    def writechar(self, ch):
        "Write a single character to the screen. Wrap the cursor if necessary."
        if self._insert:
            self.insert(ch)
        else:
            r, c = self.cursor()
            #if self._wrap and (self._do_wrap or (c == self.cols-1)):
            if self._wrap and self._do_wrap:
                self._do_wrap = 0
                self.cursor.set(c=0)
                if self.cursor.down(1):
                    self.scroll_up()
                r, c = self.cursor()
            self.set(r, c, ch)
            self.cursor.forward(1)
            self._do_wrap = (c == (self.cols-1))


#    def process(self, c):
#        self.fsm.process(c)
#
#    def write(self, text):
#        for c in text:
#            self.fsm.process(c)
#
    def get(self, row, col):
        col = col % self.cols
        row = row % self.rows
        return decode(self.buf[row][col])

    def scroll_up(self):
        self.buf.insert(self.scroll_row_end+1, self._new_row(self.cols))
        del self.buf[self.scroll_row_start]

    def scroll_down(self):
        self.buf.insert(self.scroll_row_start, self._new_row(self.cols))
        del self.buf[self.scroll_row_end+1]

    def fill_region(self, rs,cs, re,ce, ch=SPACE):
        ch = encode(ch, self.attr, self.fg, self.bg)
        rs = rs % self.rows
        re = re % self.rows
        cs = cs % self.cols
        ce = ce % self.cols
        if rs > re:
            rs, re = re, rs
        if cs > ce:
            cs, ce = ce, cs
        for r in range(rs, re+1):
            row = self.buf[r]
            for c in range(cs, ce + 1):
                row[c] = ch

    def fill(self, ch=SPACE):
        self.fill_region(0,0, self.rows-1,self.cols-1, ch)

    def get_region(self, rs,cs, re,ce):
        '''This returns a list of lines representing the region.  '''
        rs = rs % self.rows
        re = re % self.rows
        cs = cs % self.cols
        ce = ce % self.cols
        if rs > re:
            rs, re = re, rs
        if cs > ce:
            cs, ce = ce, cs
        sc = []
        for r in range(rs, re+1):
            line = ''.join(map(lambda t: apply(decode, t), self.buf[r][cs:ce+1]))
            sc.append(line)
        return sc

    def erase_end_of_line(self): # <ESC>[0K -or- <ESC>[K
        self.fill_region(self.cursor.row, self.cursor.col, self.cursor.row, self.cols-1)

    def erase_start_of_line(self): # <ESC>[1K
        '''Erases from the current cursor position to
        the start of the current line.'''
        r, c = self.cursor()
        self.fill_region(r, 0, r, c)

    def erase_line(self): # <ESC>[2K
        '''Erases the entire current line.'''
        r, c = self.cursor()
        self.fill_region(r, 0, r, self.cols-1)

    def erase_down(self): # <ESC>[0J -or- <ESC>[J
        '''Erases the screen from the current line down to
        the bottom of the screen.'''
        self.erase_end_of_line()
        self.fill_region(self.cursor.row + 1, 0, self.rows-1, self.cols-1)

    def erase_up(self): # <ESC>[1J
        '''Erases the screen from the current line up to
        the top of the screen.'''
        self.erase_start_of_line()
        self.fill_region(self.cursor.row-1, 0, 0, self.cols-1)

    def erase_screen(self): # <ESC>[2J
        '''Erases the screen with the background color.'''
        self.fill_region(self.scroll_row_start, 0, self.scroll_row_end, self.cols-1)
        self.cursor_home()

    def cr(self):
        """This moves the cursor to the beginning (col 0) of the current row."""
        self.cursor.set(c=0)

    def lf(self):
        """This moves the cursor down with scrolling.  """
        if self._linefeed_mode:
            self.cursor.set(c=0)
        if self.cursor.down(1):
            self.scroll_up()

    def null(self): # null does nothing
        return None

    def crlf(self):
        """This advances the cursor with CRLF properties.
        The cursor will line wrap and the screen may scroll.  """
        self.cr()
        self.lf()

    def bs(self):
        self.cursor_back(1)

    def tab(self): # XXX
        r, c = self.cursor()
        ts = self._tabs
        i = bisect.bisect_right(ts, c)
        if i == len(ts):
            return self.cursor.set(c=self.cols-1)
        else:
            newc = ts[i]
            return self.cursor.set(c=newc)

    def cursor_home(self, r=0, c=0):
        self._do_wrap = 0
        return self.cursor.home(self.scroll_row_start+r, c)
    cursor_force_position = cursor_home # <ESC>[{ROW};{COLUMN}f

    def cursor_set(self, r=None, c=None): # <ESC>[{ROW};{COLUMN}H
        self._do_wrap = 0
        return self.cursor.set(r, c)

    def cursor_up(self, count=1): # <ESC>[{COUNT}A
        self._do_wrap = 0
        return self.cursor.up(count)

    def cursor_down(self, count=1): # <ESC>[{COUNT}B
        self._do_wrap = 0
        return self.cursor.down(count)

    def cursor_back(self, count=1): # <ESC>[{COUNT}D
        self._do_wrap = 0
        return self.cursor.back(count)

    def cursor_forward(self, count=1): # <ESC>[{COUNT}C
        self._do_wrap = 0
        return self.cursor.forward(count)

    def cursor_up_reverse(self): # <ESC> M   (called RI -- Reverse Index)
        self._do_wrap = 0
        if self.cursor.up(1):
            self.scroll_down()

    def cursor_save(self): # <ESC>[s -or- <ESC>7
        '''Save current cursor position.'''
        return self.cursor.save()
    cursor_save_attrs = cursor_save

    def cursor_unsave(self): # <ESC>[u -or-  <ESC>8
        '''Restores cursor position after a Save Cursor.'''
        return self.cursor.restore()
    cursor_restore_attrs = cursor_unsave

    def cursor_report(self, fo):
        fo.write() # XXX

    # tabs
    def set_tab(self): # <ESC>H
        '''Sets a tab at the current position.'''
        r, c = self.cursor()
        bisect.insort_right(self._tabs, c)

    def clear_tab(self): # <ESC>[g
        '''Clears tab at the current position.'''
        r, c = self.cursor()
        try:
            i = self._tabs.index(c)
        except ValueError:
            pass
        else:
            del self._tabs[i]

    def clear_all_tabs(self): # <ESC>[3g
        '''Clears all tabs.'''
        self._tabs = [0]

#        Insert line             Esc [ Pn L
#        Delete line             Esc [ Pn M
#        Delete character        Esc [ Pn P
#        Scrolling region        Esc [ Pn(top);Pn(bot) r


class Printer(object):
    def __init__(self, outf):
        self._outf = outf

    def set_file(self, fo=None):
        self._outf = fo

    def write(self, text):
        self._outf.write(text)

    def reset(self):
        pass

    def flush(self):
        self._outf.flush()


class NullPrinter(Printer):
    def __init__(self):
        pass
    def write(self, text):
        return len(text)

class ReprPrinter(Printer):
    def write(self, text):
        self._outf.write(repr(text))
        self._outf.write("\n")


class Keyboard(object):
    _KEYMAP = {}
    def __init__(self):
        self._locked = 0

    def getkey(self, code):
        return self._KEYMAP.get(code, code)

    def reset(self): # noop in base class
        return None

    def lock(self):
        self._locked = 1

    def unlock(self):
        self._locked = 0

    def __str__(self):
        return """                                     |
                            +=================+
                            | o o %7.7s o o |
                            +-----------------+
""" % (IF(self._locked, "locked ", "o o o o"),)

class TerminalBase(object):
    def __init__(self, pty, screen, keyboard, printer=None):
        self._pty = pty
        self.screen = screen
        self.keyboard = keyboard
        self.printer = printer
        self.fsm = fsm.FSM("INIT") # populate this in <subclass>.initialize()
        self.ANY = fsm.ANY # make accessible to subclasses
        self._buf = ""
        self.initialize()

    def fileno(self):
        return self._pty.fileno()

    def initialize(self):
        return NotImplemented

    def close(self):
        self._pty.close()

    def __str__(self):
        return str(self.screen)+str(self.keyboard)

    def reset(self):
        self.fsm.reset()
        self.screen.reset()
        self.keyboard.reset()
        if self.printer:
            self.printer.reset()

    def presskey(self, code):
        ch = self.keyboard.getkey(code)
        self._pty.write(ch)


class Terminal(TerminalBase):
    def __init__(self, pty, screen, keyboard, printer=None):
        TerminalBase.__init__(self, pty, screen, keyboard, printer)

    def write(self, data):
        return self._pty.write(data)

    def _read(self, N=100):
        while 1:
            try:
                raw = self._pty._read(N)
            except OSError, why:
                if why[0] == EAGAIN:
                    continue
                else:
                    raise
            except EOFError:
                self._pty = None
                raise
            else:
                break
        if self.printer:
            self.printer.write(raw)
        return raw

    def read(self, N=4096):
        while len(self._buf) < N:
            raw = self._read()
            self.fsm.process_string(raw)
        d = self._buf[:N]
        self._buf = self._buf[N:]
        return d


class AsyncTerminal(asyncinterface.AsyncInterface, Terminal):
    def __init__(self, pty, screen, keyboard, printer=None):
        import asyncio
        Terminal.__init__(self, pty, screen, keyboard, printer)
        asyncinterface.AsyncInterface.__init__(self)
        asyncio.register(self)

    def write(self, data):
        return self._pty.write(data)

    def _read(self, N=100):
        while 1:
            try:
                raw = self._pty._read(N)
            except OSError, why:
                if why[0] == EAGAIN:
                    continue
                else:
                    raise
            except EOFError:
                self._pty = None
                raise
            else:
                break
        if self.printer:
            self.printer.write(raw)
        return raw

    def read(self, N=4096):
        while len(self._buf) < N:
            raw = self._read()
            self.fsm.process_string(raw)
        d = self._buf[:N]
        self._buf = self._buf[N:]
        return d


def get_terminal(fo, termclass=Terminal, screenclass=Screen, 
        printer=None, keyboardclass=Keyboard, rows=24, cols=80):
    import termtools
    screen = screenclass(rows, cols)
    kb = keyboardclass()
    t = termclass(fo, screen=screen, printer=printer, keyboard=kb)
    termtools.set_winsize(fo.fileno(), rows, cols)
    return t



