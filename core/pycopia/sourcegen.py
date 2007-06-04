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
This module can be used to generate python source code. It has an interface
similar to the "new" module.

"""

import sys, os

BANGLINE = "#!/usr/bin/python\n"

def _tuplestr(tup):
    return ", ".join(map(str, tup))

def _classstr(tup):
    def _cstr(c):
        if type(c) is str:
            return c
        else:
            return "%s.%s" % (c.__module__, c.__name__)
    return ", ".join(map(_cstr, tup))

# These functions resembled the "new" module interface, but with different
# names. This is the function interface. There are also generator object
# interfaces below.

def genClass(klassname, parents, attribs=None, doc=None, methods=None):
    """genClass(name, parents, [attribs, [doc, [methods]]])
    Return a string of Python source code defineing a class object.
    Where:
        name = class name (string)
        parents = tuple of parent class objects or strings.
        attribs = class-global attributes to define, contained in a dictionary.
        doc = a doc string (optional)
        methods = list of methods strings.
    """
    s = []
    if parents:
        s.append( "class %s(%s):" % (klassname, _classstr(parents)) )
    else:
        s.append( "class %s:" % (klassname) )
    if doc:
        s.append('\t"""%s"""' % doc)
    if attribs:
        for key, val in attribs.items():
            s.append( "\t%s = %r" % (key, val) )
    if methods is not None:
        s.extend(map(str, list(methods)))
    if len(s) == 1:
        s.append("\tpass")
    s.append("\n")
    return "\n".join(s)

def genFunc(funcname, params, body=None, globals=None, doc=None, level=0):
    indent = "\t" * level
    s = []
    s.append("%sdef %s(%s):" % (indent, funcname, _tuplestr(params)) )
    if doc:
        s.append('%s\t"""%s"""' % (indent, doc))
    if globals is not None:
        s.append("%s\tglobal %s" % (indent, _tuplestr(globals)))
    if body is None:
        s.append("%s\tpass" % indent)
    else:
        s.append("\n".join(["%s%s" % (indent, line) for line in body.split("\n")]))
    s.append("\n")
    return "\n".join(s)

def genInstance(localname, instance, level=0):
    indent = "\t" * level
    return "%s%s = %r\n" % (indent, localname, instance) # depends on proper repr

def genMethod(funcname, params, body=None, globals=None, doc=None):
    s = []
    s.append( "def %s(self, %s):" % (funcname, _tuplestr(params)) )
    if doc:
        s.append('\t"""%s"""' % doc)
    if globals is not None:
        s.append("\tglobal %s" % _tuplestr(globals))
    if body is None:
        s.append("\tpass")
    elif type(body) is str:
        s.extend( map(lambda l: "\t%s"%l, body.split("\n")) )
    elif type(body) is list or type(body) is tuple:
        s.extend( map(lambda l: "\t%s"%l, body) )
    else:
        raise TypeError, "invalid type for body text"
    s.append("\n")
    # insert a tab in the front of each line and return lines joined with newlines.
    return "\n".join(map(lambda l: "\t%s"%l, s))

def genComment(text):
    lines = text.split("\n")
    lines = map(lambda l: "# %s" % l, lines)
    lines.append("\n")
    return "\n".join(lines)

def genImport(module, obj=None, level=0):
    if type(module) is type(sys): # a module type
        module = module.__name__
    if obj:
        if type(obj) is tuple or type(obj) is list:
            obj = _tuplestr(obj)
        return "%sfrom %s import %s\n" % ("\t"*level, module, obj)
    else:
        return "%simport %s\n" % ("\t"*level, module)


# a Python source producer object
class SourceGen(object):
    """SourceGen(outfile, [bangline])
