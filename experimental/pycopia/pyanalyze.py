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
Experimental module for the analysis of Python source code for the purpose of
test case automation. Uses the Python Object Model (POM) as the base object
model. It can convert the Python RST into XML for analysis by XML tools.

"""

import sys, os
import parser
import symbol, token

import dtds.python as pydtd


def get_parse_tree(fname):
    ast = parser.suite(open(fname).read())
    return parser.ast2tuple(ast)

def seq2tuple(t):
    return (257, t, (0,''))

def eval_seq(t, d=None):
    if d is None:
        d = {}
    ast = parser.sequence2ast( (257, t, (0, '')) )
    co = ast.compile()
    eval(co, d, d)
    del d["__builtins__"]
    return d

def eval_simple(t, d=None):
    if d is None:
        d = {}
    # put a valid top-level wrapper around the simple statement fragment.
    ast = parser.sequence2ast( (257, (264, (265, t, (4, '') )), (0, '')) )
    co = ast.compile()
    eval(co, d, d)
    del d["__builtins__"] # somehow this gets in here.
    return d

def find_simple_var(tree, name):
    pass

def match_all(patt, tree):
    rl = []
    for st in tree[1:]:
        rv, d = match(patt, st)
        if rv:
            rl.append(d)
    return rl


def py2xml(sourcefilename):
    """py2xml(fname) Write an XML representation of Python parse tree. """
    from XML.POM import BeautifulWriter
    outname = os.path.basename(sourcefilename)
    if outname.endswith(".py"):
        outname = outname[:-3]
    outname = outname+".xml"
    inf = open(sourcefilename, "r")
    outf = BeautifulWriter(file(outname, "w"))
    py2xml_filter(inf, outf)
    inf.close()
    outf.close()

def py2xml_filter(inf, outf):
    top = parse2pom(inf)
    top.emit(outf)

def get_pom(source=None):
    import XML.pythonPOM as pythonPOM
    doc = pythonPOM.PythonSource(pydtd)
    if source:
        try:
            inf = open(source)
        except:
            print >>sys.stderr, "get_pom: cannot open source file:", source
            raise
        try:
            root = parse2pom(inf)
            doc.set_root(root)
        finally:
            inf.close()
    return doc

def parse2pom(inf):
    ast = parser.suite(inf.read())
    t = parser.ast2tuple(ast, 1) # with line numbers
    del ast
    top = _get_class(t[0])()
    for i in t[1:]:
        _add_element(top, i)
    return top

def _add_element(parent, tup):
    ob = _get_class(tup[0])()
    parent.append(ob)
    for i in tup[1:]:
        if type(i) is tuple:
                _add_element(ob, i)
        else: # leaf node
            if i:
                ob.value = i
                ob.lineno = tup[-1]
                break

def _get_class(tok_id):
    if tok_id < 100:
        name = token.tok_name[tok_id]
    else:
        name = symbol.sym_name[tok_id]
    return getattr(pydtd, name)



def get_docs(fileName):
    """Retrieve information from the parse tree of a source file.

    fileName
        Name of the file to read Python source code from.
    """
    source = open(fileName).read()
    basename = os.path.basename(os.path.splitext(fileName)[0])
    ast = parser.suite(source)
    return ModuleInfo(ast.totuple(), basename)


class SuiteInfoBase(object):
    _docstring = ''
    _name = ''

    def __init__(self, tree = None):
        self._class_info = {}
        self._function_info = {}
        if tree:
            self._extract_info(tree)

    def _extract_info(self, tree):
        # extract docstring
        if len(tree) == 2:
            found, vars = match(DOCSTRING_STMT_PATTERN[1], tree[1])
        else:
            found, vars = match(DOCSTRING_STMT_PATTERN, tree[3])
        if found:
            self._docstring = eval(vars['docstring'])
        # discover inner definitions
        for node in tree[1:]:
            found, vars = match(COMPOUND_STMT_PATTERN, node)
            if found:
                cstmt = vars['compound']
                if cstmt[0] == symbol.funcdef:
                    name = cstmt[2][1]
                    self._function_info[name] = FunctionInfo(cstmt)
                elif cstmt[0] == symbol.classdef:
                    name = cstmt[2][1]
                    self._class_info[name] = ClassInfo(cstmt)
#            found, vars = match(SIMPLE_PATT, node)

    def get_docstring(self):
        return self._docstring

    def get_name(self):
        return self._name

    def get_class_names(self):
        return self._class_info.keys()

    def get_class_info(self, name):
        return self._class_info[name]

    def __getitem__(self, name):
        try:
            return self._class_info[name]
        except KeyError:
            return self._function_info[name]


class SuiteFuncInfo(object):
    #  Mixin class providing access to function names and info.

    def get_function_names(self):
        return self._function_info.keys()

    def get_function_info(self, name):
        return self._function_info[name]


class FunctionInfo(SuiteInfoBase, SuiteFuncInfo):
    def __init__(self, tree = None):
        self._name = tree[2][1]
        SuiteInfoBase.__init__(self, tree and tree[-1] or None)


class ClassInfo(SuiteInfoBase):
    def __init__(self, tree = None):
        self._name = tree[2][1]
        SuiteInfoBase.__init__(self, tree and tree[-1] or None)

    def get_method_names(self):
        return self._function_info.keys()

    def get_method_info(self, name):
        return self._function_info[name]


class ModuleInfo(SuiteInfoBase, SuiteFuncInfo):
    def __init__(self, tree = None, name = "<string>"):
        self._name = name
        SuiteInfoBase.__init__(self, tree)
        if tree:
            found, vars = match(DOCSTRING_STMT_PATTERN, tree[1])
            if found:
                self._docstring = vars["docstring"]


def match(pattern, data, vars=None):
    """Match `data' to `pattern', with variable extraction.

    pattern
        Pattern to match against, possibly containing variables.

    data
        Data to be checked and against which variables are extracted.

    vars
        Dictionary of variables which have already been found.  If not
        provided, an empty dictionary is created.

    The `pattern' value may contain variables of the form ['varname'] which
    are allowed to match anything.  The value that is matched is returned as
    part of a dictionary which maps 'varname' to the matched value.  'varname'
    is not required to be a string object, but using strings makes patterns
    and the code which uses them more readable.

    This function returns two values: a boolean indicating whether a match
    was found and a dictionary mapping variable names to their associated
    values.
    """
    if vars is None:
        vars = {}
    if type(pattern) is list:       # 'variables' are ['varname']
        vars[pattern[0]] = data
        return 1, vars
    if type(pattern) is not tuple:
        return (pattern == data), vars
#    if len(data) != len(pattern):
#        return 0, vars
#    for pattern, data in map(None, pattern, data):
    for pattern, data in zip(pattern, data):
        same, vars = match(pattern, data, vars)
        if not same:
            break
    return same, vars


#  This pattern identifies compound statements, allowing them to be readily
#  differentiated from simple statements.
#
COMPOUND_STMT_PATTERN = (
    symbol.stmt,
    (symbol.compound_stmt, ['compound'])
    )

# support for getting simple statements from the source
# simple statements (global)
SIMPLE_PATT = (
 symbol.stmt,
  (symbol.simple_stmt, ["simple"]))


#  This pattern will match a 'stmt' node which *might* represent a docstring;
#  docstrings require that the statement which provides the docstring be the
#  first statement in the class or function, which this pattern does not check.
#
DOCSTRING_STMT_PATTERN = (
    symbol.stmt,
    (symbol.simple_stmt,
     (symbol.small_stmt,
      (symbol.expr_stmt,
       (symbol.testlist,
        (symbol.test,
         (symbol.and_test,
          (symbol.not_test,
           (symbol.comparison,
            (symbol.expr,
             (symbol.xor_expr,
              (symbol.and_expr,
               (symbol.shift_expr,
                (symbol.arith_expr,
                 (symbol.term,
                  (symbol.factor,
                   (symbol.power,
                    (symbol.atom,
                     (token.STRING, ['docstring'])
                     )))))))))))))))),
     (token.NEWLINE, '')
     ))
 
def _get_mypath():
    return os.path.join(os.environ["PYNMS_HOME"], "lib", "pyanalyze.py")

def _test_pom():
    name = _get_mypath()
    print "parsing source..."
    doc = get_pom(name)
    print "done. generating XML..."
    print doc
    print "------\ndone."

if __name__ == "__main__":
    name = _get_mypath()
    t = get_parse_tree(name)
    print match_all(DOCSTRING_STMT_PATTERN , t)



