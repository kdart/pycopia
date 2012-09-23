#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <kdart@kdart.com>

"""
This module is intended for use with the Vim editor. It provides
additional functionality to vim in general, but also some functions
designed specifically for editing other python source files.

1. Adds more advanced functionality and commands to Vim
2. Enables more convenient Python program development (makes Vim a Python IDE)

"""

from __future__ import print_function

try:
    import vim
except ImportError:
    # for running outside of vim
    import pycopia.vimlib.vimtest as vim

# buffers command current error eval windows

import sys, os
import re
import ast
import cStringIO as StringIO

from pycopia import devenviron
from pycopia import devhelpers
from pycopia import textutils


XTERM = os.environ.get("XTERM", "rxvt -e")
EXECTEMP = "/var/tmp/python_vim_temp_%s.py" % (os.getpid())

re_def = re.compile(r"^[ \t]*def ")
re_class = re.compile(r"^[ \t]*class ")
re_klass_export = re.compile(r"^class ([a-zA-Z][a-zA-Z0-9_]*)")
re_def_export = re.compile(r"^def ([a-zA-Z][a-zA-Z0-9_]*)")

# pull in these to local namespace for menus.
pyterm = devhelpers.pyterm
xterm = devhelpers.xterm

def normal(str):
    vim.command("normal "+str)

def test_count():
    print (int(vim.eval("v:count")))

def str_range(vrange):
    return vrange.join("\n") + "\n"

def exec_vimrange(vrange):
    exec str_range(vrange)

def exec_vimrange_in_term(vrange):
    tf = open(EXECTEMP , "w")
    tf.write(str_range(vrange))
    tf.close()
    devhelpers.run_config(XTERM, "python -i %s" % (EXECTEMP))

def insert_viminfo():
    """Insert a vim line with tabbing related settings reflecting current settings."""
    # The following line is to prevent this vim from interpreting it as a real
    # v-i-m tagline.
    vi = ["# %s" % ("".join(['v','i','m']),)]
    for var in ('ts', 'sw', 'softtabstop'):
        vi.append("%s=%s" % (var, vim.eval("&%s" % (var,))))
    for var in ('smarttab', 'expandtab'):
        if int(vim.eval("&%s" % var)):
            vi.append(var)
    if vim.eval("&ft") != "python":
        vi.append("ft=python")
    vim.current.range.append(":".join(vi))

def insert__all__():
    path, name = os.path.split(vim.current.buffer.name)
    if name == "__init__.py":
        insert__all__pkg(path)
    else:
        insert__all__mod()

def insert__all__mod():
    klasses = []
    funcs = []
    for line in vim.current.buffer:
        mo = re_klass_export.search(line)
        if mo:
            klasses.append(mo.group(1))
        mo = re_def_export.search(line)
        if mo:
            funcs.append(mo.group(1))
    vim.current.range.append("__all__ = [%s]" % (", ".join(map(repr, klasses+funcs))))

def insert__all__pkg(path):
    files = textutils.grep ("^[A-Za-z]+\\.py$", os.listdir(path))
    res = []
    for name, ext in map(os.path.splitext, files):
        res.append(name)
    vim.current.range.append("__all__ = [%s]" % (", ".join(map(repr, res))))


def balloonhelp():
    try:
        result = eval(vim.eval("v:beval_text")).__doc__
        if result is None:
            return "No doc."
        result = result.replace("\0", " ")
        result = result.replace('"', '\\"')
        return2vim(result)
    except:
        ex, val, tb = sys.exc_info()
        print(str(val))
        return2vim("")

# XXX is this hack really necessary?
def return2vim(val):
    vim.command('let g:python_rv = "%s"' % (val,))

# utility functions

def htmlhex(text):
    return "".join(map(lambda c: "%%%x" % (ord(c),), text))

def htmlhex_visual_selection():
    b = vim.current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        l = b[start_row-1]
        c = htmlhex(l[start_col:end_col+1])
        b[start_row-1] = l[:start_col]+c+l[end_col+1:]
    else:
        b[start_row-1:end_row] = htmlhex("\n".join(b[start_row-1:end_row])).split("\n") # XXX partial lines

def keyword_help():
    devhelpers.showdoc(vim.eval('expand("<cword>")'))

def keyword_edit():
    devhelpers.edit(vim.eval('expand("<cword>")'))

def import_edit():
    devhelpers.edit_import_line(vim.current.line)

def keyword_view():
    devhelpers.view(vim.eval('expand("<cword>")'))

def keyword_split():
    modname = vim.eval('expand("<cword>")')
    filename = devhelpers.find_source_file(modname)
    if filename is not None:
        vim.command("split %s" % (filename,))
    else:
        print("Could not find source to %s." % modname, file=sys.stderr)

def visual_edit():
    text = get_visual_selection()
    if "\n" in text:
        print("bad selection")
    else:
        devhelpers.edit(text)

def visual_view():
    text = get_visual_selection()
    if "\n" in text:
        print("bad selection")
    else:
        devhelpers.view(text)

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


