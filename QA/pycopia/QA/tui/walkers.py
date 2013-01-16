# Copyright (C) 2012  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU LGPL, version 2.1 or a later revision.

class TreeWalker(object):
    """
    Content provider for tree structures. Base class for a structured walk
    over acyclic graphs that can be displayed by :class:`TreeBox` widgets.

    Subclasses may implement methods
     * `next_sibling_position`
     * `prev_sibling_position`
     * `parent_position`
     * `first_child_position`
     * `last_child_position`

     that compute the next position in the respective direction. Also, they
     need to implement method `__getitem__` that returns a widget for a given position.

     The type of objects used as positions may vary in subclasses and is deliberately
     unspecified for the base class.
    """
    root = None

    # local helper
    def _get(self, pos):
        """loads widget at given position; handling invalid arguments"""
        res = None, None
        if pos is not None:
            try:
                res = self[pos], pos
            except (IndexError, KeyError):
                pass
        return res

    def _last_in_direction(self, starting_pos, direction):
        """
        recursively move in the tree in given direction
        and return the last position.

        :param starting_pos: position to start in
        :param direction: callable that transforms a position into a position.
        """
        next_pos = direction(starting_pos)
        if next_pos is None:
            return starting_pos
        else:
            return self._last_in_direction(next_pos, direction)

    def depth(self, pos):
        """determine depth of node at pos"""
        parent = self.parent_position(pos)
        if parent is None:
            return 0
        else:
            return self.depth(parent) + 1

    def first_ancestor(self, pos):
        """
        position of pos's ancestor with depth 0.  usually, this should return
        the root node, but a Walker might represent a Forrest - have multiple
        nodes without parent.
        """
        return self._last_in_direction(pos, self.parent_position)

    def last_decendant(self, pos):
        """position of last (in DFO) decendant of pos"""
        return self._last_in_direction(pos, self.last_child_position)

    def last_sibling_position(self, pos):
        """position of last sibling of pos"""
        return self._last_in_direction(pos, self.next_sibling_position)

    def first_sibling_position(self, pos):
        """position of first sibling of pos"""
        return self._last_in_direction(pos, self.prev_sibling_position)

    # To be overwritten by subclasses
    def parent_position(self, pos):
        """returns the position of the parent node of the node at `pos`
        or `None` if none exists."""
        return None

    def first_child_position(self, pos):
        """returns the position of the first child of the node at `pos`,
        or `None` if none exists."""
        return None

    def last_child_position(self, pos):
        """returns the position of the last child of the node at `pos`,
        or `None` if none exists."""
        return None

    def next_sibling_position(self, pos):
        """returns the position of the next sibling of the node at `pos`,
        or `None` if none exists."""
        return None

    def prev_sibling_position(self, pos):
        """returns the position of the previous sibling of the node at `pos`,
        or `None` if none exists."""
        return None


class CachingTreeWalker(TreeWalker):
    """TreeWalker that caches its contained widgets"""
    def __init__(self, load_widget):
        """
        :param load_widget: a callable that returns a Widget for given position
        """
        TreeWalker.__init__(self)
        self._content = {}
        self._load_widget = load_widget

    def __getitem__(self, pos):
        if pos not in self._content:
            widget = self._load_widget(pos)
            if widget is None:
                raise IndexError
            self._content[pos] = widget
        return self._content[pos]


class SimpleTreeWalker(TreeWalker):
    """
    Walks on a given fixed acyclic structure.
    The structure needs to be a list of nodes; every node is a tuple `(widget,
    children)`, where widget is a urwid.Widget to be displayed at that position
    and children is either `None` or a list of nodes.

    Positions are lists of integers determining a path from toplevel node.
    """
    def __init__(self, treelist, **kwargs):
        self._treelist = treelist
        self.root = (0,) if treelist else None
        TreeWalker.__init__(self, **kwargs)

    # a few local helper methods
    def _get_subtree(self, treelist, path):
        """recursive helper to look up node-tuple for `path` in `treelist`"""
        subtree = None
        if len(path) > 1:
            subtree = self._get_subtree(treelist[path[0]][1], path[1:])
        else:
            try:
                subtree = treelist[path[0]]
            except (IndexError, TypeError):
                pass
        return subtree

    def _get_node(self, treelist, path):
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

    # TreeWalker API
    def __getitem__(self, pos):
        return self._get_node(self._treelist, pos)

    def parent_position(self, pos):
        parent = None
        if pos is not None:
            if len(pos) > 1:
                parent = pos[:-1]
        return parent

    def first_child_position(self, pos):
        return self._confirm_pos(pos + (0,))

    def last_child_position(self, pos):
        candidate = None
        subtree = self._get_subtree(self._treelist, pos)
        if subtree is not None:
            children = subtree[1]
            if children is not None:
                candidate = pos + (len(children) - 1,)
        return candidate

    def next_sibling_position(self, pos):
        return self._confirm_pos(pos[:-1] + (pos[-1] + 1,))

    def prev_sibling_position(self, pos):
        return pos[:-1] + (pos[-1] - 1,) if (pos[-1] > 0) else None

    # optimizations
    def depth(self, pos):
        """more performant implementation due to specific structure of pos"""
        return len(pos) - 1
