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
An ANSI/VT102 terminal. Thanks to Noah Spurrier for code from which to start.

"""

# references:
# http://www.retards.org/terminals/vt102.html
# http://vt100.net/docs/vt102-ug/contents.html
# http://vt100.net/docs/vt220-rm/
# http://www.termsys.demon.co.uk/vtansi.htm
# 

import sys
import string

from terminal import *

# character attributes - bitfield values for screen.attr
BOLD = 0x1
DIM = 0x2
UNDERSCORE = 0x4
BLINK = 0x8
REVERSE = 0x10
HIDDEN = 0x20

# attribute command values
ALL_OFF = 0 # - All attributes off
BOLD_ON = 1 #  - Bold on
UNDERSCORE_ON = 4 # - Underscore on
BLINK_ON = 5  # - Blink on
REVERSE_ON = 7 # - Reverse on

#   Foreground Colours
#30 BLACK
#31 RED
#32 GREEN
#33 YELLOW
#34 BLUE
#35 MAGENTA
#36 CYAN
#37 WHITE
#
#   Background Colours
#40 BLACK
#41 RED
#42 GREEN
#43 YELLOW
#44 BLUE
#45 MAGENTA
#46 CYAN
#47 WHITE


class ANSIScreen(Screen):
    """This class encapsulates an ANSI/VT102 terminal.
        It filters a stream and maintains the state of
        a screen object.  """

    def set_attribute(self, which):
        if which == ALL_OFF:
            self.attr = 0
        elif which == BOLD_ON:
            self.attr |= BOLD
        elif which == UNDERSCORE_ON:
            self.attr |= UNDERSCORE
        elif which == BLINK_ON:
            self.attr |= BLINK
        elif which == REVERSE_ON:
            self.attr |= REVERSE

    def set_attribute_list(self, attrlist):
        map(self.set_attribute, attrlist)

    def set_background(self, bg):
        self.bg = bg

    def ShiftIn(self): # select G0 character set
        pass
    
    def ShiftOut(self): # select G1 character set
        pass

    def Bell(self): # ring bell
        pass

# keyboard stuff
# keyboard sequences
UPARROW = "\033\133\101" # <ESC>[A
DOWNARROW = "\033\133\102"
RIGHTARROW = "\033\133\103"
LEFTARROW = "\033\133\104"
INSERT = "\033[2~"
DELETE = "\033[3~"
PGUP = "\033[5~"
PGDOWN = "\033[6~"
HOME = "\033[7~"
END = "\033[8~"
PF1 = "\033\117\120"
PF2 = "\033\117\121"
PF3 = "\033\117\122"
PF4 = "\033\117\123"

F1 = "\x1b\x5b\x5b\x41"
F2 = "\x1b\x5b\x5b\x42"
F3 = "\x1b\x5b\x5b\x43"
F4 = "\x1b\x5b\x5b\x44"
F5 = "\x1b\x5b\x5b\x45"
F6 = "\x1b\x5b\x31\x37\x7e"
F7 = "\x1b\x5b\x31\x38\x7e"
F8 = "\x1b\x5b\x31\x39\x7e"
F9 = "\x1b\x5b\x32\x30\x7e"
F10 = "\x1b\x5b\x32\x31\x7e"
F11 = "\x1b\x5b\x32\x33\x7e"
F12 = "\x1b\x5b\x32\x34\x7e"



class ANSIKeyboard(Keyboard):
    APPLICATIONMODE = 1
    CURSORMODE = 2
    _KEYMAP = {
        "Up":UPARROW,
        "Down":DOWNARROW,
        "Right":RIGHTARROW,
        "Left":LEFTARROW,
        "Insert":INSERT,
        "Del":DELETE,
        "PageUp":PGUP,
        "PageDown":PGDOWN,
        "Home":HOME,
        "End":END,
        "PF1":PF1,
        "PF2":PF2,
        "PF3":PF3,
        "PF4":PF4,
        "F1":F1,
        "F2":F2,
        "F3":F3,
        "F4":F4,
        "F5":F5,
        "F6":F6,
        "F7":F7,
        "F8":F8,
        "F9":F9,
        "F10":F10,
        "F11":F11,
        "F12":F12,
    }

    APPLICATION_KEYS = {
        "0": "\033\117\160",
        "1": "\033\117\161",
        "2": "\033\117\162",
        "3": "\033\117\163",
        "4": "\033\117\164",
        "5": "\033\117\165",
        "6": "\033\117\166",
        "7": "\033\117\167",
        "8": "\033\117\170",
        "9": "\033\117\171",
        "-": "\033\117\155",
        ",": "\033\117\154",
        ".": "\033\117\156",
        "ENTER": "\033\117\115",
        "PF1": "\033\117\120",
        "PF2": "\033\117\121",
        "PF3": "\033\117\122",
        "PF4": "\033\117\123",
    }
    def setmode(self, mode):
        if mode:
            self._mode = self.APPLICATIONMODE
        else:
            self._mode = self.CURSORMODE



class ANSITerminal(Terminal):

    def log(self, c, fsm):
        sys.stderr.write("error: %s, %s\n" % (c, fsm.current_state))

    def Emit(self, c, fsm):
        self.screen.writechar(c)
        self._buf += c

    def Reset(self, c, fsm):
        self.reset()

    def DoCursorSave(self, c, fsm):
        self.screen.cursor_save_attrs()

    def DoCursorRestore (self, c, fsm):
        self.screen.cursor_restore_attrs()

    def DoUpReverse(self, c, fsm):
        self.screen.cursor_up_reverse()

    def DoHomeOrigin(self, c, fsm):
        self.screen.cursor_home(0,0)

    def DoBackOne(self,c, fsm):
        self.screen.cursor_back()

    def DoDownOne(self, c, fsm):
        self.screen.cursor_down()

    def DoForwardOne(self, c, fsm):
        self.screen.cursor_forward()

    def DoUpOne(self, c, fsm):
        self.screen.cursor_up()

    def DoEraseDown (self, c, fsm):
        self.screen.erase_down()

    def DoEraseEndOfLine(self, c, fsm):
        self.screen.erase_end_of_line()

    def DoEnableScroll(self, c, fsm):
        self.screen.scroll_screen()

    def no_digit(self, c, fsm):
        fsm.push(0)

    def StartNumber(self, c, fsm):
        fsm.push(c)

    def BuildNumber(self, c, fsm):
        ns = fsm.pop()
        ns = ns + c
        fsm.push(ns)

    def NextNumber(self, c, fsm):
        n = int(fsm.pop())
        fsm.push(n)

    def DoBack(self, c, fsm):
        count = max(int(fsm.pop()), 1)
        self.screen.cursor_back(count)

    def DoDown(self, c, fsm):
        count = max(int(fsm.pop()), 1)
        self.screen.cursor_down (count)

    def DoForward(self, c, fsm):
        count = max(int(fsm.pop()), 1)
        self.screen.cursor_forward(count)

    def DoUp(self, c, fsm):
        count = max(int(fsm.pop()), 1)
        self.screen.cursor_up(count)

    def DoErase(self, c, fsm):
        arg = int(fsm.pop())
        if arg == 0:
            self.screen.erase_down()
        elif arg == 1:
            self.screen.erase_up()
        elif arg == 2:
            self.screen.erase_screen()

    def DoEraseLine(self, c, fsm):
        arg = int(fsm.pop())
        if arg == 0:
            self.screen.erase_end_of_line()
        elif arg == 1:
            self.screen.erase_start_of_line()
        elif arg == 2:
            self.screen.erase_line()

    def DoHome(self, c, fsm):
        c = int(fsm.pop())
        r = int(fsm.pop())
        self.screen.cursor_home(r-1,c-1)

    def DoCursorPosition(self, c, fsm):
        c = int(fsm.pop())
        r = int(fsm.pop())
        self.screen.cursor_set(r-1,c-1)

    def DoScrollRegion(self, c, fsm):
        r2 = int(fsm.pop())
        r1 = int(fsm.pop())
        self.screen.set_scroll_rows(r1-1,r2-1)

    def DoIndex(self, c, fsm):
        if self.screen.cursor_down():
            self.screen.scroll_up()

    def DoTabStop(self, ch, fsm):
        #r, c = self.screen.cursor()
        self.screen.set_tab()

    def DoTabClear(self, ch, fsm):
        try:
            v = int(fsm.pop())
        except:
            v = 0
        if v == 0:
            self.screen.clear_tab()
        elif v == 3:
            self.screen.clear_all_tabs()
#       else:
#           self.log(ch, fsm)

    def NextLine(self, c, fsm):
        self.screen.cursor_set(c=0)
        if self.screen.cursor_down():
            self.screen.scroll_up()

    def ModeNoop(self, val):
        self.printer.write("ModeNoop: %d\n" % (val,))

    def WrapMode(self, val):
        self.screen._wrap = val

    def InsertMode(self, val):
        self.screen._insert = val

    def LinefeedMode(self, val):
        self.screen._linefeed_mode = val

    def CursorKey(self, val):
        self.keyboard.setmode(val)

    def SendRecieve(self, val):
        pass

    def KeyboardAction(self, val):
        if val:
            self.keyboard.lock()
        else:
            self.keyboard.unlock()

    def SetColumns(self, val):
        if val: # 132 column mode
            self.screen.set_columns(132)
        else: # reset = 80 col mode
            self.screen.set_columns(80)

    def ReverseNormal(self, val):
        self._reverse = val

    def JumpSmooth(self, val):
        self._smoothscroll = val

    def AbsoluteRelative(self, val):
        self._relative = val # zero is absolute, one is relative addressing

    _MODES = { 
                1: CursorKey, # application/cursor
                2: ModeNoop, # vt52
                3: SetColumns, # 80/132 column
                4: JumpSmooth, # jump/smooth scroll
                5: ReverseNormal, # reverse/normal screen
                6: AbsoluteRelative, # absolute/relative origin
                7: WrapMode, # autowrap on/off
                8: ModeNoop, # auto-repeat on/off
                18: ModeNoop, # print formfeed on/off
                19: ModeNoop, # print extent full screen/region
                40: ModeNoop, # XXX
    }
    _BASICMODES = { 
                0: ModeNoop, # error
                2: KeyboardAction, # keyboard action locked/unlocked
                4: InsertMode,      # insert/replace
                12: SendRecieve,    # send-recieve on/off
                20: LinefeedMode,   # linefeed/newline
    }
    def DoMode(self, c, fsm):
        key = int(fsm.pop())
        meth = self._MODES.get(key)
        if meth:
            if c == "h": # set
                return meth(self, 1)
            elif c == "l": # reset
                return meth(self, 0)
            else:
                raise RuntimeError, "invald char"

    def DoModeBasic(self, c, fsm):
        key = int(fsm.pop())
        meth = self._BASICMODES.get(key)
        if meth:
            if c == "h":
                return meth(self, 1)
            elif c == "l":
                return meth(self, 0)
            else:
                raise RuntimeError, "invald char"

    def Identify(self, c, fsm):
        try:
            fsm.pop()
        except:
            pass
        self.write("\x1b[?1;0c")

    def Reports(self, c, fsm):
        arg = int(fsm.pop())
        if arg == 6:
            self.write("\x1b[%d;%dR" % self.screen.cursor())
        elif arg == 5:
            self.write("\x1b[0n") # Ok

    def Answerback(self):
        self.write("\n%s\n" % (self.__class__.__name__,))

    _BASIC_ACTIONS = {
        "\x05": Answerback,
        "\r": Screen.cr,
        "\n": Screen.lf,
        "\x0b": Screen.lf, # VT
        "\x0c": Screen.lf, # FF
        "\b": Screen.bs,
        "\t": Screen.tab,
        "\0": Screen.null,
        "\x0e": ANSIScreen.ShiftOut,
        "\x0f": ANSIScreen.ShiftIn,
        "\x07": ANSIScreen.Bell,
    }
    def DoBasic(self, c, fsm):
        meth = self._BASIC_ACTIONS.get(c)
        if meth:
            meth(self.screen)

    def DoSpecial(self, c, fsm):
        arg = int(fsm.pop())
        if arg == 2: # INSERT - toggle
            if self._insert:
               self._insert = 0
            else:
                self._insert = 1

    def DoPoundAttribute(self, c, fsm):
        arg = int(c)
        if arg == 8:
            self.screen.fill("E")

    def DoAttributes(self, c, fsm): # m
        try:
            while 1:
                n = int(fsm.pop())
                self.screen.set_attribute(n)
        except IndexError:
            pass

    def initialize(self):
        self.Reset("c", None)
        fsm = self.fsm
        fsm.add_default_transition (self.Emit, 'INIT')
        fsm.add_transition_list ('\0\r\n\t\b\x0b\x0c\x0e\x0f\x07', 'INIT', self.DoBasic, 'INIT')
#        fsm.add_transition(self.ANY, "INIT", self.Emit, 'INIT')
        fsm.add_transition ('\x1b', 'INIT', None, 'ESC')
#        fsm.add_transition ('ESC', self.ANY, self.log, 'INIT')
        fsm.add_transition ('(', 'ESC', None, 'G0SCS')
        fsm.add_transition (')', 'ESC', None, 'G1SCS')
        fsm.add_transition_list ('AB012', 'G0SCS', None, 'INIT')
        fsm.add_transition_list ('AB012', 'G1SCS', None, 'INIT')
        fsm.add_transition ('7', 'ESC', self.DoCursorSave, 'INIT')
        fsm.add_transition ('8', 'ESC', self.DoCursorRestore, 'INIT')
        fsm.add_transition ('M', 'ESC', self.DoUpReverse, 'INIT')
        fsm.add_transition ('D', 'ESC', self.DoIndex, 'INIT')
        fsm.add_transition ('H', 'ESC', self.DoTabStop, 'INIT')
        fsm.add_transition ('E', 'ESC', self.NextLine, 'INIT')
        fsm.add_transition ('Z', 'ESC', self.Identify, 'INIT')
        fsm.add_transition ('c', 'ESC', self.Reset, 'INIT')
        fsm.add_transition ('>', 'ESC', self.DoUpReverse, 'INIT')
        fsm.add_transition ('<', 'ESC', self.DoUpReverse, 'INIT')
        fsm.add_transition ('\x1b', 'ESC', None, 'ESC')
        fsm.add_transition ('=', 'ESC', None, 'INIT') # Selects application keypad.
        fsm.add_transition ('#', 'ESC', None, 'GRAPHICS_POUND')
        fsm.add_transition_list (string.digits, 'GRAPHICS_POUND', self.DoPoundAttribute, 'INIT')
        fsm.add_transition ('[', 'ESC', None, 'CSI')
        # CSI means Escape Left Bracket. That is ^[[
        fsm.add_transition ('H', 'CSI', self.DoHomeOrigin, 'INIT')
        fsm.add_transition ('D', 'CSI', self.DoBackOne, 'INIT')
        fsm.add_transition ('B', 'CSI', self.DoDownOne, 'INIT')
        fsm.add_transition ('C', 'CSI', self.DoForwardOne, 'INIT')
        fsm.add_transition ('A', 'CSI', self.DoUpOne, 'INIT')
        fsm.add_transition ('J', 'CSI', self.DoEraseDown, 'INIT')
        fsm.add_transition ('K', 'CSI', self.DoEraseEndOfLine, 'INIT')
        fsm.add_transition ('r', 'CSI', self.DoEnableScroll, 'INIT')
        fsm.add_transition ('c', 'CSI', self.Identify, 'INIT')
        fsm.add_transition ('g', 'CSI', self.DoTabClear, 'INIT')
        fsm.add_transition ('m', 'CSI', self.DoAttributes, 'INIT')
        fsm.add_transition ('\x18', 'CSI', None, 'INIT') # cancel
        fsm.add_transition ('?', 'CSI', None, 'MODECRAP')
        fsm.add_transition (';', 'CSI', self.no_digit, 'SEMICOLON')
        fsm.add_transition_list ('\0\r\n\t\b\x0b\x0c\x0e\x0f\x07', 'CSI', self.DoBasic, 'CSI')
        fsm.add_transition_list (string.digits, 'CSI', self.StartNumber, 'NUMBER_1')
        fsm.add_transition_list (string.digits, 'NUMBER_1', self.BuildNumber, 'NUMBER_1')
        fsm.add_transition ('D', 'NUMBER_1', self.DoBack, 'INIT')
        fsm.add_transition ('B', 'NUMBER_1', self.DoDown, 'INIT')
        fsm.add_transition ('C', 'NUMBER_1', self.DoForward, 'INIT')
        fsm.add_transition ('A', 'NUMBER_1', self.DoUp, 'INIT')
        fsm.add_transition ('J', 'NUMBER_1', self.DoErase, 'INIT')
        fsm.add_transition ('K', 'NUMBER_1', self.DoEraseLine, 'INIT')
        fsm.add_transition ('l', 'NUMBER_1', self.DoModeBasic, 'INIT')
        fsm.add_transition ('h', 'NUMBER_1', self.DoModeBasic, 'INIT')
        fsm.add_transition ('~', 'NUMBER_1', self.DoSpecial, 'INIT')
        fsm.add_transition ('c', 'NUMBER_1', self.Identify, 'INIT')
        fsm.add_transition ('g', 'NUMBER_1', self.DoTabClear, 'INIT')
        fsm.add_transition ('m', 'NUMBER_1', self.DoAttributes, 'INIT')
        fsm.add_transition ('n', 'NUMBER_1', self.Reports, 'INIT')
        fsm.add_transition ('q', 'NUMBER_1', None, 'INIT') 
        fsm.add_transition_list ('\0\r\n\t\b\x0b\x0c\x0e\x0f\x07', 'NUMBER_1', self.DoBasic, 'NUMBER_1')
        fsm.add_transition_list (string.digits, 'MODECRAP', self.StartNumber, 'MODECRAP_NUM')
        fsm.add_transition_list (string.digits, 'MODECRAP_NUM', self.BuildNumber, 'MODECRAP_NUM')
        
        fsm.add_transition ('l', 'MODECRAP_NUM', self.DoMode, 'INIT')
        fsm.add_transition ('h', 'MODECRAP_NUM', self.DoMode, 'INIT')

        fsm.add_transition (';', 'NUMBER_1', None, 'SEMICOLON')
        fsm.add_transition_list (string.digits, 'SEMICOLON', self.StartNumber, 'NUMBER_2')
        fsm.add_transition_list (string.digits, 'NUMBER_2', self.BuildNumber, 'NUMBER_2')
        fsm.add_transition (self.ANY, 'SEMICOLON', self.log, 'INIT')
        fsm.add_transition (';', 'NUMBER_2', None, 'SEMICOLON')
        fsm.add_transition ('H', 'NUMBER_2', self.DoCursorPosition, 'INIT')
        fsm.add_transition ('f', 'NUMBER_2', self.DoHome, 'INIT')
        fsm.add_transition ('r', 'NUMBER_2', self.DoScrollRegion, 'INIT')
        fsm.add_transition ('m', 'NUMBER_2', self.DoAttributes, 'INIT')
        ### LED control. 
        fsm.add_transition ('q', 'NUMBER_2', None, 'INIT') 
        fsm.add_transition (self.ANY, 'NUMBER_2', self.log, 'INIT')




class SelfTest(object):
    def __init__(self):
        import proctools
        pm  = proctools.get_procmanager()
        proc = pm.spawnpty("vttest")
        self.term = get_ansiterm(proc, 24, 80, ReprPrinter(sys.stdout))
        self.logfile = open("/tmp/ANSITerm_test.log", "w")
        self.term.printer.set_file(self.logfile)

    def __del__(self):
        self.logfile.close()

    def __call__(self):
        import termtools, UserFile
        fd = sys.stdin.fileno()
        mode = termtools.tcgetattr(fd)
        try:
            while 1:
                print self.term
                try:
                    c = sys.stdin.read(1)
                    self.term.write(c)
                except EOFError:
                    break
        finally:
            termtools.tcsetattr(fd, termtools.TCSANOW, mode)

def get_ansiterm(fo, rows=24, cols=80, printer=None):
    import termtools
    screen = ANSIScreen(rows, cols)
    kb = ANSIKeyboard()
    t = ANSITerminal(fo, screen=screen, printer=printer, keyboard=kb)
    termtools.set_winsize(fo.fileno(), rows, cols)
    return t



if __name__ == '__main__':
    test = SelfTest()
    test()

