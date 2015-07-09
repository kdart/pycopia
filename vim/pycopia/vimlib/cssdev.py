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


