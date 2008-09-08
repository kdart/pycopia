#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Functions to make editing [X]HTML files in vim more productive.

# The following allows testing this module outside of a vim editor.
# The vimtest module is a mock of the internal vim module.
try:
    import vim
except ImportError:
    from pycopia.vimlib import vimtest as vim

from pycopia.dtds import xhtml1_strict as DTD

from cStringIO import StringIO
from pycopia.XML.POM import escape, unescape, Comment, BeautifulWriter


def xml_format(obj):
    s = StringIO()
    w = BeautifulWriter(s)
    obj.emit(w, get_encoding())
    return s.getvalue()

def get_encoding():
    # return current documents character encoding.
    return vim.eval("&fileencoding") or vim.eval("&encoding")

def htmlify():
    vim.current.range[:] = escape("\n".join(vim.current.range)).encode(get_encoding()).split("\n")

def unhtmlify():
    vim.current.range[:] = unescape("\n".join(vim.current.range)).encode(get_encoding()).split("\n")

def text_to_table():
    table = DTD.Table()
    head = table.add(DTD.Thead)
    body = table.add(DTD.Tbody)
    linecount = 0
    for line in vim.current.range:
        columns = line.split("\t")
        if len(columns) == 0:
            continue
        elif len(columns) == 1:
            cap = DTD.Caption()
            cap.add_text(columns[0])
            table.insert(0, cap)
        else:
            if linecount >= 1:
                tr = body.add(DTD.Tr)
                rc = DTD.Td
            else:
                tr = head.add(DTD.Tr)
                rc = DTD.Th
            for item in columns:
                cell = tr.add(rc)
                cell.add_text(item)
            linecount += 1
    vim.current.range[:] = xml_format(table).split("\n")

def _append(obj):
    vim.current.range.append(unicode(obj, get_encoding()))

def _replace(obj):
    vim.current.range[:] = unicode(obj, get_encoding()).split("\n")

def _replace_line(obj):
    vim.current.line = unicode(obj, get_encoding())

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
        # collect source text
        lines = b[start_row:end_row-1]
        lines.insert(0, b[start_row-1][start_col:])
        lines.append(b[end_row-1][:end_col+1])
        # comment and escape source text.
        newlines = xml_format(Comment("\n".join(lines))).split("\n")
        # replace source with new text.
        b[start_row-1] = b[start_row-1][:start_col] + newlines[0]
        b[start_row:end_row-1] = newlines[1:-1]
        b[end_row-1] = newlines[-1] + b[end_row-1][end_col+1:]


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


