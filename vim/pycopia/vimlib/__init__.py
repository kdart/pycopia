#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <kdart@kdart.com>
# $Id$

"""
This module is intended for use with the Vim editor. It provides
additional functionality to vim in general, but also some functions
designed specifically for editing other python source files.

1. Adds more advanced functionality and commands to Vim
2. Enables more convenient Python program development (makes Vim a Python IDE)
3. Adds features for other specialized editing tasks, such as HTML.

"""

try:
    from vim import *
except ImportError:
    # for running outside of vim
    from pycopia.vimlib.vimtest import *
    

import sys, os
import string
import re
import parser, symbol, token
import tokenize
import cStringIO as StringIO

from pycopia import interactive
from pycopia import textutils

pyterm = interactive.pyterm
xterm = interactive.xterm

# hm, the vim module defines eval, which is the same name as the builtin
# function.
import __builtin__
py_eval = __builtin__.eval
del __builtin__

XTERM = os.environ.get("XTERM", "rxvt -e")
EXECTEMP = "/var/tmp/python_vim_temp_%s.py" % (os.getpid())

def_template = """def XXX():
    pass
"""
re_def = re.compile(r"^[ \t]*def ")
re_class = re.compile(r"^[ \t]*class ")
re_klass_export = re.compile(r"^class ([a-zA-Z][a-zA-Z0-9_]*)")
re_def_export = re.compile(r"^def ([a-zA-Z][a-zA-Z0-9_]*)")

def normal(str):
    command("normal "+str)

def test_count():
    print int(eval("v:count"))

def str_range(vrange):
    return string.join(vrange, "\n") + "\n"

def exec_vimrange(vrange):
    exec str_range(vrange)

def exec_vimrange_in_term(vrange):
    tf = open(EXECTEMP , "w")
    tf.write(str_range(vrange))
    tf.close()
    interactive.run_config(XTERM, "python -i %s" % (EXECTEMP))

def insert_def():
    current.range.append(string.split(def_template, "\n"))

def insert_viminfo():
    """Insert a vim line with tabbing related settings reflecting current settings."""
    # The following line is to prevent this vim from interpreting it as a real
    # v-i-m tagline.
    vi = ["# %s" % ("".join(['v','i','m']),)] 
    for var in ('ts', 'sw', 'softtabstop'):
        vi.append("%s=%s" % (var, eval("&%s" % (var,))))
    for var in ('smarttab', 'expandtab'):
        if int(eval("&%s" % var)):
            vi.append(var)
    current.range.append(":".join(vi))

def insert__all__():
    path, name = os.path.split(current.buffer.name)
    if name == "__init__.py":
        insert__all__pkg(path)
    else:
        insert__all__mod()

def insert__all__mod():
    klasses = []
    funcs = []
    for line in current.buffer:
        mo = re_klass_export.search(line)
        if mo:
            klasses.append(mo.group(1))
        mo = re_def_export.search(line)
        if mo:
            funcs.append(mo.group(1))
    current.range.append("__all__ = [%s]" % (", ".join(map(repr, klasses+funcs))))

def insert__all__pkg(path):
    files = textutils.grep ("^[A-Za-z]+\\.py$", os.listdir(path))
    res = []
    for name, ext in map(os.path.splitext, files):
        res.append(name)
    current.range.append("__all__ = [%s]" % (", ".join(map(repr, res))))


def spc_to_tab(vrange=None):
    spcs = " " * int(eval("&ts"))
    if vrange is None:
        command("s/%s/  /g" % spcs)
    else:
        for linenum in range(len(vrange)):
            vrange[linenum] = re.sub(spcs, "\t", vrange[linenum])

def reverse_search(reobject):
    startline, startcol = current.window.cursor
    for linenum in xrange(startline-2, 0, -1):
        if reobject.match(current.buffer[linenum]):
            return linenum

def forward_search(reobject):
    startline, startcol = current.window.cursor
    for linenum in xrange(startline, len(current.buffer)):
        if reobject.match(current.buffer[linenum]):
            return linenum

def forward_move(reobject):
    foundline = forward_search(reobject)
    if foundline:
        current.window.cursor = foundline+1, 0
        normal("z.")

def reverse_move(reobject):
    foundline = reverse_search(reobject)
    if foundline:
        current.window.cursor = foundline+1, 0
        normal("z.")


def next_def():
    forward_move(re_def)

def previous_def():
    reverse_move(re_def)

def next_class():
    forward_move(re_class)

