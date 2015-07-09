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
Widgets for test cases.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


import sys
import urwid

from pycopia.aid import NULL

from . import walkers
from .treewidgets import *

DEBUG = NULL

### shorthand notation
AM = urwid.AttrMap


PALETTE = [
    ('body','default', 'default'),
    ('popup','black','light gray', 'standout'),
    ('top','default', 'default'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('enumbuttn','black','yellow'),
    ('buttn','black','dark cyan'),
    ('formbuttn','black','dark green'),
    ('formbuttnf','white','dark blue','bold'),
    ('buttnimportant','black','dark magenta', ("bold", "standout")),
    ('buttnimportantf','white','dark magenta', ("bold", "standout")),
    ('buttnf','white','dark blue','bold'),
    ('dirmark', 'black', 'dark cyan', 'bold'),
    ('editbx','light gray', 'dark blue'),
    ('editcp','black','light gray', 'standout'),
    ('editfc','white', 'dark blue', 'bold'),
    ('error', 'black', 'dark red'),
    ('flag', 'dark gray', 'light gray'),
    ('flagged', 'black', 'dark green', ('bold','underline')),
    ('flagged focus', 'yellow', 'dark cyan', ('bold','standout','underline')),
    ('butfocus', 'light gray', 'dark blue', 'standout'),
    ('focus','white','default','bold'),
    ('focustext','light gray','dark blue'),
    ('foot', 'light gray', 'black'),
    ('head', 'white', 'black', 'standout'),
    ('formhead', 'dark blue', 'light gray', 'standout'),
    ('subhead', 'yellow', 'black', 'standout'),
    ('important','light magenta','default',('standout','underline')),
    ('key', "black", 'light cyan', 'underline'),
    ('collabel','light gray','black'),
    ('coldivider','light blue','black'),
    ('notnulllabel','light magenta','black'),
    ('selectable','black', 'dark cyan'),
    ('notimplemented', 'dark red', 'black'),
    ('deleted', 'dark red', 'black'),
    ('title', 'white', 'black', 'bold'),
    ('colhead', 'yellow', 'black', 'default'),
    # reports
    ('repinfo', 'dark gray', 'black', 'standout'),
    ('reppass', 'light green', 'black', 'standout'),
    ('repfail', 'light red', 'black', 'standout'),
    ('repexpfail', 'dark red', 'black', 'standout'),
    ('repincomplete', 'yellow', 'black', 'standout'),
    ('repabort', 'light cyan', 'black', 'standout'),
    ('repdiag', 'light magenta', 'black', 'underline'),
    ('repmsg', 'dark blue', 'black'),
    # testtree
    ('treetc', 'yellow', 'black', 'default'),
    ('treeuc', 'light green', 'black', 'default'),
    ('treemod', 'white', 'black', 'default'),
    ('treefocus','white','dark gray','bold'),
]

#                  LT   TOP   SIDE  TR    BL    BR
_BOXCHARS = {1: [u'┏', u'━', u'┃', u'┓', u'┗', u'┛',],
             2: [u'╔', u'═', u'║', u'╗', u'╚', u'╝',],
             3: [u'┌', u'─', u'│', u'┐', u'└', u'┘',],
}

def get_linebox(wid, level, title=""):
    lt, top, side, tr, bl, br = _BOXCHARS[level]
    return urwid.LineBox(wid, title, tlcorner=lt, tline=top, lline=side,
            trcorner=tr, blcorner=bl, rline=side, bline=top, brcorner=br)



class PackageNode(urwid.WidgetWrap):
    def __init__(self, name):
        t = urwid.Text(name)
        w = urwid.AttrMap(t, 'body', 'focus')
        urwid.WidgetWrap.__init__(self, w)



class Runnable(urwid.WidgetWrap):
    signals = ["activate"]
    STYLE = "white"
    def __init__ (self, path, runnable=True, on_activate=None, user_data=None):
        self._path = path
        w = AM(urwid.Text(path.split(".")[-1]), self.STYLE, 'treefocus')
        self.__super.__init__(w)
        self._runnable = runnable
        if on_activate is not None:
            urwid.connect_signal(self, "activate", on_activate, user_data)

    @property
    def name(self):
        return self._path

    @property
    def runnable(self):
        return self._runnable

    def selectable(self):
        return self._runnable

    def keypress(self, size, key):
        try:
            if self._w.keypress(size, key) is None:
                return
        except AttributeError:
            pass
        if self._command_map[key] == 'activate':
            self._emit('activate')
            return None
        else:
            return key


class ModuleNode(Runnable):
    STYLE = "treemod"


class TestCaseNode(Runnable):
    STYLE = "treetc"


class UseCaseNode(Runnable):
    STYLE = "treeuc"



class MenuItemWidget(urwid.WidgetWrap):
    signals = ["activate"]

    def __init__ (self, text, on_activate=None, user_data=None):
        w = AM(urwid.Text(text), 'body', 'focus')
        self.__super.__init__(w)
        if on_activate is not None:
            urwid.connect_signal(self, "activate", on_activate, user_data)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._command_map[key] != 'activate':
            return key
        self._emit('activate')

    @property
    def label(self):
        return self._w.base_widget.text


class ListEntry(urwid.WidgetWrap):
    signals = ["activate", "delete"]

    def __init__ (self, text, data=None):
        w = AM(urwid.Text(text), 'body', 'focus')
        self.__super.__init__(w)
        self._data = data

    def selectable(self):
        return True

    def keypress(self, size, key):
        try:
            if self._w.keypress(size, key) is None:
                return
        except AttributeError:
            pass
        if self._command_map[key] != 'activate':
            if key == "delete":
                self._emit('delete')
                return None
            else:
                return key
        self._emit('activate')

    @property
    def data(self):
        return self._data


class Form(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["pushform", "popform", "message"]



class ModuleTreeWalker(walkers.TreeWalker):

    def __init__(self, modtree, **kwargs):
        self._modtree = modtree
        self.root = ("testcases",)
        super(ModuleTreeWalker, self).__init__(**kwargs)

#    def depth(self, pos):
#        parent = self.parent_position(pos)
#        if parent is None:
#            return 0
#        else:
#            return self.depth(parent) + 1

    def _get_subtree(self, treelist, path):
        subtree = None
        if len(path) > 1:
            subtree = self._get_subtree(treelist[path[0]], path[1:])
        else:
            try:
                subtree = treelist[path[0]]
            except KeyError:
                pass
        return subtree

    def _get_node(self, modtree, path):
        """look up widget at `path` of `treelist`; default to None if nonexistent."""
        node = None
        if path is not None:
            subtree = self._get_subtree(treelist, path)
            if subtree is not None:
                node = subtree[0]
        return node

    def _confirm_pos(self, pos):
        """look up widget for pos and default to None"""
        candidate = None
        if self._get_node(self._treelist, pos) is not None:
            candidate = pos
        return candidate

    def __getitem__(self, pos):
        DEBUG("mtw getitem", pos)
        return self._get_node(self._modtree, pos)

    def parent_position(self, pos):
        DEBUG("mtw parent_position", pos)
        parent = None
        if pos is not None:
            if len(pos) > 1:
                parent = pos[:-1]
        return parent

    def first_child_position(self, pos):
        DEBUG("mtw first_child_position", pos)
        return self._confirm_pos(pos)

    def last_child_position(self, pos):
        DEBUG("mtw last_child_position", pos)
        candidate = None
        subtree = self._get_subtree(self._treelist, pos)
        if subtree is not None:
            children = subtree[subtree.keys()[-1]]
            if children is not None:
                candidate = pos + (len(children) - 1,)
        return candidate

    def next_sibling_position(self, pos):
        DEBUG("mtw next_sibling_position", pos)
        return self._confirm_pos(pos[:-1] + (pos[-1] + 1,))

    def prev_sibling_position(self, pos):
        DEBUG("mtw prev_sibling_position", pos)
        return pos[:-1] + (pos[-1] - 1,) if (pos[-1] > 0) else None




class ListScrollSelector(urwid.Widget):
    _selectable = True
    _sizing = frozenset(['flow'])
    signals = ["click", "change"]
    UPARR=u"↑"
    DOWNARR=u"↓"

    def __init__(self, choicelist):
        self.__super.__init__()
        self._list = choicelist
        self._prefix = ""
        self._max = len(choicelist)
        assert self._max > 0, "Need list with at least one element"
        self._index = 0
        self.set_text(self._list[self._index])
        maxwidth = reduce(lambda c,m: max(c,m), map(lambda o: len(str(o)), choicelist), 0)
        self._fmt = u"{} {{:{}.{}s}} {}".format(self.UPARR, maxwidth, maxwidth, self.DOWNARR)

    def keypress(self, size, key):
        cmd =  self._command_map[key]
        if cmd == 'cursor up':
            self._prefix = ""
            self._index = (self._index - 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == 'cursor down':
            self._prefix = ""
            self._index = (self._index + 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == "activate":
            self._emit("click")
        elif key == "backspace":
            self._prefix = self._prefix[:-1]
        elif len(key) == 1 and key.isalnum():
            self._prefix += key
            i = self.prefix_index(self._list, self._prefix, self._index + 1)
            if i is not None:
                self._index = i
                self.set_text(self._list[i])
        else:
            return key

    @staticmethod
    def prefix_index(thelist, prefix, index=0):
        while index < len(thelist):
            if thelist[index].startswith(prefix):
                return index
            index += 1
        return None

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        (maxcol,) = size
        text = self._fmt.format(self._text).encode("utf-8")
        c = urwid.TextCanvas([text], maxcol=maxcol)
        c.cursor = self.get_cursor_coords(size)
        return c

    def set_text(self, text):
        self._text = text
        self._invalidate()
        self._emit("change")

    def get_cursor_coords(self, size):
        return None

    @property
    def value(self):
        return self._list[self._index]



class OptionInput(urwid.WidgetWrap):
    signals = ["update", "pushform", "message"]
    def __init__(self):
        wid = self.build()
        self.__super.__init__(wid)

    def build(self):
        wlist = []
        addnew = urwid.Button("Add")
        urwid.connect_signal(addnew, 'click', self._add_new_option)
        addnew = urwid.AttrWrap(addnew, 'selectable', 'butfocus')
        wlist.append(addnew)
        for attrib in getattr(self.row, self.metadata.colname): # list-like attribute
            entry = ListEntry(urwid.Columns(
                    [(30, urwid.Text(str(attrib.type))),
                     urwid.Text(unicode(attrib.value).encode("utf-8"))]))
            entry.attrname = attrib.type.name
            urwid.connect_signal(entry, 'activate', self._edit_option)
            urwid.connect_signal(entry, 'delete', self._delete)
            wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), max(7, len(wlist)+2))

    def _add_new_option(self, b):
        pass

    def _edit_option(self, b):
        pass

    def _delete(self, b):
        pass

## XXXX testing only below here

def construct_example_tree(selectable_nodes=True):

    class FocusableText(urwid.WidgetWrap):
        """Selectable Text used for nodes in our example"""
        def __init__(self, txt):
            t = urwid.Text(txt)
            w = urwid.AttrMap(t, 'body', 'focus')
            urwid.WidgetWrap.__init__(self, w)

        def selectable(self):
            return selectable_nodes

        def keypress(self, size, key):
            return key

    # define root node
    tree = (FocusableText('ROOT'), [])

    # define some children
    c = g = gg = 0  # counter
    for i in range(4):
        subtree = (FocusableText('Child %d' % c), [])
        # and grandchildren..
        for j in range(2):
            subsubtree = (FocusableText('Grandchild %d' % g), [])
            for k in range(3):
                leaf = (FocusableText('Grand Grandchild %d' % gg), None)
                subsubtree[1].append(leaf)
                gg += 1  # inc grand-grandchild counter
            subtree[1].append(subsubtree)
            g += 1  # inc grandchild counter
        tree[1].append(subtree)
        c += 1
    return tree


class TestForm(Form):

    def __init__(self, title, contents):
        display_widget = self.build(title, contents)
        self.__super.__init__(display_widget)

    def unhandled_input(self, k):
        if k == "esc":
            raise urwid.ExitMainLoop()
        DEBUG("unhandled key:", k)

    def run(self):
        loop = urwid.MainLoop(self._w, PALETTE, unhandled_input=self.unhandled_input, #pop_ups=True,
                event_loop=eventloop.PycopiaEventLoop())
        loop.run()

    def build(self, title, contents):
        header = AM(urwid.Text(title), 'header')
        #clist = self._build_tree(contents)
        #listbox = urwid.TreeWalker(PackageNode(contents[0]))
        #listbox = urwid.TreeListBox(urwid.TreeWalker(PackageNode(contents[0])))
        #return urwid.Frame(AM(urwid.Filler(urwid.Text("Sample")), 'body'), header=header)
        #treelist = CollapsibleArrowTreeListWalker([ListEntry(e) for e in contents])
        #mtw = ModuleTreeWalker([ListEntry(e) for e in contents])

# define a list of trees to be passed on to SimpleTreeWalker
        forrest = [construct_example_tree()]
# stick out test tree into a SimpleTreeWalker
        swalker = walkers.SimpleTreeWalker(forrest)

        if_grandchild = lambda pos: swalker.depth(pos) > 1
        treelist = CollapsibleIndentedTreeListWalker(swalker,
        #treelist = CollapsibleArrowTreeListWalker(swalker,
                       is_collapsed=if_grandchild,
                       #indent=6,
                       #childbar_offset=1,
                       selectable_icons=True,
                       icon_focussed_att='focus',
                       #icon_frame_left_char=None,
                       #icon_frame_right_char=None,
                       #icon_expanded_char='-',
                       #icon_collapsed_char='+',
                )
        #return urwid.Frame(AM(treebox, 'body'), header=header)

        wlist = [ListEntry(e) for e in contents]
        listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))

        treebox = TreeBox(treelist)
        #return urwid.Frame(AM(treebox, 'body'), header=header)

        return urwid.Pile([urwid.LineBox(listbox), urwid.LineBox(treebox)])


    def _build_tree(self, contents):
        return [] # XXX

def _test(argv):

    #pprint(construct_example_tree())
    TCLIST = [
            "testcases.unittests.process.expect",
            "testcases.unittests.process.expect.BasicExpect",
            "testcases.unittests.process.expect.TimeoutExpect",
            "testcases.unittests.storage.imported",
            "testcases.unittests.core.scheduler",
            "testcases.unittests.core.scheduler.BasicSleepTest",
            "testcases.unittests.core.scheduler.BasicTimer",
    ]
    app = TestForm("Test Form", TCLIST)
    print(app.run())


if __name__ == "__main__":
    from pprint import pprint
    from pycopia.db.tui import eventloop
    from pycopia import autodebug
    from pycopia import logwindow
    DEBUG = logwindow.DebugLogWindow()
    walkers.DEBUG = DEBUG
    _test(sys.argv)

