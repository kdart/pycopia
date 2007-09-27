#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
A Python Object Model document for plain text files.

This module's goal is to provide an identical API to POM/XHTML, but emit
plain text instead. As a sub-goal the plain text should be RST compatible.
It's primary purpose is to provide plain-text obtions for web frameworks
without changing any page markup generator code.

However, it currently lags far behind the XHTML document API.

"""

import sys

from pycopia.XML import POM
from pycopia.aid import partial

Text = POM.Text

# Hand-coded DTD elements for plain text. Note that add_text() is the only
# method that makes sense, but is not enforced.

# indicates any content
ANYCONTENT = POM.ContentModel((True,)) # can contain other nodes

attribClass = POM.XMLAttribute('class', 8, 12, None)
attribHref = POM.XMLAttribute('href', 1, 12, None)
attribLevel = POM.XMLAttribute('level', 1, 12, None)


def check_object(obj):
    if type(obj) in (str, unicode):
        return POM.Text(obj)
    if isinstance(obj, POM.ElementNode):
        return obj
    raise POM.ValidationError, "bad initializer object"

class InlineMixin(object):

    def _init(self, dtd):
        self.dtd = dtd

    def emit(self, fo):
        fo.write(self.__str__())

class ContainerMixin(object):

    def _init(self, dtd):
        self.dtd = dtd

    def make_node(self, name, attribs, *content):
        if name in ("Text", "ASIS", "Fragments"):
            elemclass = getattr(POM, name)
        else:
            elemclass = Plaintext

        if attribs:
            elem = elemclass(**attribs)
        else:
            elem = elemclass()

        for cont in content:
            if isinstance(cont, (POM.ElementNode, POM.Text, POM.ASIS)):
                elem.append(cont)
            else:
                elem.add_text(cont)
        return elem

    def get_nodemaker(self):
        def _make_node(container, name, attribs, *contents):
            return container.make_node(name, attribs, *contents)
        return partial(_make_node, self)
    nodemaker = property(get_nodemaker)

    def get_section(self, _name, **kwargs):
        #kwargs["class"] = _name
        sect = Section(**kwargs)
        sect._init(self.dtd)
        return sect

    def add_section(self, _name, **kwargs):
        sect = self.get_section(_name, **kwargs)
        self.append(sect)
        return sect

    def add_break(self):
        self.append(Br())

    def get_para(self, **attribs):
        p = Para(**attribs)
        p._init(self.dtd)
        return p

    def add_para(self, **attribs):
        p = self.get_para(**attribs)
        self.append(p)
        return p

    def new_para(self, text, **attribs):
        p = self.get_para(**attribs)
        t = check_object(text)
        p.append(t)
        self.append(p)
        return p

    def get_header(self, level, text, **kwargs):
        hobj = Heading(level=level)
        hobj.append(POM.Text(text))
        return hobj

    def add_header(self, level, text, **kwargs):
        hobj = self.get_header(level, text, **kwargs)
        self.append(hobj)
        return hobj

    def get_unordered_list(self, items, **attribs):
        rv = []
        for item in items:
            self.append(Plaintext("* %s\n" % item))
        return rv

    def add_unordered_list(self, items, **attribs):
        for item in items:
            self.append(Plaintext("* %s\n" % item))

    def get_ordered_list(self, items):
        rv = []
        for i, item in enumerate(items):
            rv.append(Plaintext("%d. %s\n" % (i, item)))
        return rv

    def add_ordered_list(self, items):
        for i, item in enumerate(items):
            self.append(Plaintext("%d. %s\n" % (i, item)))

    def add_anchor(self, **attribs):
        raise NotImplementedError

    def new_anchor(self, obj, **attribs):
        raise NotImplementedError

    def get_table(self, **kwargs):
        raise NotImplementedError

    def add_table(self, **kwargs):
        raise NotImplementedError

    def emit(self, fo, encoding="ascii"):
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            fo.write(self.__str__())
        else:
            fo.write(self.__str__())
            map(lambda o: o.emit(fo), self._children)

# root element
class Plaintext(ContainerMixin, POM.ElementNode):
    _name = "text"
    CONTENTMODEL = ANYCONTENT
    ATTRIBUTES = {
         'class': attribClass, 
         }
    KWATTRIBUTES = {
         'class_': attribClass, 
         }

    def __str__(self):
        s = map(str, self._children)
        return "".join(s)

    def __iadd__(self, text):
        self.add_text(str(text))
        return self


class Title(InlineMixin, POM.ElementNode):
    _name = "title"
    CONTENTMODEL = ANYCONTENT
    def __str__(self):
        t = self.get_text()
        line = "=" * len(t)
        return "%s\n%s\n%s\n\n" % (line, t, line)


class Br(ContainerMixin, POM.ElementNode):
    _name = "br"
    def __str__(self):
        return "\n"

class A(ContainerMixin, POM.ElementNode):
    _name = "a"
    CONTENTMODEL = ANYCONTENT
    ATTRIBUTES = {
         'href': attribHref, 
         }
    KWATTRIBUTES = {
         'href': attribHref, 
         }
    def __str__(self):
        t = self.get_text()
        return "%s [%s] " % (t, self.href)

class Heading(ContainerMixin, POM.ElementNode):
    _name = "heading"
    CONTENTMODEL = ANYCONTENT
    ATTRIBUTES = {
         'level': attribLevel, 
         }
    KWATTRIBUTES = {
         'level': attribLevel, 
         }
    def __str__(self):
        t = self.get_text()
        try:
            level = int(self.level)
        except (ValueError, TypeError):
            level = 0
        indent = " "*level
        lc = {0:"=", 1:"-", 2:"_", 3:"*"}.get(level, "+")
        line = lc * len(t)
        return "%s%s\n%s%s\n" % (indent, t, indent, line)


class Para(Plaintext):
    _name = "para"
    def __str__(self):
        s = map(str, self._children)
        return "".join(s)+"\n\n"

class Section(Plaintext):
    _name = "section"

class Chapter(Plaintext):
    _name = "chapter"


class TextDocument(POM.POMDocument, ContainerMixin):
    """POM document for text/plain documents.
    This document object is intended to have the same interface as the
    XHTMLDocument as much as possible. But it will produce plain text that
    is recognizable by the reStructuredText parser.
    """
    XMLHEADER = ""
    DOCTYPE = ""
    MIMETYPE = "text/plain"
    def __init__(self, encoding="ascii"):
        dtd = sys.modules[__name__] # the psuedo-dtd module is this module
        super(TextDocument, self).__init__(dtd=dtd, encoding=encoding)

    def initialize(self):
        self.set_root(Plaintext())

    def __iadd__(self, text):
        self.root.add_text(text)
        return self

    def add_text(self, text):
        self.root.add_text(text)

    def __str__(self):
        return str(self.root)

    def emit(self, fo):
        self.root.emit(fo)

    def add_title(self, title):
        ti = Title()
        ti.append(Text(title))
        self.root.insert(0, ti)
        return ti

    def _get_title(self):
        return self.get_path("/title")

    title = property(_get_title, add_title)

    # general add methods
    def append(self, obj, **kwargs):
        self.root.append(obj)

    def insert(self, ind, obj, **kwargs):
        self.root.insert(ind, obj)


def new_document(encoding=POM.DEFAULT_ENCODING):
    doc = TextDocument(encoding)
    doc.initialize()
    return doc

