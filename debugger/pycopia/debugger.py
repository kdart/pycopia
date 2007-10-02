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
Debugger that can be used instead of the pdb module. This one provides a nicer
command interface by using the CLI module.

"""

import sys, os
import linecache
import bdb
from repr import Repr
import re

from pycopia import IO
from pycopia import UI
from pycopia import CLI
from pycopia.aid import IF

# Create a custom safe Repr instance and increase its maxstring.
# The default of 30 truncates error messages too easily.
_repr = Repr()
_repr.maxstring = 200
_repr.maxother = 50
_saferepr = _repr.repr

DebuggerQuit = bdb.BdbQuit

def find_function(funcname, filename):
    cre = re.compile(r'def\s+%s\s*[(]' % funcname)
    try:
        fp = open(filename)
    except IOError:
        return None
    # consumer of this info expects the first line to be 1
    lineno = 1
    answer = None
    while 1:
        line = fp.readline()
        if line == '':
            break
        if cre.match(line):
            answer = funcname, filename, lineno
            break
        lineno = lineno + 1
    fp.close()
    return answer

def lookupmodule(filename):
    """Helper function for break/clear parsing."""
    root, ext = os.path.splitext(filename)
    if ext == '':
        filename = filename + '.py'
    if os.path.isabs(filename):
        return filename
    for dirname in sys.path:
        while os.path.islink(dirname):
            dirname = os.readlink(dirname)
        fullname = os.path.join(dirname, filename)
        if os.path.exists(fullname):
            return fullname
    return None

def checkline(filename, lineno, ui):
    """Return line number of first line at or after input
    argument such that if the input points to a 'def', the
    returned line number is the first
    non-blank/non-comment line to follow.  If the input
    points to a blank or comment line, return 0.  At end
    of file, also return 0."""

    line = linecache.getline(filename, lineno)
    if not line:
        ui.Print('*** End of file')
        return 0
    line = line.strip()
    # Don't allow setting breakpoint at a blank line
    if (not line or (line[0] == '#') or
         (line[:3] == '"""') or line[:3] == "'''"):
        ui.Print('*** Blank or comment')
        return 0
    # When a file is read in and a breakpoint is at
    # the 'def' statement, the system stops there at
    # code parse time.  We don't want that, so all breakpoints
    # set at 'def' statements are moved one line onward
    if line[:3] == 'def':
        instr = ''
        brackets = 0
        while 1:
            skipone = 0
            for c in line:
                if instr:
                    if skipone:
                        skipone = 0
                    elif c == '\\':
                        skipone = 1
                    elif c == instr:
                        instr = ''
                elif c == '#':
                    break
                elif c in ('"',"'"):
                    instr = c
                elif c in ('(','{','['):
                    brackets = brackets + 1
                elif c in (')','}',']'):
                    brackets = brackets - 1
            lineno = lineno+1
            line = linecache.getline(filename, lineno)
            if not line:
                ui.Print('*** end of file')
                return 0
            line = line.strip()
            if not line: continue   # Blank line
            if brackets <= 0 and line[0] not in ('#','"',"'"):
                break
    return lineno

def run_editor(fname, lineno):
    if os.environ.has_key("DISPLAY"):
        if os.environ.has_key("XEDITOR"):
            ed = os.environ["XEDITOR"]
        else:
            ed = os.environ.get("EDITOR", "/bin/vi")
    else:
        ed = os.environ.get("EDITOR", "/bin/vi")
    cmd = "%s +%d %s" % (ed, lineno, fname) # assumes vi-like editor
    os.system(cmd)

class DebuggerTheme(UI.ANSITheme):
    pass

