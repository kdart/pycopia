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
Perform static analysis of test case code modules to determine parameters used by the test.
This should simplify maintenance by further automating the test case managment.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

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

    def __init__(self, findall=True):
        self._classes = {}
        self._currentclass = None
        self.findall = findall

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


def find_classes(modname, findall=True):
    ast = get_ast(modname)
    nv = TestmoduleVisitor(findall)
    nv.visit(ast)
    return nv._classes

def get_class(cls):
    """Return  TestModuleVisitor report from a class instance."""
    ast = get_ast(cls.__module__)
    nv = TestmoduleVisitor()
    nv.visit(ast)
    return nv._classes[cls.__name__]



if __name__ == "__main__":
    from pycopia import autodebug

    modname = "testcases.unittests.QA.core.params"
    print(find_classes(modname))