An instance of this SourceGen class is a factory for generating python
source code, by writing to a file object.

    """
    def __init__(self, outfile, bangline=None):
        self.outfile = outfile
        bangline = bangline or BANGLINE 
        self.outfile.write(bangline)

    def genClass(self, klassname, parents=None, attribs=None, doc=None, methods=None):
        self.outfile.write( genClass(klassname, parents, attribs, doc, methods) )

    def genInstance(self, name, instance, level=0):
        self.outfile.write(genInstance(name, instance))

    def genFunc(self, funcname, params, attribs=None, doc=None, level=0):
        self.outfile.write( genFunc(funcname, params, attribs, doc, level) )

    def genMethod(self, funcname, params, body=None, globals=None, doc=None):
        self.outfile.write( genMethod(funcname, params, body, globals, doc) )

    def genComment(self, text):
        self.outfile.write( genComment(text) )

    def genImport(self, module, obj=None):
        self.outfile.write( genImport(module, obj) )

    def genBlank(self):
        self.outfile.write("\n")

    def write(self, obj):
        self.outfile.write( str(obj) )

    def writeln(self, obj):
        self.write(obj)
        self.write("\n")


# factory functions. 
# Returns a source generator ready to write to a file (or filename).
def get_generator(outfile):
    if type(outfile) is str:
        outfile = open(outfile, "w")
    return SourceGen(outfile)

# return a SourceFile object.
def get_sourcefile(outfile=None, bangline=None):
    if type(outfile) is str:
        outfile = open(outfile, "w")
    return SourceFile(outfile, bangline)


# object holder interface
class FunctionHolder(object):
    def __init__(self, funcname, params=None, attributes=None, doc=None):
        self.name = funcname
        self.params = params or ()
        self.attributes = attributes or {}
        self.doc = doc

    def __str__(self):
        return genFunc(self.name, self.params, self.attributes, self.doc)

    def add_attribute(self, name, value):
        self.attributes[name] = value
    set_attribute = add_attribute

    def get_attribute(self, name):
        return self.attributes[name]

    def del_attribute(self, name):
        del self.attributes[name]


class MethodHolder(object):
    def __init__(self, funcname, params=None, body=None, globals=None, doc=None):
        self.name = funcname
        self.params = params or ()
        self.body = body
        self.globals = globals
        self.doc = doc

    def __str__(self):
        return genMethod(self.name, self.params, self.body, self.globals, self.doc)


class ClassHolder(object):
    def __init__(self, klassname, parents=None, attributes=None, doc=None, methods=None):
        self.classname = klassname
        self.parents = parents or ()
        self.attributes = attributes or {}
        self.methods = methods or []
        self.doc = doc

    def __str__(self):
        return genClass(self.classname, self.parents, self.attributes, self.doc, self.methods)

    def add_method(self, funcname, params, body=None, globals=None, doc=None):
        mh = MethodHolder(funcname, params, body, globals, doc)
        self.methods.append(mh)
        return mh

    def add_attribute(self, name, value):
        self.attributes[name] = value
    set_attribute = add_attribute

    def get_attribute(self, name):
        return self.attributes[name]

    def del_attribute(self, name):
        del self.attributes[name]

class InstanceHolder(object):
    def __init__(self, name, instance, level=0):
        self.name = name
        self.instance = instance
        self.level = level

    def __str__(self):
        return genInstance(self.name, self.instance, self.level)

class TextHolder(object):
    """Holds arbitrary text for the source file. Caller must assure the
    text is syntactically correct Python."""
    def __init__(self, text, level=0):
        self.text = text
        self.level = level

    def __str__(self):
        indent = "\t" * self.level
        s = ["%s%s" % (indent, line) for line in self.text.split("\n")]
        s.append("\n")
        return "\n".join(s)


# python source file.
class SourceFile(object):
    def __init__(self, fo=None, bangline=None):
        self.fo = fo
        self.elements = []
        self.docstring = None
        self.bangline = bangline or BANGLINE

    def __str__(self):
        s = [self.bangline]
        if self.docstring:
            s.append('"""\n%s\n"""\n\n' % (self.docstring))
        s.extend(map(str, self.elements))
        return "\n".join(s)

    def add_doc(self, docstring):
        self.docstring = docstring

    def add_comment(self, text):
        self.elements.append(genComment(text))

    def add_import(self, module, obj=None):
        self.elements.append(genImport(module, obj))

    def add_blank(self):
        self.elements.append("\n")

    def add_function(self, funcname, params, attribs=None, doc=None):
        fh = FunctionHolder(funcname, params, attribs, doc)
        self.elements.append(fh)
        return fh

    def add_class(self, klassname, parents, attributes=None, doc=None, methods=None):
        ch = ClassHolder(klassname, parents, attributes, doc, methods)
        self.elements.append(ch)
        return ch

    def add_instance(self, name, instance, level=0):
        ih = InstanceHolder(name, instance, level)
        self.elements.append(ih)
        return ih

    def add_code(self, text, level=0):
        th = TextHolder(text, level)
        self.elements.append(th)
        return th

    def append(self, holder):
        self.elements.append(holder)

    def write(self, fo=None):
        fo = fo or self.fo
        fo.write(str(self))

    def writefile(self, filename=None):
        filename = filename or self.filename
        if filename:
            fo = open(filename, "w")
            self.write(fo)
        else:
            raise ValueError, "SourceFile: no filename given to write to!"



if __name__ == "__main__":
    class SUBCLASS(object):
        pass
    print "generated classes"
    print "-----------------"
    print genComment(__doc__)
    print genClass("test1", (), {})
    print genClass("test2", ("sub1",), {})
    print genClass("test3", ("sub1","sub2"), {})
    print genClass("test4", (SUBCLASS,), {})
    print genClass("test5", (), {"attr1": 1})
    print genClass("test6", (), {}, "One docstring")
    print genClass("test7", (), {"attr1": 1}, "another docstring")

    print "Holder classes"
    print "--------------"
    print genImport(sys.modules[__name__])
    print genImport(sys)
    print genImport(sys, "open")
    ch = ClassHolder("holdclass", ("sub1",))
    print ch
    print "--------------"
    ch.add_method("holdmethod1", ("param1",))
    print ch
    print "--------------"
    ch.add_method("holdmethod2", ("hm2p1",), "print 'body code'", doc="Some docstring")
    print ch
    print "--------------"
    ch.doc = "Documentation for holdclass."
    print ch
    print "--------------"
    sf = SourceFile()
    sf.add_doc("Testing the generator.")
    sf.add_import(sys)
    sf.append(ch)
    sf.write(sys.stdout)