class Debugger(bdb.Bdb):
    def reset(self):
        bdb.Bdb.reset(self) # old style class
        self.forget()
        self._parser = None
        theme = DebuggerTheme("%GDebug%N> ")
        io = IO.ConsoleIO()
        self._ui = CLI.UserInterface(io, env=None, theme=theme)
        self._ui.register_expansion("S", self._expansions)

    def _expansions(self, c):
        if c == "S": # current frame over total frames in backtrace
            return "%s/%s" % (self.curindex+1, len(self.stack))

    def forget(self):
        self.lineno = None
        self.stack = []
        self.curindex = 0
        self.curframe = None

    def setup(self, f, t):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, t)
        self.curframe = self.stack[self.curindex][0]

    # Override Bdb methods

    def set_trace(self, frame=None, start=0):
        """Start debugging from `frame`, or `start` frames back from
        caller's frame.
        If frame is not specified, debugging starts from caller's frame.
        """
        if frame is None:
            frame = sys._getframe().f_back
        self.reset()
        if start:
            start = int(start)
            while start > 0 and frame:
                frame = frame.f_back
                start -= 1
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        self.set_step()
        sys.settrace(self.trace_dispatch)

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self.stop_here(frame):
            self._ui.printf('%g--Call--%N')
            self.interaction(frame, None)

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        self.interaction(frame, None)

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        frame.f_locals['__return__'] = return_value
        self._ui.printf('%g--Return--%N')
        self.interaction(frame, None)

    def user_exception(self, frame, (exc_type, exc_value, exc_traceback)):
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exception__'] = exc_type, exc_value
        if type(exc_type) == type(''):
            exc_type_name = exc_type
        else: 
            exc_type_name = exc_type.__name__
        self.print_exc(exc_type_name, exc_value)
        self.interaction(frame, exc_traceback)

    # General interaction function
    def interaction(self, frame, traceback):
        self.setup(frame, traceback)
        self.print_stack_entry(self.stack[self.curindex])
        if self._parser is None:
            cmd = DebuggerCommands(self._ui, CLIaliases)
            cmd._setup(self, "%GDebug%N:%S> ")
            parser = DebuggerParser(cmd)
            self._parser = parser
        self._parser.interact()
        self.forget()

    def execline(self, line):
        locals = self.curframe.f_locals
        globals = self.curframe.f_globals
        try:
            code = compile(line + '\n', '<stdin>', 'single')
        except:
            t, v = sys.exc_info()[:2]
            self._ui.printf('*** Could not compile: %%r%s%%N: %s' % (t, v))
        else:
            try:
                exec code in globals, locals
            except:
                t, v = sys.exc_info()[:2]
                self._ui.printf('*** %%r%s%%N: %s' % (t, v))

    def go_up(self):
        if self.curindex == 0:
            return '*** Oldest frame'
        self.curindex = self.curindex - 1
        self.curframe = self.stack[self.curindex][0]
        self.print_stack_entry(self.stack[self.curindex])
        self.lineno = None
        return None

    def go_down(self):
        if self.curindex + 1 == len(self.stack):
            return '*** Newest frame'
        self.curindex = self.curindex + 1
        self.curframe = self.stack[self.curindex][0]
        self.print_stack_entry(self.stack[self.curindex])
        self.lineno = None
        return None

    def getval(self, arg):
        return eval(arg, self.curframe.f_globals, self.curframe.f_locals)

    def retval(self):
        if '__return__' in self.curframe.f_locals:
            return self.curframe.f_locals['__return__']
        else:
            return None

    def defaultFile(self):
        """Produce a reasonable default."""
        filename = self.curframe.f_code.co_filename
        return filename

    def lineinfo(self, identifier):
        failed = (None, None, None)
        # Input is identifier, may be in single quotes
        idstring = identifier.split("'")
        if len(idstring) == 1:
            # not in single quotes
            id = idstring[0].strip()
        elif len(idstring) == 3:
            # quoted
            id = idstring[1].strip()
        else:
            return failed
        if id == '': 
            return failed
        parts = id.split('.')
        # Protection for derived debuggers
        if parts[0] == 'self':
            del parts[0]
            if len(parts) == 0:
                return failed
        # Best first guess at file to look at
        fname = self.defaultFile()
        if len(parts) == 1:
            item = parts[0]
        else:
            # More than one part.
            # First is module, second is method/class
            f = lookupmodule(parts[0])
            if f:
                fname = f
            item = parts[1]
        answer = find_function(item, fname)
        return answer or failed

    # Print a traceback starting at the top stack frame.
    # The most recently entered frame is printed last;
    # this is different from dbx and gdb, but consistent with
    # the Python interpreter's stack trace.
    # It is also consistent with the up/down commands (which are
    # compatible with dbx and gdb: up moves towards 'main()'
    # and down moves towards the most recent stack frame).

    def print_stack_trace(self):
        try:
            for frame_lineno in self.stack:
                self.print_stack_entry(frame_lineno)
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self, frame_lineno):
        frame, lineno = frame_lineno
        if frame is self.curframe:
            self._ui.Print(self._ui.format('%I>%N'), None)
        else:
            self._ui.Print(' ', None)
        self._ui.Print(self.format_stack_entry(frame_lineno))
        self.lineno = None

    def format_stack_entry(self, frame_lineno):
        frame, lineno = frame_lineno
        filename = self.canonic(frame.f_code.co_filename)
        s = []
        s.append(self._ui.format("%%y%s%%N(%%Y%r%%N) in " % (filename, lineno)))
        if frame.f_code.co_name:
            s.append(frame.f_code.co_name)
        else:
            s.append("<lambda>")
        if '__args__' in frame.f_locals:
            args = frame.f_locals['__args__']
            s.append(_saferepr(args))
        else:
            s.append('()')
        if '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            s.append(self._ui.format('%I->%N'))
            s.append(_saferepr(rv))
        line = linecache.getline(filename, lineno)
        if line: 
            s.append("\n  ")
            s.append(line.strip())
        return "".join(s)

    def print_exc(self, ex, val):
        uif = self._ui.format
        self._ui.Print(uif('%R'), ex, uif('%N:'), str(val))

    def debug(self, arg):
        sys.settrace(None)
        globals = self.curframe.f_globals
        locals = self.curframe.f_locals
        p = Debugger()
        p.reset()
        sys.call_tracing(p.run, (arg, globals, locals))
        sys.settrace(p.trace_dispatch)



