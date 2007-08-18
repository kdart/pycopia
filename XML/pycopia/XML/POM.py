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
This module implements the XML POM -- the Python Object Model for XML. It is
something like DOM, but more Pythonic, and easier to use. These base classes
are used to build POM source files which are self-validating python-based XML
constructor objects. The major parts of the dtd2py command line tool are also
here.

"""

import sys, os, re
import codecs
import unicodedata
from htmlentitydefs import name2codepoint

from pycopia.aid import IF
from pycopia.textutils import identifier, keyword_identifier

from pycopia import dtds
from pycopia.XML import XMLVisitorContinue, ValidationError


DEFAULT_ENCODING = sys.getdefaultencoding()

def set_default_encoding(newcodec):
    global DEFAULT_ENCODING
    newcodec = str(newcodec)
    verify_encoding(newcodec)
    old = DEFAULT_ENCODING
    DEFAULT_ENCODING = newcodec
    return old

def verify_encoding(newcodec):
    try:
        codecs.lookup(newcodec)
    except LookupError, err:
        raise ValueError, err.args[0]

set_default_encoding("utf-8")


class ContentModel(object):
    """Represents and validates a content model.  """
    def __init__(self, rawmodel=None):
        self.model = rawmodel # TODO need actual content model...

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.model)

    def is_empty(self):
        return not self.model


#########################################################
# XML generating classes
# These classes are used to generate XML documents, similar to DOM. But, this
# interface is simpler and more Python-ic.
#########################################################

class Text(object):
    def __init__(self, data="", encoding=DEFAULT_ENCODING):
        self._parent = None
        self.set_text(data, encoding)
    def set_text(self, data, encoding=DEFAULT_ENCODING):
        self.data = unescape(to_unicode(data, encoding))
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data, encoding=None):
        self.data = unescape(to_unicode(data, encoding or self.encoding)) + self.data
    def add_text(self,data, encoding=None):
        self.data += unescape(to_unicode(data, encoding or self.encoding))
    append = add_text
    __iadd__ = add_text
    def __add__(self, other):
        return self.__class__(self.data + other.data)
    def emit(self, fo, encoding=None):
        fo.write( escape(self.data).encode(encoding or self.encoding) )
    def encode(self, encoding):
        return escape(self.data).encode(encoding)
    def __str__(self):
        return self.encode(self.encoding)
    def __unicode__(self):
        return escape(self.data)
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, escape(self.data))
    def __len__(self):
        return len(self.data)
    def __getslice__(self, start, end):
        return self.data[start:end]
    def __setslice__(self, start, end, v):
        self.data[start:end] = v
    def __delslice__(self, start, end):
        del self.data[start:end]
    def get_escape_length(self):
        return len(escape(self.data))
    def destroy(self):
        self.data = None
        self._parent = None
    def detach(self):
        self._parent = None
    def _fullpath(self):
        if self._parent:
            return "%s = %r" % (self._parent._fullpath(), self.data)
        else:
            return `self.data`
    fullpath = property(_fullpath)
    def walk(self, visitor):
        visitor(self)
    # dummy methods, for polymorphism with ElementNode
    def matchpath(self, pe):
        return 0
    def has_children(self):
        return 0
    def has_attributes(self):
        return 0
    def getall(self, elclass, depth=0, collect=None):
        return []

class CDATA(Text):
    def __str__(self):
        return self.encode(self.encoding)
    def encode(self, encoding):
        return "\n<![CDATA[%s]]>\n" % self.data.encode(encoding)
    def __unicode__(self):
        return u"<![CDATA[\n%s\n]]>\n" % (self.data,)
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.data)
    def emit(self, fo, encoding=None):
        fo.write("\n<![CDATA[")
        fo.write( self.data.encode(encoding or self.encoding) )
        fo.write("]]>\n")

class Comment(Text):
    def __init__(self, data="", encoding=DEFAULT_ENCODING):
        self._parent = None
        self.set_text(data, encoding)
    def set_text(self, data, encoding=DEFAULT_ENCODING):
        self.data = to_unicode(data, encoding)
        self.encoding = encoding
    def __str__(self):
        return self.encode(self.encoding)
    def encode(self, encoding):
        return "<!-- %s -->" % self._fix(self.data).encode(encoding)
    def __unicode__(self):
        return u"<!-- %s -->" % self._fix(self.data)
    def emit(self, fo, encoding=None):
        fo.write( "<!-- %s -->" % self._fix(self.data).encode(encoding or self.encoding) )
    def get_text(self):
        return self.data
    def insert(self, data, encoding=None):
        self.data = to_unicode(data, encoding or self.encoding) + self.data
    def add_text(self, data, encoding=None):
        self.data += to_unicode(data, encoding or self.encoding)
    append = add_text
    def _fix(self, data):
        data = escape(data)
        if data.find(u"--") != -1:
            data = data.replace(u"--", u"- ")
        return data

class ASIS(object):
    """Holder for pre-made markup that may be inserted into POM tree. It is a
    text leaf-node only. You can cache pre-constructed markup and insert it
    into the POM to speed up some page emission.  """
    def __init__(self, data="", encoding=DEFAULT_ENCODING):
        self._parent = None
        self.set_text(data, encoding)
    def set_text(self, data, encoding=DEFAULT_ENCODING):
        self.data = to_unicode(data, encoding)
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data, encoding=None):
        raise NotImplementedError, "Cannot insert into ASIS"
    def add_text(self,data, encoding=None):
        self.data += to_unicode(data, encoding or self.encoding)
    append = add_text
    __iadd__ = add_text
    def __str__(self):
        return self.data.encode(self.encoding)
    def encode(self, encoding):
        return self.data.encode(encoding)
    def __unicode__(self):
        return self.data
    def __repr__(self):
        cl = self.__class__
        return "%s.%s()" % (cl.__module__, cl.__name__)
    def __len__(self):
        return len(self.data)
    def __getslice__(self, start, end):
        return self.data[start:end]
    def __setslice__(self, start, end, v):
        self.data[start:end] = v
    def __delslice__(self, start, end):
        del self.data[start:end]
    def get_escape_length(self):
        return len(self.data)
    def destroy(self):
        self.data = None
        self._parent = None
    def detach(self):
        self._parent = None
    def _fullpath(self):
        if self._parent:
            return "%s = %r" % (self._parent._fullpath(), self.data)
        else:
            return repr(self.data)
    fullpath = property(_fullpath)
    def emit(self, fo, encoding=None):
        fo.write( self.data.encode(encoding or self.encoding) )
    def walk(self, visitor):
        visitor(self)
    # dummy methods, for polymorphism with ElementNode
    def matchpath(self, pe):
        return 0
    def has_children(self):
        return 0
    def has_attributes(self):
        return 0


class NameSpace(object):
    def __init__(self, name, uri):
        self.uri = uri
        if ":" in name:
            [xmlns, name] = name.split(":", 1)
            self.name = "%s:" % name
        else:
            self.name = "" # default name space
    def __str__(self):
        return self.name
    def __nonzero__(self):
        return bool(self.name)


# runtime attribute object
class POMAttribute(object):
    __slots__ = ["name", "value", "namespace"]
    def __init__(self, name, value, namespace=u"",
                            encoding=DEFAULT_ENCODING):
        self.name = to_unicode(name, encoding)
        self.value = to_unicode(value, encoding)
        self.namespace = namespace

    def __hash__(self):
        return hash((self.name, self.value, self.namespace))

    def __str__(self):
        return self.encode(DEFAULT_ENCODING)

    def encode(self, encoding=DEFAULT_ENCODING):
        name = self.name.encode(encoding)
        value = escape(self.value).encode(encoding)
        return '%s="%s"' % (name, value)
# TODO namespace support

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.name, self.value, 
                  self.namespace)

    def __nonzero__(self):
        return bool(self.name)


class ProcessingInstruction(object):
    pass # XXX

# abstract base class for generic XML node generation.
# Create an XML node by subclassing this and defining allowed attribute names
# in ATTRIBUTES. CONTENTMODEL holds the content specification from the DTD.
# Use the dtd2py program to convert a DTD to a python module that has classes
# for element types. Use that python dtd as a paramter for the POMDocument,
# below.

class ElementNode(object):
    ATTRIBUTES = {}
    KWATTRIBUTES = {}
    CONTENTMODEL = None
    _name = None
    def __init__(self, **attribs):
        self.__dict__["_attribs"] = attr = {}
        self.__dict__["_badattribs"] = badattrs = {}
        self.__dict__["_parent"] = None
        self.__dict__["_children"] = []
        self.__dict__["_namespace"] = u""
        self.__dict__["_encoding"] = DEFAULT_ENCODING
        ATT = self.__class__.KWATTRIBUTES
        for key, value in attribs.items():
            xmlattr = ATT.get(key)
            if type(value) is tuple:
                atns, value = value
            else:
                atns = u""
            if xmlattr:
                attr[xmlattr.name] = POMAttribute(xmlattr.name, value, atns)
            else:
                # for delayed attribute validation.
                # XXX could be foriegn namespace attribute
                badattrs[key] = POMAttribute(key, value, atns)

    def get_attribute(self, name):
        try:
            xmlattr = self.__class__.ATTRIBUTES[name]
        except KeyError:
            try:
                xmlattr = self.__class__.KWATTRIBUTES[name]
            except KeyError:
                return None
        try:
            return self.__dict__["_attribs"][xmlattr.name].value
        except KeyError:
            # might be implied, fixed, or enum...
            if xmlattr.a_decl in (FIXED, IMPLIED, DEFAULT):
                return xmlattr.default or u""
        return None
    getAttribute = get_attribute # JS compatibility

    def set_attribute(self, name, val, ns=u""):
        """set_attribute(name, value)
        Set the element node attribute "name" to "value". 
        The name can be the shorthand identifier, or the real name.
        """
        if u":" in name:
            self._attribs[name] = POMAttribute(name, val)
            return True
        try:
            xmlattr = self.__class__.ATTRIBUTES[name]
        except KeyError:
            try:
                xmlattr = self.__class__.KWATTRIBUTES[name]
            except KeyError:
                return False
        self._attribs[xmlattr.name] = POMAttribute(xmlattr.name, val, ns)
        return True
    setAttribute = set_attribute # JS compatibility

    def __getattr__(self, name):
        defval = self.get_attribute(name)
        if defval is not None:
            return defval
        raise AttributeError, "Element %r has no attribute %r." % (self._name, name)

    def __setattr__(self, name, value):
        if not self.set_attribute(name, value, self.__dict__["_namespace"]):
            self.__dict__[name] = value

    def del_attribute(self, name):
        self.__delattr__(name)
    removeAttribute = del_attribute # JS compatibility

    def __delattr__(self, name):
        try:
            xmlattr = self.__class__.ATTRIBUTES[name]
        except KeyError:
            try:
                xmlattr = self.__class__.KWATTRIBUTES[name]
            except KeyError:
                try:
                    del self.__dict__[key]
                except KeyError:
                    raise AttributeError("%r has no attribute %r " % (self.__class__, name))
        try:
            del self._attribs[xmlattr.name]
        except KeyError:
            pass

    def get_keyword_attributes(self):
        """return list of names that may be used as keyword names when
        instantiating this element.
        """
        return self.__class__.KWATTRIBUTES.keys()

    def get_attributes(self):
        """return list of DTD defined attribute names.
        """
        return self.__class__.ATTRIBUTES.keys()

    def get_parent(self):
        return self._parent
    parent = property(get_parent)

    def replace(self, newtree):
        if not isinstance(newtree, (ElementNode, Text, Comment)):
            raise ValueError, "Must replace with another ElementNode"
        if self._parent:
            p = self._parent
            i = self._parent.index(self)
            del self._parent[i]
            self._parent = None
            p.insert(i, newtree)
        return self

    def detach(self):
        """Detach this node from the tree. It becomes the root of another tree."""
        if self._parent:
            try:
                i = self._parent.index(self)
                del self._parent[i]
            except ValueError:
                pass
        self._parent = None
        return self

    def destroy(self):
        """destroy() Remove this node and all child node references."""
        # remove parent _children list reference
        if self._parent:
            i = self._parent.index(self)
            del self._parent[i]
        self._parent = None
        for n in self._children:
            n._parent = None
        self._children = None

    def set_encoding(self, encoding):
        POM.verify_encoding(encoding)
        self._encoding = encoding

    def index(self, obj):
        objid = id(obj)
        i = 0
        for o in self._children:
            if id(o) == objid:
                return i
            i += 1
        raise ValueError, "ElementNode: Object not contained here."

    def append(self, obj):
        """Append an existing DTD object instance."""
        if obj is not None:
            obj._parent = self
            self._children.append(obj)

    def pop(self, idx=-1):
        """Pop a child element from child list and return it."""
        obj = self._children[idx]
        del self._children[idx]
        obj._parent = None
        return obj

    def extend(self, objlist):
        for obj in objlist:
            self.append(obj)

    def insert(self, index, obj):
        obj._parent = self
        self._children.insert(index, obj)

    def add(self, klass, **kwargs):
        """Add an element class from a dtd module."""
        obj = apply(klass, (), kwargs)
        self.append(obj)
        return obj

    def get_children(self):
        return self._children[:]

    def __iter__(self):
        return iter(self._children)

    def add_text(self, text, encoding=DEFAULT_ENCODING):
        "Adding text to elements is so common, there is a special method for it."
        if self.has_children() and isinstance(self._children[-1], Text):
            self._children[-1].add_text(text, encoding)
        else:
            t = Text(text, encoding)
            self.append(t)

    def add_asis(self, xmltext):
        """Add text that is already XML markup, or script text."""
        asis = ASIS(xmltext)
        self.append(asis)
        return asis

    def add_cdata(self, text, encoding=DEFAULT_ENCODING):
        """Add character data that is not parsed."""
        if self.has_children() and isinstance(self._children[-1], CDATA):
            self._children[-1].add_text(text, encoding)
        else:
            t = CDATA(text, encoding)
            self.append(t)

    def replace_text(self, text):
        if self._children:
            del self._children[-1]
        self.append(Text(text))

    def __len__(self):
        return len(self._children)

    # The truth is, we exist, even if we have no children.
    def __nonzero__(self):
        return True

    def has_attributes(self):
        return bool(self._attribs)
    hasAttributes = has_attributes

    def has_attribute(self, name):
        return name in self._attribs

    def attributes(self):
        return self.ATTRIBUTES.keys()

    def has_children(self):
        return len(self._children)

    def _find_index(self, index):
        if type(index) is str:
            for i in xrange(len(self._children)):
                if self._children[i].matchpath(index):
                    return i
            raise IndexError, "no elements match"
        else:
            return index

    def __getitem__(self, index):
        if type(index) is str:
            el =  self.get_element(index)
            if el is None:
                raise IndexError, "no item matches"
            else:
                return el
        else:
            return self._children[index]

    def __setitem__(self, index, obj):
        index = self._find_index(index)
        obj._parent = self
        self._children[index] = obj

    def __delitem__(self, index):
        index = self._find_index(index)
        del self._children[index]

    def __repr__(self):
        attrs = [('%s=%r' % (keyword_identifier(normalize_unicode(t[0])), t[1]))
            for t in self._attribs.items()]
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, ", ".join(attrs))

    def __str__(self):
        return self.encode(self._encoding)

    def _verify_attributes(self):
        if self._badattribs:
            cl = self.__class__
            raise ValidationError(
                "Attribute(s) %r not valid for %s.%s." %
                (",".join(self._badattribs.keys()), cl.__module__, cl.__name__))
        attribs = self._attribs
        for key, dtdattr in self.__class__.ATTRIBUTES.items():
            aval = attribs.get(key, None)
            if aval is None:
                if dtdattr.a_decl == REQUIRED:
                    raise ValidationError(
                        "Required attribute not present: %s" % (dtdattr.name,))
            else:
                dtdattr.verify(aval.value)

    def encode(self, encoding):
        self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            return self._empty_str(encoding)
        else:
            return self._non_empty_str(encoding)

    def set_namespace(self, ns, encoding=DEFAULT_ENCODING):
        self._namespace = to_unicode(ns, encoding)

    def del_namespace(self):
        self._namespace = u""

    namespace = property(lambda s: s._namespace, set_namespace,
                del_namespace)

    def _get_ns(self, encoding):
        return self._namespace.encode(encoding)

    def _non_empty_str(self, encoding):
        ns = self._get_ns(encoding)
        name = self._name.encode(encoding)
        s = ["<%s%s%s>" % (ns, name, self._attr_str(encoding))]
        map(s.append, map(lambda o: o.encode(encoding), self._children))
        s.append("</%s%s>" % (ns, name))
        return "".join(s)

    def _empty_str(self, encoding):
        return "<%s%s%s />" % (self._get_ns(encoding), self._name.encode(encoding), 
                       self._attr_str(encoding))

    def _attr_str(self, encoding):
        attrs = map(lambda o: o.encode(encoding), self._attribs.values())
        attrs.insert(0, "") # for space before first attribute
        return " ".join(attrs)

    def emit(self, fo, encoding=None):
        enc = encoding or self._encoding
        self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            fo.write(self._empty_str(enc))
        else:
            ns = self._get_ns(enc)
            name = self._name.encode(enc)
            fo.write("<%s%s%s>" % (ns, name, self._attr_str(enc)))
            map(lambda o: o.emit(fo, enc), self._children)
            fo.write("</%s%s>" % (ns, name))

    def validate(self, encoding=DEFAULT_ENCODING):
        ff = FakeFile(None)
        # Will raise a ValidationError if not valid.
        # Don't need full backtrace for this type of error.
        try:
            self.emit(ff, encoding)
        except ValidationError, err:
            raise ValidationError, err 

    def walk(self, visitor):
        try:
            visitor(self)
        except XMLVisitorContinue:
            return
        for node in self._children:
            node.walk(visitor)

    # methods for node path manipulation

    _xpath_index_re = re.compile(r'(\w+)\[(\d+)]')
    _xpath_re = re.compile(r'(\w+)\[(.*)]')

    def pathname(self):
        """pathname() returns the ElementNode as a string in xpath format."""
        if self._attribs:
            s = map(lambda it: "@%s='%s'" % it, self._attribs.items())
            return "%s[%s]" % (self.__class__.__name__, " and ".join(s))
        else:
            return self.__class__.__name__

    def _fullpath(self):
        """fullpath() returns the ElementNode's full path as a string in
        xpath format."""
        if self._parent:
            base = self._parent._fullpath()
        else:
            base = ""
        return "%s/%s" % (base, self.pathname() )
    fullpath = property(_fullpath)

    def matchpath(self, pathelement):
        if "[" not in pathelement:
            return pathelement == self._name
        else:
            mo = ElementNode._xpath_re.match(pathelement)
            if mo:
                name, match = mo.groups()
                if name != self._name:
                    return False
                mp = match.split("=")
                attr = self.get_attribute(mp[0][1:])
                if attr is None:
                    return False
                if len(mp) > 1:
                    return mp[1][1:-1] == attr
                else:
                    return True
            else:
                raise ValueError, "Path element %r not found." % (pathelement,)

    def find_elements(self, pathelement):
        rv = []
        for child in self._children:
            if child.matchpath(pathelement):
                rv.append(child)
        return rv


    def get_element(self, pathelement):
        mo = ElementNode._xpath_index_re.match(pathelement)
        if mo:
            return self._children[int(mo.group(2))-1]
        for child in self._children:
            if child.matchpath(pathelement):
                return child
        return None

    def elements(self, elclass):
        """Return iterator that iterates over list of elements matching elclass"""
        return NodeIterator(self, elclass)

    def getall(self, elclass, depth=sys.maxint, collect=None):
        if collect is None:
            collection = []
        else:
            collection = collect # should be a list
        for el in self._children:
            if isinstance(el, elclass):
                collection.append(el)
            if depth > 0:
                el.getall(elclass, depth-1, collection)
        return collection

    def find(self, elclass, **attribs):
        for obj in self._children:
            if isinstance(obj, elclass):
                if self._attribs_match(obj, attribs):
                    return obj
        return None

    def _attribs_match(self, obj, attribdict):
        for tname, tval in attribdict.items():
            try:
                if getattr(obj, tname) != tval:
                    return 0
            except AttributeError:
                return 0
        return 1

    def get_text(self):
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            return u" "
        else:
            nodes = self.getall(Text, sys.maxint)
            return u"".join(map(lambda s: s.get_text(), nodes))

    # XPath-like functions
    def comment(self):
        return self.getall(Comment, sys.maxint)

    def text(self):
        return self.getall(Text, sys.maxint)

    def processing_instruction(self):
        return self.getall(ProcessingInstruction, sys.maxint)

    def node(self):
        return self.getall(ElementNode, sys.maxint)


# Used to hold unknown nodes (not found it dtd module). Usually from some
# foriegn namespace.
class UnknownNode(ElementNode):
    ATTRIBUTES = {}
    KWATTRIBUTES = {}
    CONTENTMODEL = ContentModel((True,))
    _name = None
    def __init__(self, **attribs):
        self.__dict__["_attribs"] = attr = {}
        self.__dict__["_badattribs"] = badattrs = {}
        self.__dict__["_parent"] = None
        self.__dict__["_children"] = []
        self.__dict__["_namespace"] = u""
        self.__dict__["_encoding"] = DEFAULT_ENCODING
        ATT = self.__class__.KWATTRIBUTES
        for key, value in attribs.items():
            xmlattr = ATT.get(key)
            if type(value) is tuple:
                atns, value = value
            else:
                atns = u""
            if xmlattr:
                attr[xmlattr.name] = POMAttribute(xmlattr.name, value, atns)
            else:
                # for delayed attribute validation.
                # XXX could be foriegn namespace attribute
                badattrs[key] = POMAttribute(key, value, atns)

    def _verify_attributes(self):
        return True # XXX cannot verify foriegn attributes at this time.

    def _get_ns(self, encoding):
        return u"".encode(encoding)


class NodeIterator(object):
    def __init__(self, node, elclass):
        self.node = node
        self.elclass = elclass
        self.i = 0

    def __iter__(self):
        return self

    def next(self):
        while 1:
            try:
                n = self.node[self.i]
            except IndexError:
                raise StopIteration
            self.i += 1
            if isinstance(n, elclass):
                break
        return n


def find_nodes(node, elclass):
    if isinstance(node, elclass):
        yield node
    for child in node.get_children():
        for cn in find_nodes(child, elclass):
            yield cn
    return


class Fragments(ElementNode):
    """Fragments is a special holder class to hold 'loose' markup fragments.
    That is, bits of markup that don't have a common container (e.g. not in
    root element).  It is invisible."""
    def __str__(self):
        return self.encode(self._encoding)

    def encode(self, encoding):
        s = []
        map(s.append, map(lambda o: o.encode(encoding), self._children))
        return "".join(s)

    def emit(self, fo, encoding=None):
        map(lambda o: o.emit(fo, encoding), self._children)

    def matchpath(self, pathelement):
        return False


def to_unicode(arg, encoding):
    if isinstance(arg, unicode):
        return arg
    return unicode(str(arg), encoding)


class Notation(object):
    def __init__(self, name, pubid, sysid):
        self.name = name
        self.public = pubid
        self.system = sysid

    def __str__(self):
        if self.system:
            return "%s %s" % (self.public, self.system)
        else:
            return self.public

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r, %r)" % (cl.__module__, cl.__name__, 
                    self.name, self.public, self.system)


class BeautifulWriter(object):
    """A wrapper for a file-like object that is itself a file-like object. It
    is basically a shim. It attempts to beautify the XML stream emitted by the
    POM tree. Pass one of these to the emit method if you want better looking
    output."""
    def __init__(self, fo, inline=[]):
        self._fo = fo # the wrapped file object
        self._inline = list(inline) # list of special tags that are inline
        self._level = 0
        self._tagre = re.compile(r"<([-a-zA-Z0-9_:]+)") # start tag
    def __getattr__(self, name):
        return getattr(self._fo, name)

    def write(self, data):
        if data.endswith("/>"):
            self._fo.write("\n"+"  "*self._level)
            return self._fo.write(data)
        if data.startswith("</"):
            self._level -= 1
            self._fo.write("\n"+"  "*self._level)
            return self._fo.write(data)
        mo = self._tagre.search(data)
        if mo:
            if mo.group(1) in self._inline:
                return self._fo.write(data)
            else:
                self._fo.write("\n"+"  "*self._level)
                self._level += 1
                return self._fo.write(data)
        return self._fo.write(data)


# base class for whole POM documents, including Header.
class POMDocument(object):
    XMLHEADER = '<?xml version="1.0" encoding="%s"?>\n' % DEFAULT_ENCODING
    DOCTYPE = ""
    MIMETYPE = "application/xml" # reset in subclass

    def __init__(self, dtd=None, doctype=None, lang=None, encoding=DEFAULT_ENCODING):
        if doctype is None and dtd is None:
            raise ValueError("POMDocument: Need one of doctype or dtd parameter.")
        self.dtds = []
        self.root = None
        self.lang = lang
        self.dirty = 0
        self._idmap = {}
        self._COUNTERS = {}
        if doctype: # implies new document 
            self.set_doctype(doctype)
        elif dtd:
            self.set_dtd(dtd)
            try:
                root = self.dtd._Root()
            except AttributeError:
                print >>sys.stderr, "Document warning: unknown root element."
            else:
                self.set_root(root)
        self.set_encoding(encoding)
        self.set_language(lang)

    def initialize(self):
        """New document initializer."""
        pass

    def set_encoding(self, encoding):
        verify_encoding(encoding)
        self.XMLHEADER = '<?xml version="1.0" encoding="%s"?>\n' % (encoding,)
        self.encoding = encoding

    def set_language(self, lang):
        self.lang = lang
        if lang and self.root:
            self.root.xml_lang = lang

    def set_doctype(self, doctype):
        dt = dtds.get_doctype(doctype)
        if dt:
            self.DOCTYPE = str(dt)
            self.set_dtd(dtds.get_dtd_module(doctype))
            rootclass = getattr(self.dtd, identifier(dt.name))
            self.set_root(rootclass())
        else:
            raise ValidationError, "Invalid doctype: %s" % (doctype,)

    def set_root(self, root):
        if isinstance(root, ElementNode):
            # set fixed attributes on root element (usually namespace
            # identifiers)
            for keyname, xmlattrib in root.ATTRIBUTES.items():
                if xmlattrib.a_decl == FIXED:
                    root.set_attribute(keyname, xmlattrib.default)
            self.root = root
            self.dirty = 0
        else:
            raise ValueError, "root document must be POM ElementNode."

    def add_dtd(self, dtdmod):
        self.dtds.append(dtdmod)

    def set_dtd(self, dtdmod):
        self.dtds = [dtdmod]
        self.dtd = dtdmod

    def set_dirty(self, val=1):
        self.dirty = val

    def __str__(self):
        return self.encode(self.encoding)

    def encode(self, encoding=DEFAULT_ENCODING):
        if encoding != self.encoding:
            self.set_encoding(encoding)
        return self.XMLHEADER + self.DOCTYPE + self.root.encode(encoding) + "\n"

    def emit(self, fo, encoding=DEFAULT_ENCODING):
        if encoding != self.encoding:
            self.set_encoding(encoding)
        fo.write(self.XMLHEADER)
        fo.write(self.DOCTYPE)
        self.root.emit(fo, encoding)
        fo.write("\n")

    def validate(self, encoding=DEFAULT_ENCODING):
        self.root.validate(encoding)


    def walk(self, visitor):
        self.root.walk(visitor)

    def get_identity(self, name):
        for dtd in self.dtds:
            try:
                return dtd.GENERAL_ENTITIES[name]
            except KeyError:
                pass
        return None

    def get_parser(self, **kwargs):
        return get_parser(self, **kwargs)

    def parse(self, url, data=None, encoding=DEFAULT_ENCODING, **kwargs):
        parser = get_parser(self, **kwargs)
        parser.parse(url, data=data, encoding=encoding)
        parser.close()

    def parseFile(self, fo, **kwargs):
        parser = get_parser(self, **kwargs)
        parser.parseFile(fo)

    def parseString(self, string, **kwargs):
        parser = get_parser(self, **kwargs)
        parser.feed(string)
        parser.close()

    def write_xmlfile(self, filename=None, encoding=DEFAULT_ENCODING):
        filename = filename or self.filename
        if filename:
            fo = open(os.path.expanduser(filename), "w")
            try:
                self.emit(fo, encoding)
            finally:
                fo.close()
        self.dirty = 0
    writefile = write_xmlfile

    def get_path(self, path):
        """Returns an ElementNode instance in the tree addressed by the path."""
        elements = path.split("/")
        while not elements[0]: # eat empty first element
            elements.pop(0)
        node = self.root
        pathelement = elements.pop(0)
        if node.matchpath(pathelement):
            while elements:
                pathelement = elements.pop(0)
                node = node.get_element(pathelement)
                if node is None:
                    raise IndexError, "path element not found"
            return node
        else:
            raise IndexError, "first path element not found"
    getpath = get_path # alias

    def __getitem__(self, name):
        return self.get_path(name)

    def set_path(self, path, text):
        node = self.get_path(path)
        node.replace_text(text)

    def del_path(self, path):
        els = path.split("/")
        path, endnode = "/".join(els[:-1]), els[-1]
        node = self.get_path(path)
        del node[endnode]

    def add_path(self, basepath, newnode):
        node = self.get_path(basepath)
        node.append(newnode)

    def add_text(self, basepath, text, encoding=None):
        node = self.get_path(basepath)
        node.add_text(text, encoding or self.encoding)

    def add_asis(self, basepath, xmltext):
        asis = ASIS(xmltext)
        node = self.get_path(basepath)
        node.append(asis)
        return asis

    def _write_text(self, fo, node):
        for n in node:
            if isinstance(n, Text):
                fo.write(n._fullpath())
                fo.write("\n")
            else:
                self._write_text(fo, n)

    def write_paths(self, fileobject):
        realfile = 0
        if type(fileobject) is str:
            fileobject = open(fileobject, "w")
            realfile = 1
        self._write_text(fileobject, self.root)
        if realfile:
            fileobject.close()




# Document constructors

def new_document(doctype, encoding=DEFAULT_ENCODING):
    dtd = dtds.get_dtd_module(doctype)
    doc = POMDocument(dtd=dtd)
    doc.set_encoding(encoding)
    return doc

def write_error(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")

XML_HEADER_RE = re.compile(r'xml version="([0123456789.]+)" encoding="([A-Z0-9-]+)"', re.IGNORECASE)

#### new sax2 parser ###
class ContentHandler(object):

    def __init__(self, doc=None, doc_factory=new_document, logfile=None):
        self._locator = None
        self.stack = []
        self.msg = None
        self.doc = doc # call set_root on this when document fully parsed.
        self._doc_factory = doc_factory
        self.encoding = DEFAULT_ENCODING # default to regenerate as
        self.modules = []
        self._prefixes = {}
        self._classcache = {}
        if logfile:
            self._errormethod = logfile.write
        else:
            self._errormethod = write_error

    def _get_class(self, name):
        klass = None
        name = identifier(name)
        try:
            return self._classcache[name]
        except KeyError:
            pass
        for mod in self.doc.dtds:
            try:
                klass = getattr(mod, name)
            except AttributeError:
                continue
            if klass:
                self._classcache[name] = klass
                return klass
        raise AttributeError

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startDocument(self):
        self.stack = []

    def endDocument(self):
        if self.stack: # stack should be empty now
            raise ValidationError, "unbalanced document!"
        if self.doc is None:
            self.doc = self._doc_factory(encoding=self.encoding)
        root = self.msg
        self.msg = None
        # Parser strips out namespaces, have to add them back in.
        if self._prefixes:
            for uri, prefix in self._prefixes.items():
                root.set_attribute(u"xmlns:%s" % prefix, uri)
        self.doc.set_root(root)

    def startElement(self, name, atts):
        "Handle an event for the beginning of an element."
        try:
            klass = self._get_class(name)
        except AttributeError:
            raise ValidationError, "Undefined element tag: " + name
        attr = {}
        for name, value in atts.items():
            attr[keyword_identifier(normalize_unicode(name))] = unescape(value)
        obj = klass(**attr)
        self.stack.append(obj)

    def endElement(self, name):
        "Handle an event for the end of an element."
        obj = self.stack.pop()
        try:
            self.stack[-1].append(obj)
        except IndexError:
            self.msg = obj

    def characters(self, text):
        if self.stack and text:
            self.stack[-1].append(Text(text))

    def processingInstruction(self, target, data):
        'handle: xml version="1.0" encoding="ISO-8859-1"?'
        # NOTE this seems to never be called by the parser.
        mo = XML_HEADER_RE.match(data)
        if mo:
            version, encoding = mo.groups()
            assert version == "1.0"
            self.encoding = encoding
            if self.doc:
                self.doc.set_encoding(encoding)
        else:
            self._errormethod("!!! Unhandled pi: %r" % (data,))

    def startPrefixMapping(self, prefix, uri):
        self._prefixes[uri] = prefix

    def endPrefixMapping(self, prefix):
        pass

    def skippedEntity(self, name):
        if self.stack:
            self.stack[-1].add_text(unichr(name2codepoint[name]))

    def ignorableWhitespace(self, whitespace):
        self._errormethod("unhandled ignorableWhitespace: %r" % (whitespace,))

    # Namespace interface
    def startElementNS(self, cooked_name, name, atts):
        ns, basename = cooked_name
        if ns:
            attr = {}
            obj = UnknownNode()
            obj._name = name
            obj.set_namespace(self._prefixes[ns])
            for cooked_attname, value in atts.items():
                atns, atname = cooked_attname
                attr[atname] = POMAttribute(atname, unescape(value), atns)
            obj._attribs = attr
        else:
            try:
                klass = self._get_class(basename)
            except AttributeError:
                raise ValidationError, "Undefined element tag: " + name
            attributes = {}
            for cooked_attname, value in atts.items():
                atns, atname = cooked_attname
                kwname = keyword_identifier(normalize_unicode(atname))
                if atns:
                    attributes[kwname] = (self._prefixes[atns], unescape(value))
                else:
                    attributes[kwname] =  unescape(value)
            obj = klass(**attributes)
        self.stack.append(obj)

    def endElementNS(self, name, rawname):
        obj = self.stack.pop()
        try:
            self.stack[-1].append(obj)
        except IndexError:
            self.msg = obj

    # DTDHandler interface
    def notationDecl(self, name, publicId, systemId):
        """Handle a notation declaration event."""
        self._errormethod("unhandled notationDecl: %r %r %r" % (
                                               name, publicId, systemId))

    def unparsedEntityDecl(self, name, publicId, systemId, ndata):
        """Handle an unparsed entity declaration event."""
        self._errormethod("unhandled unparsedEntityDecl: %r %r %r %r" % (
                    name, publicId, systemId, ndata))

    # entity resolver interface
    def resolveEntity(self, publicId, systemId):
        for modname, doctype in dtds.DOCTYPES.items():
            if doctype.public == publicId:
                if self.doc is None:
                    self.doc = self._doc_factory(doctype=modname, encoding=self.encoding)
                else:
                    self.doc.set_doctype(modname)
                break
        else:
            raise ValidationError, "unknown DOCTYPE: %r" % (publicId,)
        # Have to fake a file-like object for the XML parser to not
        # actually get an external entity.
        return FakeFile(systemId)


class FakeFile(object):
    def __init__(self, name):
        self.name = name
    def read(self, amt=None):
        return ""
    def write(self, data):
        return len(data)


class ErrorHandler(object):
    def __init__(self, logfile=None):
        self._lf = logfile

    def error(self, exception):
        "Handle a recoverable error."
        raise exception

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        raise exception

    def warning(self, exception):
        "Handle a warning."
        if self._lf:
            self._lf.write("XML Warning: %s" % (exception,))


def get_parser(document=None, namespaces=0, validate=0, external_ges=1, 
        logfile=None, doc_factory=new_document):
    import xml.sax.sax2exts
    import xml.sax.handler
    import new
    handler = ContentHandler(document, doc_factory=doc_factory, logfile=logfile)
    errorhandler = ErrorHandler(logfile)
    # create parser 
    parser = xml.sax.sax2exts.XMLParserFactory.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, namespaces)
    parser.setFeature(xml.sax.handler.feature_validation, validate)
    parser.setFeature(xml.sax.handler.feature_external_ges, external_ges)
    parser.setFeature(xml.sax.handler.feature_external_pes, 0)
    parser.setFeature(xml.sax.handler.feature_string_interning, 1)
    # set handlers 
    parser.setContentHandler(handler)
    parser.setDTDHandler(handler)
    parser.setEntityResolver(handler)
    parser.setErrorHandler(errorhandler)
    # since the xml API provides some generic parser I can't just
    # subclass I have to "patch" the object in-place with this trick.
    # This is to a) make the API compatible with the HTMLParser, and b)
    # allow specifing the encoding and other headers in the request.
    parser.parse_orig = parser.parse
    def parse(self, url, data=None, encoding=DEFAULT_ENCODING, 
                                    useragent=None, accept=None):
        from pycopia.WWW import urllibplus
        fo = urllibplus.urlopen(url, data, encoding, useragent=useragent, accept=accept)
        if logfile:
            from pycopia import UserFile
            fo = UserFile.FileWrapper(fo, logfile=logfile)
        return self.parse_orig(fo)
    parser.parse = new.instancemethod(parse, parser, parser.__class__)
    return parser

class Enumeration(tuple):
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, tuple.__repr__(self))
    def __str__(self):
        return "(%s)" % ", ".join(map(repr, self))

class AttributeList(list):
    def __repr__(self):
        cl = self.__class__
        s = ["%s.%s([" % (cl.__module__, cl.__name__)]
        for item in self:
            s.append("%r, " % (item,))
        s.append("])")
        return "\n         ".join(s)

    def __str__(self):
        return " ".join(map(str, self))

class IDREFS(AttributeList):
    def add_ref(self, value):
        self.data.append(IDREF(value))

class ENTITIES(AttributeList):
    pass

class NMTOKENS(AttributeList):
    pass


class _AttributeType(str):
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, self)

class CDATA_ATT(_AttributeType):
    pass

class ID(_AttributeType):
    pass

class IDREF(_AttributeType):
    pass

class NMTOKEN(_AttributeType):
    pass

class ENTITY(_AttributeType):
    pass


PCDATA = Text
ANY = True
EMPTY = None

# enumerations
AT_CDATA = 1
AT_ID = 2
AT_IDREF = 3
AT_IDREFS = 4
AT_ENTITY = 5
AT_ENTITIES = 6
AT_NMTOKEN = 7
AT_NMTOKENS = 8

REQUIRED = 11   # attribute is mandatory
IMPLIED = 12    # inherited from environment if not specified
DEFAULT = 13    # default value for enumerated types (added by parser)
FIXED = 14      # always the same, fixed, value.

_ATTRTYPEMAP = {
    u"CDATA": AT_CDATA,
    u"ID": AT_ID,
    u"IDREF": AT_IDREF,
    u"IDREFS": AT_IDREFS,
    u"ENTITY": AT_ENTITY,
    u"ENTITIES": AT_ENTITIES,
    u"NMTOKEN": AT_NMTOKEN,
    u"NMTOKENS": AT_NMTOKENS
}

_ATTRCLASSMAP = {
    AT_CDATA: CDATA_ATT,
    AT_ID: ID,
    AT_IDREF: IDREF,
    AT_IDREFS: IDREFS,
    AT_ENTITY: ENTITY,
    AT_ENTITIES: ENTITIES,
    AT_NMTOKEN: NMTOKEN,
    AT_NMTOKENS: NMTOKENS
}

_DEFAULTMAP = {
    u'#REQUIRED': REQUIRED,
    u'#IMPLIED': IMPLIED,
    u'#DEFAULT': DEFAULT,
    u'#FIXED': FIXED,
}

class XMLAttribute(object):
    """Holds information from the DTD, instantiated from compiled dtd
    module.
    """
    __slots__ = ["name", "a_type", "a_decl", "default", "_is_enumeration"]
    def __init__(self, name, a_type, a_decl, a_def=None):
        self.name = name
        self._is_enumeration = False
        a_type_type = type(a_type)
        if a_type_type is int: # from the generated file
            self.a_type = _ATTRCLASSMAP.get(a_type, a_type)
        elif a_type_type is unicode: # from the parser
            self.a_type = _ATTRTYPEMAP.get(a_type, a_type)
        elif issubclass(a_type_type, list):
            self.a_type = Enumeration(a_type)
            self._is_enumeration = True
        else:
            self.a_type = a_type
        # declaration
        # convert string to int value when generating, just use the int
        # when imported from Python dtd format.
        self.a_decl = _DEFAULTMAP.get(a_decl, a_decl)
        self.default = a_def

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r, %r, %r)" % (cl.__module__, cl.__name__, 
                               self.name, self.a_type, self.a_decl, self.default)

    def __hash__(self):
        return hash((self.name, self.a_type, self.a_decl, self.default))

    def __nonzero__(self):
        return True

    # Generate a unique identifier for internal use in dtd module.
    # TODO verify the enumerations are unique enough.
    def get_identifier(self):
        h = self.__hash__()
        h *= h # make non-negative
        return "attrib%s_%s" % (identifier(normalize_unicode(self.name)), h)

    def verify(self, value):
        if self._is_enumeration:
            if value not in self.a_type:
                raise ValidationError(
                        "Enumeration has wrong value for %r. %r is not one of %r." % (
                        self.name, value, self.a_type))
        elif self.a_decl == FIXED:
            if value != self.default:
                raise ValidationError(
                        "Bad value for FIXED attrib for %r. %r must be %r." % (
                        self.name, value, self.default))
        return True


class UnknownXMLAttribute(object):
    def verify(self, value):
        raise ValidationError("Can't validate unknown attribute: %r" % (self.name,))


#########################################################
# Utility functions
#########################################################

def normalize_unicode(uni):
    return unicodedata.normalize("NFKD", uni).encode("ASCII", "ignore")

def swapPOM(dst, src=None):
    """Replace dest in a DOM tree with source, returning detached tree (dest)."""
    if src:
        return dst.replace(src)
    else:
        return dst.detach()

def _find_element(elname, modules):
    for mod in modules:
        try:
            return getattr(mod, elname)
        except AttributeError:
            continue
    return None

def _construct_node(name, modules):
    if "[" not in name:
        nc = _find_element(name, modules)
        if nc is None:
            raise ValidationError, "no such element name %r in modules" % (name,)
        return nc() # node
    else:
        xpath_re = re.compile(r'(\w*)(\[.*])')
        mo = xpath_re.match(name)
        if mo:
            attdict = {}
            ename, attribs = mo.groups()
            nc = _find_element(ename, modules)
            if nc is None:
                raise ValidationError, "no such element name in modules"
            attribs = attribs[1:-1].split("and") # chop brackets and split on 'and'
            attribs = map("".strip, attribs) # strip whitespace
            for att in attribs:                  # dict elememnts are name and vaue
                name, val = att.split("=")
                attdict[name[1:]] = val[1:-1]
        return apply(nc, (), attdict)


def make_node(path, modules, value=None):
    """
    Makes a node or an XML fragment given a path, element module list, and an
    optional value.
    """
    if type(modules) is not list:
        modules = [modules]
    pathelements = path.split("/")
    if not pathelements[0]: # delete possible empty root node
        del pathelements[0]
    rootnode = current = _construct_node(pathelements[0], modules)
    for element in pathelements[1:]:
        new = _construct_node(element, modules)
        current.append(new)
        current = new
    current.set_inline()
    if value is not None:
        current.add_text(value)
    return rootnode

def unescape(s):
    if u'&' not in s:
        return s
    s = s.replace(u"&lt;", u"<")
    s = s.replace(u"&gt;", u">")
    s = s.replace(u"&apos;", u"'")
    s = s.replace(u"&quot;", u'"')
    s = s.replace(u"&amp;", u"&") # Must be last
    return s

def escape(s):
    s = s.replace(u"&", u"&amp;") # Must be first
    s = s.replace(u"<", u"&lt;")
    s = s.replace(u">", u"&gt;")
    s = s.replace(u"'", u"&apos;")
    s = s.replace(u'"', u"&quot;")
    return s

