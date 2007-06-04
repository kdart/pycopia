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
Objects for representing tabular data.

"""

### A general class for tabular data, with provisions for report
# generation. Implemented as nested lists, with row and column names as
# lists.
#
#  headings  =  [ ...  ]
#       data = [[ ...  ],
#               [ ...  ],
#               [ ...  ], ... ]
# rownames = [...,
#             ...,
#             ...]

class GenericTable(object):
    """GenericTable([initializer], [default=None])
A two-dimensional table of objects."""
    def __init__(self, obj=None, default=None, title=None):
        self.default = default # default value is value for "empty" cells
        self.title = title
        if obj is None:
            self._newtable((0,0))
        elif isinstance(obj, self.__class__):
            self.data = obj.data[:]
            self.headings = obj.headings[:]
            self.rownames = obj.rownames[:]
        elif type(obj) is tuple: # a tuple with the dimensions
            self._newtable(obj)
        elif type(obj) is list: # create table from heading list
            self.headings = obj[:]
            self.x = len(self.headings)
            self.clear()
        else:
            raise ValueError, "%s: bad table initializer" % self.__class__.__name__

    def _newtable(self, sizetuple):
        self.data = []
        self.rownames = []
        x, y = sizetuple
        self.headings = ['']*x
        for n in xrange(y):
            self.data.append([self.default]*x)
            self.rownames.append('')
        self.x = x ; self.y = y

    def clear(self):
        self.data = []
        self.rownames = []
        self.y = 0

    def set_default(self, newdef):
        self.default = newdef

    def set_heading_name(self, col, name):
        self.headings[col] = name
    set_column_name = set_heading_name

    def set_row_name(self, rowidx, name):
        self.rownames[rowidx] = name

    def get_dimensions(self):
        return self.x, self.y

    def add_cols(self, *names):
        for name in names:
            if type(name) is list:
                self.append_column(name)
                continue
            self.headings.append(name)
            self.x += 1
            for row in self.data:
                row.append(self.default)
    add_columns = add_cols
    add_column = add_cols
    add_col = add_cols

    def append_column(self, newcol, label=""):
        newcol = list(newcol)
        if len(newcol) == self.y:
            self.headings.append(label)
            self.x += 1
            for i in xrange(self.y):
                self.data[i].append(newcol[i])
        else:
            raise ValueError, "GenericTable: append_column: new column must be a list with length %d." % (self.y)
    
    def get_column(self, idx):
        if type(idx) is str:
            idx = self.headings.index(idx)
        rv = []
        for row in self.data:
            rv.append(row[idx])
        return rv

    def add_rows(self, *names):
        for rowname in names:
            self.data.append([self.default]*self.x) 
            self.rownames.append(rowname)
            self.y = self.y + 1

    def add_row(self, _name, **cols):
        self.rownames.append(_name)
        newrow = [self.default]*self.x
        for colname, val in cols.items():
            newrow[self.headings.index(colname)] = val
        self.y += 1
        self.data.append(newrow)

    def append_row(self, newrow, label=""):
        newrow = list(newrow)
        if len(newrow) == self.x:
            self.data.append(newrow)
            self.y += 1
            self.rownames.append(label)
        else:
            raise ValueError, "GenericTable: append_row: new row must be a list with length the same as table width."
    append = append_row

    def del_row(self, ind):
        del self.data[ind]
        del self.row_names[ind]
        self.y -= 1

    def get_row(self, rowidx):
        if type(rowidx) is str:
            rowidx = self.rownames.index(rowidx)
        return self.data[rowidx]

    def get_headings(self):
        return self.headings[:]

    def set(self, col, row, value):
        if type(col) is str:
            try:
                col = self.headings.index(col)
            except ValueError:
                self.add_cols(col)
                col = self.headings.index(col)

        if type(row) is str:
            try:
                row = self.rownames.index(row)
            except ValueError:
                self.add_row(row)
                row = self.rownames.index(row)
        self.data[row][col] = value

    def get(self, x, y):
        return self.data[y][x]

    def __str__(self):
        if self.x == 0 and self.y == 0:
            return "<empty table>"
        s = ["            " + " | ".join(map(lambda lv: "%10.10s" % lv, self.headings))]
        s.append("            "+"-"*(13*len(self.headings)+1))
        r = 0
        for row in self.data:
            s.append("%10.10s: " % self.rownames[r] + " | ".join(map(lambda lv: "%10.10s" % lv, row)))
            r += 1
        if self.title:
            s.insert(0, self.title.center(78))
        return "\n".join(s)

    def __iter__(self):
        return _TableIter(self)

    def __getitem__(self, key):
        kt = type(key)
        if kt is tuple:
            x, y = self._get_cell(key)
            return self.data[y][x]
        elif kt is str:
            i = self.rownames.index(key)
            return TableRow(self.data[i], self.headings, key)
        elif kt is int:
            return TableRow(self.data[key], self.headings, str(key))
        else:
            raise TypeError, "table index has wrong type"

    # key is an (x,y) tuple, x or y may be a name.
    def __setitem__(self, key, val):
        x, y = self._get_cell(key)
        self.data[y][x] = val

    # likewise
    def __delitem__(self, key): 
        x, y = self._get_cell(key)
        self.data[y][x] = self.default

    # slice operations take two args, so are convenient for table access.
    # However, this object will return a single (scalar) object when
    # sliced.
    def __getslice__(self, i, j):
        return self.data[j][i]
    
    def __setslice__(self, i, j, val):
        self.data[j][i] = val

    def __delslice__(self, i, j):
        self.data[j][i] = self.default

    def __len__(self):
        return self.y

    # cells may be addressed by index number or name of the col/row.
    # coord should be a 2-tuple
    def _get_cell(self, coord):
        x, y = coord # also asserts 2-tuple
        if type(x) is str:
            x = self.headings.index(x)
        if type(y) is str:
            y = self.rownames.index(y)
        return x, y


# this row object is returned when iterating over the table. It allows indexing
# by header name.
class TableRow(list):
    def __init__(self, init, headings, label=""):
        super(TableRow, self).__init__(init)
        self.label = label
        self.headings = headings

    def __getitem__(self, key):
        kt = type(key)
        if kt is str:
            i = self.headings.index(key)
            return list.__getitem__(self, i)
        elif kt is int:
            return list.__getitem__(self, key)
        else:
            raise TypeError, "index must be string matching header, or integer."

    def __str__(self):
        return "%-10s: %s" % (self.label, super(TableRow, self).__str__())


class _TableIter(object):
    def __init__(self, table):
        self.table = table
        self.dataiter = iter(table.data)
        self._rownum = 0
    def __iter__(self):
        return self
    def next(self):
        # delegates to the tables data iterator. StopIteration will be raised
        # from there.
        nr = self.dataiter.next()
        label = self.table.rownames[self._rownum]
        self._rownum += 1
        return TableRow(nr, self.table.headings, label)


#########################################
def get_combo_table(headings, datalist):
    t = GenericTable(headings)
    Nbins = len(headings)
    for i in xrange(len(datalist)):
        newrow = [None]*Nbins

if __name__ == "__main__":
    t = GenericTable()
    print t
    t.set("X", "Y", "XY val")
    t.set("X1", "Y1", "X1Y1 val")
    t.set("X1", "Y", "X1Y val")
    t.set("X2", "Y2", "X2Y2 val")
    t.set("X", "Y1", "XY2 val")
    t[("X2", "Y1")] =  "X2Y1 val"
    print t
    t.add_columns("newcol1", "newcol2")
    print t
    print t.get_dimensions()

    for r in t:
        print r["X2"]