class DebuggerParser(CLI.CommandParser):
    def initialize(self):
        ANY = CLI.ANY
        f = CLI.FSM(0)
        f.arg = ""
        f.add_default_transition(self._error, 0)
        # normally add text to args
        f.add_transition(ANY, 0, self._addtext, 0)
        f.add_transition_list(" \t", 0, self._wordbreak, 0)
        f.add_transition("\n", 0, self._doit, 0)
        # slashes
        f.add_transition("\\", 0, None, 1)
        f.add_transition(ANY, 1, self._slashescape, 0)
        # vars 
        f.add_transition("$", 0, self._startvar, 7)
        f.add_transition("{", 7, self._vartext, 9)
        f.add_transition_list(self.VARCHARS, 7, self._vartext, 7)
        f.add_transition(ANY, 7, self._endvar, 0)
        f.add_transition("}", 9, self._endvar, 0)
        f.add_transition(ANY, 9, self._vartext, 9)
        self._fsm = f


class DebuggerCommands(CLI.BaseCommands):
    def _setup(self, obj, prompt=None):
        self._dbg = obj # the debugger object
        self._obj = obj # for base class
        self._namespace = obj.curframe.f_locals
        if prompt:
            self._environ["PS1"] = str(prompt)
        self._reset_scopes()

    def _reset_namespace(self):
        self._namespace = self._dbg.curframe.f_locals

    def finalize(self):
        self._dbg.set_quit()

    def default_command(self, argv):
        line = " ".join(argv)
        self._dbg.execline(line)

    def execute(self, argv):
        """execute <statement>
    Execute <statement> in current frame context."""
        line = " ".join(argv[1:])
        self._dbg.execline(line)

    def brk(self, argv):
        """brk [-t] [breakpoint] ([file:]lineno | function) [, condition]
    With a line number argument, set a break there in the current
    file.  With a function name, set a break at first executable line
    of that function.  Without argument, list all breaks.  If a second
    argument is present, it is a string specifying an expression
    which must evaluate to true before the breakpoint is honored.

    The line number may be prefixed with a filename and a colon,
    to specify a breakpoint in another file (probably one that
    hasn't been loaded yet).  The file is searched for on sys.path;
    the .py suffix may be omitted."""
        temporary = False
        opts, longopts, args = self.getopt(argv, "t")
        for opt, arg in opts:
            if opt == "-t":
                temporary = True

        if not args:
            if self._dbg.breaks:  # There's at least one
                self._print("Num Type         Disp Enb   Where")
                for bp in bdb.Breakpoint.bpbynumber:
                    if bp:
                        bp.bpprint()
            return
        # parse arguments; comma has lowest precedence
        # and cannot occur in filename
        arg = " ".join(args)
        filename = None
        lineno = None
        cond = None
        comma = arg.find(',')
        if comma > 0:
            # parse stuff after comma: "condition"
            cond = arg[comma+1:].lstrip()
            arg = arg[:comma].rstrip()
        # parse stuff before comma: [filename:]lineno | function
        colon = arg.rfind(':')
        if colon >= 0:
            filename = arg[:colon].rstrip()
            f = lookupmodule(filename)
            if not f:
                self._print('*** ', `filename`, 'not found from sys.path')
                return
            else:
                filename = f
            arg = arg[colon+1:].lstrip()
            try:
                lineno = int(arg)
            except ValueError, msg:
                self._print('*** Bad lineno:', arg)
                return
        else:
            # no colon; can be lineno or function
            try:
                lineno = int(arg)
            except ValueError:
                try:
                    func = eval(arg,
                                self._dbg.curframe.f_globals,
                                self._dbg.curframe.f_locals)
                except:
                    func = arg
                try:
                    if hasattr(func, 'im_func'):
                        func = func.im_func
                    code = func.func_code
                    lineno = code.co_firstlineno
                    filename = code.co_filename
                except:
                    # last thing to try
                    (ok, filename, ln) = self._dbg.lineinfo(arg)
                    if not ok:
                        self._print('*** The specified object', `arg`)
                        self._print('is not a function or was not found along sys.path.')
                        return
                    lineno = int(ln)
        if not filename:
            filename = self._dbg.defaultFile()
        # Check for reasonable breakpoint
        line = checkline(filename, lineno, self._ui)
        if line:
            # now set the break point
            err = self._dbg.set_break(filename, line, temporary, cond)
            if err: 
                self._print('***', err)
            else:
                bp = self._dbg.get_breaks(filename, line)[-1]
                self._print("Breakpoint %d at %s:%d" % (bp.number, bp.file, bp.line))

    def enable(self, argv):
        """enable bpnumber [bpnumber ...]
    Enables the breakpoints given as a space separated list of
    bp numbers."""
        for i in argv[1:]:
            try:
                i = int(i)
            except ValueError:
                self._print('Breakpoint index %r is not a number' % i)
                continue
            if not (0 <= i < len(bdb.Breakpoint.bpbynumber)):
                self._print('No breakpoint numbered', i)
                continue
            bp = bdb.Breakpoint.bpbynumber[i]
            if bp:
                bp.enable()

    def disable(self, argv):
        """disable bpnumber [bpnumber ...]
    Disables the breakpoints given as a space separated list of
    bp numbers."""
        for i in argv[1:]:
            try:
                i = int(i)
            except ValueError:
                self._print('Breakpoint index %r is not a number' % i)
                continue
            if not (0 <= i < len(bdb.Breakpoint.bpbynumber)):
                self._print('No breakpoint numbered', i)
                continue
            bp = bdb.Breakpoint.bpbynumber[i]
            if bp:
                bp.disable()

    def condition(self, argv):
        """condition bpnumber str_condition
    str_condition is a string specifying an expression which
    must evaluate to true before the breakpoint is honored.
    If str_condition is absent, any existing condition is removed;
    i.e., the breakpoint is made unconditional."""
        bpnum = int(argv[1].strip())
        try:
            cond = argv[2]
        except:
            cond = None
        bp = bdb.Breakpoint.bpbynumber[bpnum]
        if bp:
            bp.cond = cond
            if not cond:
                self._print('Breakpoint', bpnum, 'is now unconditional.')

    def ignore(self, argv):
        """ignore bpnumber count
    Sets the ignore count for the given breakpoint number.  A breakpoint
    becomes active when the ignore count is zero.  When non-zero, the
    count is decremented each time the breakpoint is reached and the
    breakpoint is not disabled and any associated condition evaluates
    to true."""
        bpnum = int(argv[1].strip())
        try:
            count = int(argv[2].strip())
        except:
            count = 0
        bp = bdb.Breakpoint.bpbynumber[bpnum]
        if bp:
            bp.ignore = count
            if count > 0:
                reply = 'Will ignore next '
                if count > 1:
                    reply = reply + '%d crossings' % count
                else:
                    reply = reply + '1 crossing'
                self._print(reply + ' of breakpoint %d.' % bpnum)
            else:
                self._print( 'Will stop next time breakpoint', bpnum, 'is reached.')

    def clear(self, argv):
        """clear ...
    Three possibilities, tried in this order:
    clear -> clear all breaks, ask for confirmation
    clear file:lineno -> clear all breaks at file:lineno
    clear bpno bpno ... -> clear breakpoints by number

    With a space separated list of breakpoint numbers, clear
    those breakpoints.  Without argument, clear all breaks (but
    first ask confirmation).  With a filename:lineno argument,
    clear all breaks at that line in that file.

    Note that the argument is different from previous versions of
    the debugger (in python distributions 1.5.1 and before) where
    a linenumber was used instead of either filename:lineno or
    breakpoint numbers."""
        if len(argv) == 1:
            reply = self._ui.yes_no('Clear all breaks? ')
            if reply:
                self._dbg.clear_all_breaks()
            return
        arg = " ".join(argv[1:])
        if ':' in arg:
            # Make sure it works for "clear C:\foo\bar.py:12"
            i = arg.rfind(':')
            filename = arg[:i]
            arg = arg[i+1:]
            try:
                lineno = int(arg)
            except:
                err = "Invalid line number (%s)" % arg
            else:
                err = self._dbg.clear_break(filename, lineno)
            if err: 
                self._print('***', err)
            return
        numberlist = arg.split()
        for i in numberlist:
            err = self._dbg.clear_bpbynumber(i)
            if err:
                self._print('***', err)
            else:
                self._print('Deleted breakpoint %s ' % (i,))

    def where(self, argv): # backtrace
        """where
    Print a stack trace, with the most recent frame at the bottom.
    An arrow indicates the "current frame", which determines the
    context of most commands.  'bt' is an alias for this command."""
        self._dbg.print_stack_trace()

    def up(self, argv):
        """up
    Move the current frame one level up in the stack trace
    (to a newer frame)."""
        res = self._dbg.go_up()
        if res:
            self._print(res)
        self._reset_namespace()

    def down(self, argv):
        """down
    Move the current frame one level down in the stack trace
    (to an older frame)."""
        res = self._dbg.go_down()
        if res:
            self._print(res)
        self._reset_namespace()

    def step(self, argv):
        """step
    Execute the current line, stop at the first possible occasion
    (either in a function that is called or in the current function)."""
        self._dbg.set_step()
        raise CLI.CommandExit

    def next(self, argv):
        """next
    Continue execution until the next line in the current function
    is reached or it returns."""
        self._dbg.set_next(self._dbg.curframe)
        raise CLI.CommandExit

    def returns(self, argv):
        """returns
    Continue execution until the current function returns."""
        self._dbg.set_return(self._dbg.curframe)
        raise CLI.CommandExit

    def cont(self, arg):
        """cont
    Continue execution, only stop when a breakpoint is encountered."""
        self._dbg.set_continue()
        if self._dbg.breaks:
            raise CLI.CommandExit
        else:
            self._dbg._parser = None
            raise CLI.CommandQuit

    def jump(self, argv):
        """jump lineno
    Set the next line that will be executed."""
        if self._dbg.curindex + 1 != len(self._dbg.stack):
            self._print("*** You can only jump within the bottom frame")
            return
        try:
            arg = int(argv[1])
        except ValueError:
            self._print("*** The 'jump' command requires a line number.")
        else:
            try:
                # Do the jump, fix up our copy of the stack, and display the
                # new position
                self._dbg.curframe.f_lineno = arg
                self._dbg.stack[self._dbg.curindex] = self._dbg.stack[self._dbg.curindex][0], arg
                self._dbg.print_stack_entry(self._dbg.stack[self._dbg.curindex])
            except ValueError, e:
                self._print('*** Jump failed:', e)
            else:
                self._reset_namespace()

    def debug(self, argv):
        """debug code
    Enter a recursive debugger that steps through the code argument
    (which is an arbitrary expression or statement to be executed
    in the current environment)."""
        self._print("ENTERING RECURSIVE DEBUGGER")
        self._dbg.debug(" ".join(argv[1:]))
        self._print("LEAVING RECURSIVE DEBUGGER")

    def quit(self, argv):
        """quit or exit - Quit from the debugger.
    The program being executed is aborted."""
        super(DebuggerCommands, self).quit(argv)

    def args(self, argv):
        """args
    Print the arguments of the current function."""
        f = self._dbg.curframe
        co = f.f_code
        dict = f.f_locals
        n = co.co_argcount
        if co.co_flags & 4: n = n+1
        if co.co_flags & 8: n = n+1
        for i in range(n):
            name = co.co_varnames[i]
            self._print(name, '=', None)
            if name in dict: 
                self._print(dict[name])
            else: 
                self._print("*** undefined ***")

    def retval(self, argv):
        """retval
    Show return value."""
        val = self._dbg.retval()
        if val is not None:
            self._print(val)

    def show(self, argv):
        """show [<name>...]
    Shows the current frame's object and values. If parameter names are given
    then show only those local names."""
        f = self._dbg.curframe
        if len(argv) > 1:
            for name in argv[1:]:
                try:
                    self._print("%25.25s = %s" % \
                                (name, _saferepr(f.f_locals[name])))
                except KeyError:
                    self._print("%r not found." % (name,))
        else:
            self._ui.printf("%%I%s%%N (" % (f.f_code.co_name or "<lambda>",))
            co = f.f_code
            n = co.co_argcount
            if co.co_flags & 4: 
                n += 1
            if co.co_flags & 8: 
                n += 1
            local = f.f_locals
            for name in co.co_varnames[:n]:
                val = local.get(name, "*** no formal ***")
                self._print("%15.15s = %s," % (name, _saferepr(val)))
            self._print("  )")
            s = []
            for name in co.co_varnames[n:]:
                val = local.get(name, "*** undefined ***")
                s.append("%25.25s = %s" % (name, _saferepr(val)))
            if s:
                self._print("  Compiled locals:")
                self._print("\n".join(s))
            # find and print local variables that were not defined when
            # compiled. These must have been "stuffed" by other code.
            extra = []
            varnames = list(co.co_varnames) # to get list methods
            for name, val in local.items():
                try:
                    i = varnames.index(name)
                except ValueError:
                    extra.append("%25.25s = %s" % (name, _saferepr(val)))
            if extra:
                self._print("  Extra locals:")
                self._print("\n".join(extra))

    def Print(self, argv):
        """Print <expression>
    Print the value of the expression."""
        try:
            self._print(repr(self._dbg.getval(" ".join(argv[1:]))))
        except:
            ex, val = sys.exc_info()[:2]
            self._print("***", ex, val)

    def list(self, argv):
        """list [first [,last]]
    List source code for the current file.
    Without arguments, list 20 lines around the current line
    or continue the previous listing.
    With one argument, list 20 lines centered at that line.
    With two arguments, list the given range;
    if the second argument is less than the first, it is a count."""

        last = None
        if len(argv) >= 2:
            first = max(1, int(argv[1]) - 10)
            if len(argv) >= 3:
                last = int(argv[2])
                if last < first:
                    # Assume it's a count
                    last = first + last
        elif self._dbg.lineno is None:
            first = max(1, self._dbg.curframe.f_lineno - 10)
        else:
            first = self._dbg.lineno + 1
        if last is None:
            last = first + 20
        filename = self._dbg.curframe.f_code.co_filename
        self._print_source(filename, first, last)


    def edit(self, argv):
        """edit
    Open your editor at the current location."""
        line = self._dbg.curframe.f_lineno
        filename = self._dbg.curframe.f_code.co_filename
        run_editor(filename, line)

    def whatis(self, argv):
        """whatis arg
    Prints the type of the argument."""
        arg = " ".join(argv[1:])
        try:
            value = eval(arg, self._dbg.curframe.f_globals, self._dbg.curframe.f_locals)
        except:
            t, v = sys.exc_info()[:2]
            if type(t) == type(''):
                exc_type_name = t
            else: exc_type_name = t.__name__
            self._print('***', exc_type_name + ':', `v`)
            return
        # Is it a function?
        try: 
            code = value.func_code
        except: 
            pass
        else:
            self._print('Function', code.co_name)
            return
        # Is it an instance method?
        try: 
            code = value.im_func.func_code
        except: 
            pass
        else:
            self._print('Method', code.co_name)
            return
        # None of the above...
        self._print(type(value))

    def docs(self, argv):
        """docs
    Display the full documentation for the debugger."""
        if not help():
            self._print('Sorry, can\'t find the help file "debugger.doc"')

    def search(self, argv):
        """search <pattern>
    Search the source file for the regular expression pattern."""
        patt = re.compile(" ".join(argv[1:]))
        filename = self._dbg.curframe.f_code.co_filename
        if self._dbg.lineno is None:
            start = 0
        else:
            start = max(0,  self._dbg.lineno - 9)
        lines = linecache.getlines(filename)[start:]
        for lineno, line in enumerate(lines):
            #line = linecache.getline(filename, lineno)
            mo = patt.search(line)
            if mo:
                self._print_source(filename, lineno+start-10, lineno+start+10)
                return
        else:
            self._print("Pattern not found.")

    def _print_source(self, filename, first, last):
        breaklist = self._dbg.get_file_breaks(filename)
        try:
            for lineno in range(first, last+1):
                line = linecache.getline(filename, lineno)
                if not line:
                    self._ui.printf('%Y[EOF]%N')
                    break
                else:
                    s = []
                    s.append("%5.5s%s" % (lineno, IF(lineno in breaklist, self._ui.format(" %RB%N"), "  ")))
                    if lineno == self._dbg.curframe.f_lineno:
                        s.append(self._ui.format("%I->%N "))
                    else:
                        s.append("   ")
                    self._print("".join(s), line.rstrip())
                    self._dbg.lineno = lineno
        except KeyboardInterrupt:
            pass

