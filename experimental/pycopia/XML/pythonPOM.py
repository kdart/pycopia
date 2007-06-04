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
Used to make more efficient the use of POM for the python code generation and
analysis. 

"""

import XML.POM as POM

# base class for all python parse tree elements. Since all are the same. Also
# adds some query methods.
class TokenNode(POM.ElementNode):
    ATTLIST = POM.AttributeList([POM.XMLAttribute('value', 1, 12, None)])
    _name = "TokenNode"

class SymbolNode(POM.ElementNode):
    CONTENTMODEL = POM.ContentModel(POM.ANY)
    ATTLIST = POM.AttributeList([POM.XMLAttribute('value', 1, 12, None)])
    _name = "SymbolNode"

class PythonSource(POM.POMDocument):
    HEADER = '<?xml version="1.0" encoding="iso-8859-1"?>\n<!DOCTYPE file_input SYSTEM "python.dtd">\n'

    def get_leaf_values(self, n, elclass, line_info=0):
        for cn in gen_leaf_nodes(n, elclass):
            if line_info:
                yield (cn.value, cn.lineno)
            else:
                yield cn.value

    def strings(self, node=None, line_info=0):
        """Strings([node])
A generator function that iterates over string literal values in a document tree. """
        n = node or self.root
        return self.get_leaf_values(n, self.dtd.STRING, line_info)

    def funcdefs(self, node=None, line_info=0):
        n = node or self.root
        return self.get_leaf_values(n, self.dtd.funcdef, line_info)


class PyNodeIterator(object):
    def __init__(self, node, elclass):
        self.l = node.getall(elclass, 100)
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        try:
            v = self.l[self.i].value
        except IndexError:
            raise StopIteration
        self.i += 1
        return v


def gen_leaf_nodes(node, elclass):
    if isinstance(node, elclass):
        yield node
    for child in node.get_children():
        for cn in gen_leaf_nodes(child, elclass):
            yield cn
    return




