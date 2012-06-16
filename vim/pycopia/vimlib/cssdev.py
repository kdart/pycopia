#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Vim module for editing CSS.
"""

try:
    import vim
except ImportError:
    # for running outside of vim when testing
    import pycopia.vimlib.vimtest as vim

from pycopia import gtktools


def edit_color_visual_selection():
    """Spawn a color selector with the current hex coded color, and replaces it
    with the newly selected color.
    """
    b = vim.current.buffer
    start_row, start_col = b.mark("<")
    end_row, end_col = b.mark(">")
    if start_row == end_row:
        l = b[start_row-1]
        t = l[start_col:end_col+1]
        t = gtktools.color_select(t)
        b[start_row-1] = l[:start_col]+t+l[end_col+1:]