def previous_class():
    reverse_move(re_class)

def balloonhelp():
    try:
        result = py_eval(eval("v:beval_text")).__doc__
        if result is None:
            return "No doc."
        result = result.replace("\0", " ")
        result = result.replace('"', '\\"')
        return2vim(result)
    except:
        #ex, val, tb = sys.exc_info()
        return2vim("")

# XXX is this hack really necessary?
def return2vim(val):
    command('let g:python_rv = "%s"' % (val,))

# utility functions

def htmlhex(text):
    return "".join(map(lambda c: "%%%x" % (ord(c),), text))

def get_visual_selection():
    b = vim.current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        return b[start_row-1][start_col:end_col+1]
    else:
        s = [ b[start_row-1][start_col:] ]
        for l in b[start_row:end_row-2]:
            s.append(l)
        s.append(b[end_row-1][:end_col+1])
        return "\n".join(s)

def htmlhex_visual_selection():
    b = current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        l = b[start_row-1]
        c = str(htmlhex(l[start_col:end_col+1]))
        b[start_row-1] = l[:start_col]+c+l[end_col+1:]
    else:
        b[start_row-1:end_row] = str(htmlhex("\n".join(b[start_row-1:end_row]))).split("\n") # XXX partial lines

def get_indent_level(line=None):
    if line is None:
        line = current.line
    altpyts = int(eval("&ts"))
    pyts = 8
    col = altcol = 0
    for i in xrange(len(line)):
        if line[i] == '#' or line[i] == '\n':
            continue
        if line[i] not in " \t":
            break
        if line[i] == " ":
            col = col + 1 ; altcol = altcol +1
        if line[i] == "\t":
            col = (col/pyts + 1) * pyts ; altcol = (altcol/altpyts + 1) * altpyts
    return col, altcol

