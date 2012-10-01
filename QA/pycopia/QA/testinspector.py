#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""
Perform static analysis of test case code modules to determine parameters used by the test.
This should simplify maintenance by further automating the test case managment.
"""

import sys
import imp
import ast

from pycopia import module


def get_ast(modname):
    """Return an AST given a module path name."""
    fo, path, (suffix, mode, mtype) = module.find_module(modname)
    try:
        if mtype == imp.PY_SOURCE:
            tree = ast.parse(fo.read(), filename=path, mode='exec')
        else:
            raise ValueError("{!r} is not a python source code module.".format(modname))
    finally:
        fo.close()
    return tree



class TestmoduleVisitor(ast.NodeVisitor):

    def __init__(self, all=True):
        self._classes = {}
        self._currentclass = None
        self.findall = all

    def visit_ClassDef(self, node):
        #print((node.body[0]))
        if not self.findall:
            pass
        self._currentclass = node.name
        self._classes[node.name] = []
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Looking for 'p1 = self.config.get("param1", "default1")'

        This is the canonical form of getting test case parameters in a test
        implementation. This ends up with an AST looking like:

            Assign(targets=[Name(id='p1', ctx=Store())],
            value=Call(func=Attribute(value=Attribute(value=Name(id='self',
            ctx=Load()), attr='config', ctx=Load()), attr='get', ctx=Load()),
            args=[Str(s='param1'), Str(s='default1')], keywords=[], starargs=None, kwargs=None))
        """
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            try:
                if (node.value.func.value.value.id == "self" and
                        node.value.func.value.attr == "config" and
                        node.value.func.attr == "get"):
                    lhs = node.targets[0].id
                    param = node.value.args[0].s
                    default = node.value.args[1].s
                    if self._currentclass is not None:
                        self._classes.setdefault(self._currentclass, []).append( (lhs, param, default) )
                    else:
                        raise ValueError("Didn't see class before config get")
            except AttributeError:
                return


def find_classes(modname, all=True):
    ast = get_ast(modname)
    nv = TestmoduleVisitor(all)
    nv.visit(ast)
    return nv._classes

def get_class(cls):
    """Return  TestModuleVisitor report from a class instance."""
    ast = get_ast(cls.__module__)
    nv = TestmoduleVisitor(all)
    nv.visit(ast)
    return nv._classes[cls.__name__]



if __name__ == "__main__":
    from pycopia import autodebug

    modname = "testcases.unittests.QA.core.params"
    print(find_classes(modname))