CLIaliases = {
    "p":["Print"],
    "l":["list"],
    "n":["next"],
    "s":["step"],
    "c":["cont"],
    "ret":["returns"],
    "r":["returns"],
    "u":["up"],
    "d":["down"],
    "exec":["execute"],
    "e":["execute"],
    "bp":["brk"],
    "break":["brk"],
    "bt":["where"],
    "q":["quit"],
    "/":["search"],
}


# Simplified interface
def run(statement, globals=None, locals=None):
    Debugger().run(statement, globals, locals)

def runeval(expression, globals=None, locals=None):
    return Debugger().runeval(expression, globals, locals)

def runcall(*args):
    return Debugger().runcall(*args)

def set_trace(frame=None, start=0):
    Debugger().set_trace(frame, start)

# post mortems used to debug
def post_mortem(t, exc=None, val=None):
    "Start debugging at the given traceback."
    p = Debugger()
    p.reset()
    while t.tb_next is not None:
        t = t.tb_next
    if exc and val:
        p.print_exc(exc, val)
    p.interaction(t.tb_frame, t)

def debug(method, *args, **kwargs):
    """Run the method and debug any exception, except syntax or user
    interrupt.
    """
    try:
        method(*args, **kwargs)
    except:
        ex, val, tb = sys.exc_info()
        if ex in (SyntaxError, IndentationError, KeyboardInterrupt):
            sys.__excepthook__(ex, val, tb)
        else:
            post_mortem(tb, ex, val)

def pm():
    "Start debugging with the system's last traceback."
    ex, val, tb = sys.exc_info()
    post_mortem(tb, ex, val)

# show the external doc
def help():
    for dirname in sys.path:
        fullname = os.path.join(dirname, 'debugger.doc')
        if os.path.exists(fullname):
            import termtools
            io = termtools.PagedIO()
            io.write(file(fullname).read())
            del io
            return True
    return False

if __name__=='__main__':
    runcall(help)