def classifyws(s, tabwidth):
    raw = effective = 0
    for ch in s:
        if ch == ' ':
            raw = raw + 1
            effective = effective + 1
        elif ch == '\t':
            raw = raw + 1
            effective = (effective // tabwidth + 1) * tabwidth
        else:
            break
    return raw, effective

def select_block(top_re):
    matchline = reverse_search(top_re)
    if matchline:
        current.window.cursor = matchline+1, 0
#       normal("z\r")
        ind, realind = get_indent_level(current.line)
        for i in xrange(1,len(current.buffer) - matchline):
            if get_indent_level(current.buffer[matchline+i])[1] <= realind:
                break
        normal("V%dj" % i)

def select_class():
    select_block(re_class)

def select_def():
    select_block(re_def)

def keyword_help():
    interactive.showdoc(eval('expand("<cword>")'))

def keyword_edit():
    interactive.edit(eval('expand("<cword>")'))

def keyword_view():
    interactive.view(eval('expand("<cword>")'))

def keyword_split():
    modname = eval('expand("<cword>")')
    filename = interactive.find_source_file(modname)
    if filename is not None:
        command("split %s" % (filename,))
    else:
        print >>sys.stderr, "Could not find source to %s." % modname

def get_visual_selection():
    b = current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        return b[start_row-1][start_col:end_col+1]
    else:
        s = [ b[start_row-1][start_col:] ]
        for l in b[start_row:end_row-2]:
            s.append(l)
        s.append(b[end_row-1][:end_col+1])
        return "\n".join(s)

def visual_edit():
    text = get_visual_selection()
    if "\n" in text:
        print "bad selection"
    else:
        interactive.edit(text)

def visual_view():
    text = get_visual_selection()
    if "\n" in text:
        print "bad selection"
    else:
        interactive.view(text)


#### The following is experimental and is not fully functional.
### code analysis....

def syntax_check():
    src = "\n".join(current.buffer)+"\n"
    fo = StringIO.StringIO(src)
    if check(fo):
        ast = get_ast(src)

def get_ast(src=None):
    if src is None:
        src = "\n".join(current.buffer)+"\n"
    try:
        ast = parser.suite(src)
    except parser.ParserError, err:
        print >>sys.stderr, "ParserError:", err
        return None
    except SyntaxError, err:
        print >>sys.stderr, "SyntaxError:", err
        return None
    else:
        return ast

def eval_simple(t, d=None):
    if d is None:
        d = {}
    # put a valid top-level wrapper around the simple statement fragment.
    ast = parser.sequence2ast( (257, (264, (265, t, (4, '') )), (0, '')) )
    co = ast.compile()
    py_eval(co, d, d)
    del d["__builtins__"] # somehow this gets in here.
    return d

def seq2tuple(t):
    return (257, t, (0,''))

def eval_seq(t, d=None):
    if d is None:
        d = {}
    ast = parser.sequence2ast( (257, t, (0, '')) )
    co = ast.compile()
    py_eval(co, d, d)
    del d["__builtins__"]
    return d


def match(pattern, data, vars=None):
    if vars is None:
        vars = {}
    if type(pattern) is list:      # 'variables' are ['varname']
        vars[pattern[0]] = data
        return 1, vars
    if type(pattern) is not tuple:
        return (pattern == data), vars
    for pattern, data in zip(pattern, data):
        same, vars = match(pattern, data, vars)
        if not same:
            break
    return same, vars


def match_all(patt, tree):
    rl = []
    for st in tree[1:]:
        rv, d = match(patt, st)
        if rv:
            rl.append(d)
    return rl


# following is experimental, it does not currently work. copied from
# tabnanny. The idea here is to make vim have a built-in tabnanny...

def errprint(*args):
    sep = ""
    for arg in args:
        sys.stderr.write(sep + str(arg))
        sep = " "
    sys.stderr.write("\n")

class NannyNag(Exception):
    """
    Raised by tokeneater() if detecting an ambiguous indent.
    Captured and handled in check().
    """
    def __init__(self, lineno, msg, line):
        self.lineno, self.msg, self.line = lineno, msg, line
    def get_lineno(self):
        return self.lineno
    def get_msg(self):
        return self.msg
    def get_line(self):
        return self.line

def check(fo):
    try:
        process_tokens(tokenize.generate_tokens(fo.readline))

    except tokenize.TokenError, msg:
        errprint("Token Error: %s" % (str(msg)))
        return

    except NannyNag, nag:
        badline = nag.get_lineno()
        line = nag.get_line()
        print "*** Questionable tabbing on line %d ***" % (badline)
        current.window.cursor = (badline, 0)
        normal("z.")
        #print nag.get_msg()
        return 0

    print "Indents look ok."
    return 1

class Whitespace:
    # the characters used for space and tab
    S, T = ' \t'

    # members:
    #   raw
    #      the original string
    #   n
    #      the number of leading whitespace characters in raw
    #   nt
    #      the number of tabs in raw[:n]
    #   norm
    #      the normal form as a pair (count, trailing), where:
    #      count
    #          a tuple such that raw[:n] contains count[i]
    #          instances of S * i + T
    #      trailing
    #          the number of trailing spaces in raw[:n]
    #      It's A Theorem that m.indent_level(t) ==
    #      n.indent_level(t) for all t >= 1 iff m.norm == n.norm.
    #   is_simple
    #      true iff raw[:n] is of the form (T*)(S*)

    def __init__(self, ws):
        self.raw  = ws
        S, T = Whitespace.S, Whitespace.T
        count = []
        b = n = nt = 0
        for ch in self.raw:
            if ch == S:
                n = n + 1
                b = b + 1
            elif ch == T:
                n = n + 1
                nt = nt + 1
                if b >= len(count):
                    count = count + [0] * (b - len(count) + 1)
                count[b] = count[b] + 1
                b = 0
            else:
                break
        self.n  = n
        self.nt   = nt
        self.norm = tuple(count), b
        self.is_simple = len(count) <= 1

    # return length of longest contiguous run of spaces (whether or not
    # preceding a tab)
    def longest_run_of_spaces(self):
        count, trailing = self.norm
        return max(len(count)-1, trailing)

    def indent_level(self, tabsize):
        # count, il = self.norm
        # for i in range(len(count)):
        #   if count[i]:
        #       il = il + (i/tabsize + 1)*tabsize * count[i]
        # return il

        # quicker:
        # il = trailing + sum (i/ts + 1)*ts*count[i] =
        # trailing + ts * sum (i/ts + 1)*count[i] =
        # trailing + ts * sum i/ts*count[i] + count[i] =
        # trailing + ts * [(sum i/ts*count[i]) + (sum count[i])] =
        # trailing + ts * [(sum i/ts*count[i]) + num_tabs]
        # and note that i/ts*count[i] is 0 when i < ts

        count, trailing = self.norm
        il = 0
        for i in range(tabsize, len(count)):
            il = il + i/tabsize * count[i]
        return trailing + tabsize * (il + self.nt)

    # return true iff self.indent_level(t) == other.indent_level(t)
    # for all t >= 1
    def equal(self, other):
        return self.norm == other.norm

    # return a list of tuples (ts, i1, i2) such that
    # i1 == self.indent_level(ts) != other.indent_level(ts) == i2.
    # Intended to be used after not self.equal(other) is known, in which
    # case it will return at least one witnessing tab size.
    def not_equal_witness(self, other):
        n = max(self.longest_run_of_spaces(),
                other.longest_run_of_spaces()) + 1
        a = []
        for ts in range(1, n+1):
            if self.indent_level(ts) != other.indent_level(ts):
                a.append( (ts,
                           self.indent_level(ts),
                           other.indent_level(ts)) )
        return a

    # Return true iff self.indent_level(t) < other.indent_level(t)
    # for all t >= 1.
    # The algorithm is due to Vincent Broman.
    # Easy to prove it's correct.
    # XXXpost that.
    # Trivial to prove n is sharp (consider T vs ST).
    # Unknown whether there's a faster general way.  I suspected so at
    # first, but no longer.
    # For the special (but common!) case where M and N are both of the
    # form (T*)(S*), M.less(N) iff M.len() < N.len() and
    # M.num_tabs() <= N.num_tabs(). Proof is easy but kinda long-winded.
    # XXXwrite that up.
    # Note that M is of the form (T*)(S*) iff len(M.norm[0]) <= 1.
    def less(self, other):
        if self.n >= other.n:
            return 0
        if self.is_simple and other.is_simple:
            return self.nt <= other.nt
        n = max(self.longest_run_of_spaces(),
                other.longest_run_of_spaces()) + 1
        # the self.n >= other.n test already did it for ts=1
        for ts in range(2, n+1):
            if self.indent_level(ts) >= other.indent_level(ts):
                return 0
        return 1

    # return a list of tuples (ts, i1, i2) such that
    # i1 == self.indent_level(ts) >= other.indent_level(ts) == i2.
    # Intended to be used after not self.less(other) is known, in which
    # case it will return at least one witnessing tab size.
    def not_less_witness(self, other):
        n = max(self.longest_run_of_spaces(),
                other.longest_run_of_spaces()) + 1
        a = []
        for ts in range(1, n+1):
            if self.indent_level(ts) >= other.indent_level(ts):
                a.append( (ts,
                           self.indent_level(ts),
                           other.indent_level(ts)) )
        return a

def format_witnesses(w):
    import string
    firsts = map(lambda tup: str(tup[0]), w)
    prefix = "at tab size"
    if len(w) > 1:
        prefix = prefix + "s"
    return prefix + " " + string.join(firsts, ', ')

def process_tokens(tokens):
    INDENT = tokenize.INDENT
    DEDENT = tokenize.DEDENT
    NEWLINE = tokenize.NEWLINE
    JUNK = tokenize.COMMENT, tokenize.NL
    indents = [Whitespace("")]
    check_equal = 0

    for (type, token, start, end, line) in tokens:
        if type == NEWLINE:
            # a program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #    (NL | COMMENT)* (INDENT | DEDENT+)?
            # If an INDENT appears, setting check_equal is wrong, and will
            # be undone when we see the INDENT.
            check_equal = 1

        elif type == INDENT:
            check_equal = 0
            thisguy = Whitespace(token)
            if not indents[-1].less(thisguy):
                witness = indents[-1].not_less_witness(thisguy)
                msg = "indent not greater e.g. " + format_witnesses(witness)
                raise NannyNag(start[0], msg, line)
            indents.append(thisguy)

        elif type == DEDENT:
            # there's nothing we need to check here!  what's important is
            # that when the run of DEDENTs ends, the indentation of the
            # program statement (or ENDMARKER) that triggered the run is
            # equal to what's left at the top of the indents stack

            # Ouch!  This assert triggers if the last line of the source
            # is indented *and* lacks a newline -- then DEDENTs pop out
            # of thin air.
            # assert check_equal  # else no earlier NEWLINE, or an earlier INDENT
            check_equal = 1

            del indents[-1]

        elif check_equal and type not in JUNK:
            # this is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER; the "line" argument exposes the leading whitespace
            # for this statement; in the case of ENDMARKER, line is an empty
            # string, so will properly match the empty string with which the
            # "indents" stack was seeded
            check_equal = 0
            thisguy = Whitespace(line)
            if not indents[-1].equal(thisguy):
                witness = indents[-1].not_equal_witness(thisguy)
                msg = "indent not equal e.g. " + format_witnesses(witness)
                raise NannyNag(start[0], msg, line)

