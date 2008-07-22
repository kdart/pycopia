#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Functions to make editing [X]HTML files in vim more productive.

try:
    import vim
except ImportError:
    from pycopia.vimlib import vimtest as vim

import sys, os, re

from pycopia.WWW import XHTML
from pycopia.dtds import xhtml1_strict as DTD

from cStringIO import StringIO
from pycopia.XML.POM import escape, unescape, Comment, BeautifulWriter



def xml_format(obj):
    s = StringIO()
    w = BeautifulWriter(s)
    obj.emit(w)
    return s.getvalue()

def vimstring(obj):
    return unicode(str(obj), vim.eval("&fileencoding") or vim.eval("&encoding"))

def htmlify():
    vim.current.line = escape(vim.current.line).encode("ascii")

def text_to_table():
    table = DTD.Table()
    for line in vim.current.range:
        tr = table.add(DTD.Tr)
        for item in line.split("\t"):
            td = tr.add(DTD.Td)
            td.add_text(item)
    vim.current.range[:] = str(table).split("\n")

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

def _append(obj):
    vim.current.range.append(str(obj))

def _replace(obj):
    vim.current.range[:] = str(obj).split("\n")

def _replace_line(obj):
    vim.current.line = str(obj)

def commentline():
    vim.current.line = str(Comment(vim.current.line))

def comment_visual_selection():
    b = vim.current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        l = b[start_row-1]
        c = str(Comment(l[start_col:end_col+1]))
        b[start_row-1] = l[:start_col]+c+l[end_col+1:]
    else:
        b[start_row-1:end_row] = str(Comment("\n".join(b[start_row-1:end_row]))).split("\n") # XXX partial lines

def block_visual_selection(objname):
    obj = getattr(DTD, objname)
    b = vim.current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        l = b[start_row-1]
        c = str(obj(l[start_col:end_col+1]))
        b[start_row-1] = l[:start_col]+c+l[end_col+1:]
    else:
        b[start_row-1:end_row] = str(obj("\n".join(b[start_row-1:end_row]))).split("\n") # XXX partial lines


def _list(lobj):
    r = vim.current.range
    for l in r:
        li = DTD.Li()
        li.add_text(l)
        lobj.append(li)
    r[:] = xml_format(lobj).split("\n")

def unordered_list():
    _list(DTD.Ul())

def ordered_list():
    _list(DTD.Ol())


