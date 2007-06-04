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
from htmlentitydefs import name2codepoint

from pycopia.aid import IF
from pycopia.textutils import identifier

from pycopia.XML import XMLVisitorContinue, ValidationError

DEFAULT_ENCODING = sys.getdefaultencoding()

def set_default_encoding(newcodec):
    global DEFAULT_ENCODING
    newcodec = str(newcodec)
    import codecs
    try:
        codecs.lookup(newcodec)
    except LookupError, err:
        raise ValueError, err.args[0]
    old = DEFAULT_ENCODING
    DEFAULT_ENCODING = newcodec
    return old

# Allow attributes to be keyword names with "_" appended.
_KEYWORDS = {}
import keyword
for kw in keyword.kwlist:
    _KEYWORDS[kw+"_"] = kw
del kw, keyword


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
        self.data = unescape(POMString(data, encoding))
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data):
        self.data = unescape(POMString(data, self.encoding)) + self.data
    def add_text(self,data, encoding=None):
        self.data += unescape(POMString(data, encoding or self.encoding))
    append = add_text
    __iadd__ = add_text
    def __add__(self, other):
        return self.__class__(self.data + other.data)
    def __str__(self):
        return escape(str(self.data))
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
    def emit(self, fo):
        fo.write( escape(self.data) )
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
        return "\n<![CDATA[%s]]>\n" % (self.data,)
    def __unicode__(self):
        return u"<![CDATA[\n%s\n]]>\n" % (self.data,)
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.data)
    def emit(self, fo):
        fo.write("\n<![CDATA[")
        fo.write(self.data)
        fo.write("]]>\n")

class Comment(Text):
    def __init__(self, data="", encoding=DEFAULT_ENCODING):
        self._parent = None
        self.set_text(data, encoding)
    def __str__(self):
        return "<!-- %s -->" % (self._fix(self.data),)
    def __unicode__(self):
        return u"<!-- %s -->" % (self._fix(self.data),)
    def emit(self, fo):
        fo.write( self.__str__() )
    def set_text(self, data, encoding=DEFAULT_ENCODING):
        self.data = POMString(data, encoding)
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data):
        self.data = POMString(data, self.encoding) + self.data
    def add_text(self, data, encoding=None):
        self.data += POMString(data, encoding or self.encoding)
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
        self.data = POMString(data, encoding)
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data):
        raise NotImplementedError
    def add_text(self,data, encoding=None):
        self.data += POMString(data, encoding or self.encoding)
    append = add_text
    __iadd__ = add_text
    def __str__(self):
        return str(self.data)
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
            return `self.data`
    fullpath = property(_fullpath)
    def emit(self, fo):
        fo.write( self.data )
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
        self.uri = str(uri)
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
    def __init__(self, name, value, namespace=""):
        self.name = name
        self.value = value
        self.namespace = namespace
    def __str__(self):
        if self.namespace:
            return '%s:%s="%s"' % (self.namespace, self.name, escape(str(self.value)))
        else:
            return '%s="%s"' % (self.name, escape(str(self.value)))
    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.name, self.value, self.namespace)
    def __nonzero__(self):
        return bool(self.name)


class ProcessingInstruction(object):
    pass # XXX

# abstract base class for generic XML node generation.
# Create an XML node by subclassing this and defining allowed attribute names
# in ATTLIST. CONTENTMODEL holds the content specification from the DTD.
# Use the dtd2py program to convert a DTD to a python module that has classes
# for element types. Use that python dtd as a paramter for the POMDocument,
# below.

class ElementNode(object):
    ATTLIST = None
    CONTENTMODEL = None
    _name = None
    _namespaces = None
    _default_namespace = None
    _acquired = {"_namespaces":None, "_default_namespace":None  } # acquired attributes
    def __init__(self, **attribs):
        kwd = _KEYWORDS
        self._attribs = {}
        self._namespaces = {}
        for key, value in attribs.items():
            key = kwd.get(key, key)
            if self._validate_attribute(key, value):
                self._attribs[key] = POMAttribute(key, value)
            elif key.startswith("xmlns:"):
                ns = NameSpace(key, value)
                self._namespaces[ns.name] = ns
            elif key.startswith("xmlns"):
                ns = NameSpace(key, value)
                self._default_namespace = ns
            elif ":" in key:
                ns, name = key.split(":", 1)
                if self._validate_attribute(name, value):
                    assert str(self._namespace) == ns
                    self._attribs[key] = POMAttribute(name, value, ns)
                else:
                    raise ValidationError, \
                    "Invalid attribute name (%s) for this element (%s)." % \
                    (key, self._name)
            else:
                raise ValidationError, \
                    "Invalid attribute name (%s) for this element (%s)." % \
                    (key, self._name)
        self._children = []
        self._parent = None

    # check if attribute name is defined for this element
    def _validate_attribute_name(self, name):
        if self.ATTLIST:
            for xmlattr in self.ATTLIST:
                if name == xmlattr.name:
                    return True
        return False

    def _validate_attribute(self, name, value):
        if self.ATTLIST:
            for xmlattr in self.ATTLIST:
                if name == xmlattr.name:
                    return xmlattr.verify(value)
        return False

    def _verify_attributes(self):
        if not self.ATTLIST:
            return None
        for attr in self.ATTLIST:
            aval = self._attribs.get(attr.name, None)
            if aval is None:
                if attr.a_decl == REQUIRED:
                    raise ValidationError, \
                        "required attribute not present: %s" % (attr.name,)
            else:
                attr.verify(aval.value)

    def _get_attribute(self, name):
        if not self.ATTLIST:
            return None
        try:
            return self._attribs[name].value
        except KeyError:
            # might be implied, fixed, or enum...
            for xmlattr in self.ATTLIST:
                if name == xmlattr.name:
                    if xmlattr.a_decl == IMPLIED:
                        return ""
                    elif xmlattr.a_decl == FIXED:
                        return xmlattr.default
                    elif xmlattr.a_decl == DEFAULT: # an enum type
                        return xmlattr.default
        return None

    def get_parent(self):
        return self._parent
    parent = property(get_parent)

#    def reparent(self, newparent):
#        if self._parent:
#            i = self._parent.index(self)
#        newparent.append(self)

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

    def set_namespace(self, ns):
        self._namespace = ns

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

    def hasAttributes(self):
        return bool(self._attribs)
    has_attributes = hasAttributes

    def has_attribute(self, name):
        return self._attribs.has_key(name)

    def attributes(self):
        return map(lambda o: o.name, self.ATTLIST)

    def has_children(self):
        return len(self._children)

    def set_attribute(self, name, val, ns=None):
        """set_attribute(name, value) This exists to set attributes that
        have names with characters that make it an illegal Python
        identifier.  """
        ns = ns or self._default_namespace
        if self._validate_attribute(name, val):
            self._attribs[name] = POMAttribute(name, val, ns)

    def get_attribute(self, name):
        """get_attribute(name) Use this method to get attributes that have
        names with characters that make it an illegal Python identifier.
        """
        return self._get_attribute(name)

    def __setattr__(self, name, value):
        if self._validate_attribute(name, value):
            self._attribs[name] = POMAttribute(name, value, self._default_namespace)
        else:
            self.__dict__[name] = value

    # this plus the _parent and _acquired attributes implement "acquisiton",
    # or run-time inheritance.
    def __getattr__(self, name):
        defval = self._get_attribute(name)
        if defval is not None:
            return defval
        try:
            return self._acquire(name)
        except:
            pass
        raise AttributeError, "AttributeError: %s has no attribute '%s'" % (self._name, name)

    def _acquire(self, name):
        if self._parent:
            try:
                return self._parent.__dict__[name]
            except KeyError:
                pass
            return self._parent._acquire(name)
        else:
            try:
                return self._acquired[name]
            except KeyError:
                pass
        raise AttributeError

    def __delattr__(self, name):
        del self._attribs[name]

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
#       self._children[index].destroy()
        del self._children[index]

    def __repr__(self):
        attrs = map(lambda t: '%s=%r' % t, self._attribs.items())
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, ", ".join(attrs))

    def __str__(self):
        self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            return self._empty_str()
        else:
            return self._non_empty_str()

    def _get_ns(self):
        return self._default_namespace or "" # XXX
        return IF(self._namespace, "%s:" % self._namespace, "")

    def _non_empty_str(self):
        s = ["<%s%s%s>" % (self._get_ns(), self._name, self._attr_str())]
        map(s.append, map(str, self._children))
        s.append("</%s%s>" % (self._get_ns(), self._name))
        return "".join(s)

    def _empty_str(self):
        return "<%s%s%s />" % (self._get_ns(), self._name, self._attr_str())

    def _attr_str(self):
        attrs = map(str, self._attribs.values())
        attrs.insert(0, "") # for space before first attribute
        return " ".join(attrs)

    def get_iterator(self, writer=None):
        """Return an iterable of the content."""
        it = WSGIAdapter(writer=writer)
        self.emit(it)
        return it

    def emit(self, fo):
        self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            fo.write(self._empty_str())
        else:
            fo.write("<%s%s%s>" % (self._get_ns(), self._name, self._attr_str()))
            map(lambda o: o.emit(fo), self._children)
            fo.write("</%s%s>" % (self._get_ns(), self._name))

    def walk(self, visitor):
        try:
            visitor(self)
        except XMLVisitorContinue:
            return
        for node in self._children:
            node.walk(visitor)

    # methods for node path manipulation
    def pathname(self):
        """pathname() returns the ElementNode as a string in xpath format."""
        if self._attribs:
            s = map(lambda i: "@%s='%s'" % (i[0],i[1]), self._attribs.items())
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
            xpath_re = re.compile(r'(\w+)\[(.*)]') # XXX still needs work
            mo = xpath_re.match(pathelement)
            if mo:
                name, match = mo.groups()
                if name != self._name:
                    return False
                mp = match.split("=")
                attr = self._get_attribute(mp[0][1:])
                if attr is None:
                    return False
                if len(mp) > 1:
                    return mp[1][1:-1] == attr
                else:
                    return True
            else:
                raise ValueError, "Invalid path element"

    def find_elements(self, pathelement):
        rv = []
        for child in self._children:
            if child.matchpath(pathelement):
                rv.append(child)
        return rv

    def get_element(self, pathelement):
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


class ContentModel(object):
    """Represents and validates a content model.  """
    def __init__(self, rawmodel=None):
        self.model = rawmodel # TODO need actual content model...

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.model)

    def is_empty(self):
        return not self.model


class Fragments(ElementNode):
    """Fragments is a special holder class to hold 'loose' markup fragments.
    That is, bits of markup that don't have a common container (e.g. not in
    root element).  It is invisible."""
    def __str__(self):
        s = []
        map(s.append, map(str, self._children))
        return "".join(s)

    def emit(self, fo):
        map(lambda o: o.emit(fo), self._children)

    def matchpath(self, pathelement):
        return False


class POMString(unicode):
    def __new__(cls, arg, enc=DEFAULT_ENCODING):
        if isinstance(arg, unicode):
            return unicode.__new__(cls, arg)
        else:
            return unicode.__new__(cls, str(arg), enc)


class POMTimeStamp(long):
    pass


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
            if str(mo.group(1)) in self._inline:
                return self._fo.write(data)
            else:
                self._fo.write("\n"+"  "*self._level)
                self._level += 1
                return self._fo.write(data)
        return self._fo.write(data)


class WSGIAdapter(object):
    """Adapt the emit() method of a document to the WSGI spec. It is an
    iterable object that you can return to the WSGI caller. This is also
    the file-like for the document's (or node's) emit() method.
    First, pass this to a document or node's emit() method. Then, return
    it to the WSGI caller.
    Alternatively, use the WSGI write function by passing it to the
    constructor.

    Use it like this:

    def SampleApp(environ, start_response): # use write callabled
      doc = <POMDocument from somewhere>
      response = "200 OK"
      headers = [("Content-Type", doc.MIMETYPE)]
      writer = start_response(response, headers)
      it = WSGIAdapter(writer=writer)
      doc.emit(it)
      return it

    def SampleApp2(environ, start_response): # use iterator
      doc = <POMDocument from somewhere>
      it = WSGIAdapter(doc.MIMETYPE)
      start_response(it.response, it.headers)
      doc.emit(it)
      return it

    """
    def __init__(self, mimetype=None, writer=None):
        if writer:
            self.write = writer # override write method
        self._chunks = []
        self.length = 0
        self._response = "200 OK"
        self._mimetype = mimetype

    def __iter__(self):
        return iter(self._chunks)

    def __len__(self):
        return self.length

    def close(self):
        self._chunks = []

    #  emit() calls this
    def write(self, data):
        try:
            self.length += len(data)
            self._chunks.append(data)
        finally:
            self._response = "500 Writer error"

    def get_headers(self):
        if self.length:
            rv = [("Content-Length", str(self.length))]
        else:
            rv = []
        if self._mimetype:
            rv.append(("Content-Type", self._mimetype))
        return rv

    def get_response(self):
        return self._response

    def set_mimetype(self, mimetype):
        self._mimetype = mimetype

    headers = property(get_headers, None, None, "WSGI style header list")
    response = property(get_response)
    mimetype = property(lambda s: s._mimetype, set_mimetype)


# base class for whole POM documents, including Header.
class POMDocument(object):
    DOCTYPE = ""
    MIMETYPE = "application/xml" # reset in subclass
    def __init__(self, dtd=None, encoding=DEFAULT_ENCODING):
        self.dtds = []
        self.root = None
        self.parser = None
        self.dirty = 0
        self._idmap = {}
        self.set_encoding(encoding)
        if dtd:
            self.add_dtd(dtd)

    def set_encoding(self, encoding):
        # verify encoding is valid
        import codecs
        try:
            codecs.lookup(encoding)
        except LookupError, err:
            raise ValueError, "Invalid character encoding: %r" % (err.args[0],)
        self.XMLHEADER = '<?xml version="1.0" encoding="%s"?>\n' % (encoding,)
        self.encoding = encoding

    def set_doctype(self, doctype):
        self.DOCTYPE = str(doctype)

    def __str__(self):
        return self.XMLHEADER + self.DOCTYPE + str(self.root) + "\n"

    def get_iterator(self, writer=None):
        """Return an iterable of the document content.  """
        it = WSGIAdapter(self.MIMETYPE, writer)
        self.emit(it)
        return it

    def emit(self, fo):
        fo.write(self.XMLHEADER)
        fo.write(self.DOCTYPE)
        fo.write("\n")
        self.root.emit(fo)
        fo.write("\n")

    def walk(self, visitor):
        self.root.walk(visitor)

    def set_dirty(self, val=1):
        self.dirty = val

    def set_root(self, root):
        """Forcibly set the root document. Be careful with this."""
        if isinstance(root, ElementNode):
            self.root = root
        else:
            raise ValueError, "root document must be POM ElementNode."

    def add_dtd(self, dtdmod):
        self.dtds.append(dtdmod)

    def set_dtd(self, dtdmod):
        self.dtds = [dtdmod]

    def get_parser(self, namespaces=0, validate=0, external_ges=0, 
            external_pes=0, logfile=None):
        self.parser = get_document_parser(self, namespaces, validate, 
                external_ges, external_pes, logfile)
        return self.parser

    def del_parser(self):
        self.parser = None

    def parse(self, url, data=None, encoding=DEFAULT_ENCODING):
        if not self.parser:
            self.get_parser()
        self.parser.parse(url, data=data, encoding=encoding)
        self.del_parser()

    def parseFile(self, fo, **kwargs):
        if not self.parser:
            self.get_parser(**kwargs)
        self.parser.parseFile(fo)
        self.del_parser()

    def parseString(self, string, **kwargs):
        if not self.parser:
            self.get_parser(**kwargs)
        self.parser.feed(string)
        self.parser.close()
        self.del_parser()

    def write_xmlfile(self, filename=None):
        filename = filename or self.filename
        if filename:
            fo = open(os.path.expanduser(filename), "w")
            try:
                self.emit(fo)
            finally:
                fo.close()
        self.dirty = 0
    writefile = write_xmlfile

    def get_document(self, filename, **kwargs):
        self.get_parser(**kwargs)
        self.parse(filename)
        self.filename = filename
        self.del_parser()

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



#### new sax2 parser ###

class ContentHandler(object):
    XML_RE = re.compile(r'xml version="([0123456789.]+)" encoding="([A-Z0-9-]+)"', re.IGNORECASE)

    def __init__(self, doc, logfile=None):
        self._locator = None
        self.stack = []
        self.msg = None
        self.doc = doc # call set_root on this when document fully parsed.
        self.modules = []
        if logfile:
            self._errormethod = logfile.write
        else:
            self._errormethod = sys.stderr.write

    def _get_class(self, name):
        klass = None
        for mod in self.doc.dtds:
            try:
                klass = getattr(mod, identifier(name))
            except AttributeError:
                continue
            if klass:
                return klass
        raise AttributeError

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startDocument(self):
        self.stack = []

    def endDocument(self):
        if self.stack: # stack should be empty now
            raise ValidationError, "unbalanced document!"
        self.doc.set_root(self.msg)
        self.msg = None
        self.doc = None # release doc reference

    def startElement(self, name, atts):
        "Handle an event for the beginning of an element."
        try:
            klass = self._get_class(name)
        except AttributeError:
            raise ValidationError, "Undefined element tag: " + name
        attr = {} # atts is a instance with unicode keys.. must convert to str..
        for name, value in atts.items():
            attr[str(name)] = unescape(str(value))
        obj = klass(**attr)
        self.stack.append(obj)

    def endElement(self, name):
        "Handle an event for the end of an element."
        obj = self.stack.pop()
        if self.stack:
            self.stack[-1].append(obj)
        else:
            self.msg = obj

    def characters(self, text):
        if self.stack and text:
            self.stack[-1].append(Text(text))

    def processingInstruction(self, target, data):
        'handle: xml version="1.0" encoding="ISO-8859-1"?'
        mo = self.XML_RE.match(data)
        if mo:
            version, encoding = mo.groups()
            assert version == "1.0"
            self.doc.set_encoding(encoding)
        else:
            self._errormethod("!!! Unhandled pi: %r" % (data,))

    def startPrefixMapping(self, prefix, uri):
        self._errormethod("unhandled startPrefixMapping: %s %s" % (prefix, uri))

    def endPrefixMapping(self, prefix):
        self._errormethod("unhandled endPrefixMapping: %s" % (prefix,))

    def skippedEntity(self, name):
        if self.stack:
            self.stack[-1].add_text(str(unichr(name2codepoint[name])))

    def ignorableWhitespace(self, whitespace):
        self._errormethod("unhandled ignorableWhitespace: %r" % (whitespace,))

    # TODO handle namespaces
    def startElementNS(self, cooked_name, name, attributesns):
        self._errormethod("unhandled startElementNS: %r %r %r" % ( 
                               cooked_name, name, attributesns))

    def endElementNS(self, name, rawname):
        self._errormethod("unhandled endElementNS: %r %r" % (name, rawname))

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
        # TODO handle external entities by getting python compiled version
        # or fetching and compiling it.
        return FakeFile(systemId)

class FakeFile(object):
    def __init__(self, name):
        self.name = name
    def read(self, amt=None):
        return ""

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


def get_document_parser(document, namespaces=0, validate=0, external_ges=0,
        external_pes=0, logfile=None):
    import xml.sax.sax2exts
    import xml.sax.handler
    import new
    #import xml.sax.handler
    handler = ContentHandler(document, logfile)
    errorhandler = ErrorHandler(logfile)
    # create parser 
    parser = xml.sax.sax2exts.XMLParserFactory.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, namespaces)
    parser.setFeature(xml.sax.handler.feature_validation, validate)
    parser.setFeature(xml.sax.handler.feature_external_ges, external_ges)
    parser.setFeature(xml.sax.handler.feature_external_pes, external_pes)
    # set handlers 
    parser.setContentHandler(handler)
    parser.setDTDHandler(handler)
    parser.setEntityResolver(handler)
    parser.setErrorHandler(errorhandler)
    # since the xml API provides some generic parser I can't just
    # subclass I have to "patch" the object in-place with this trick.
    # This is to a) make the API compatible with the HTMLParser, and b)
    # allow specifing the encoding in the request.
    parser.parse_orig = parser.parse
    def parse(self, url, data=None, encoding=DEFAULT_ENCODING):
        fo = urlopen(url, data, encoding)
        return self.parse_orig(fo)
    parser.parse = new.instancemethod(parse, parser, parser.__class__)
    return parser


def urlopen(url, data=None, encoding="utf-8", useragent=None):
    """Get a URL with a particular character encoding.
    Like urllib, but allows requesting a document encoding, and has more
    "realistic" headers.
    Parameters:
        url:
            The full URL to fetch.
        data:
            A set of data to post. See the docs for urllib2.
        encoding:
            The character encoding to accept. Default to utf-8.
    """
    import urllib2
    req = urllib2.Request(url, data)
    # just in case server checks browser type.
    req.add_header("User-Agent", 
            useragent or "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.13) Gecko/20060418")
    # We want XHTML
    req.add_header("Accept",
            "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9")
    # the charset we want
    req.add_header("Accept-Charset", "%s;q=0.9,*;q=0.7" % (encoding,))
    return urllib2.urlopen(req)


def get_parser(dtd, **kwargs):
    doc = POMDocument(dtd)
    return doc.get_parser(**kwargs)


class Enumeration(list):
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, list.__repr__(self))
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
    "CDATA": AT_CDATA,
    "ID": AT_ID,
    "IDREF": AT_IDREF,
    "IDREFS": AT_IDREFS,
    "ENTITY": AT_ENTITY,
    "ENTITIES": AT_ENTITIES,
    "NMTOKEN": AT_NMTOKEN,
    "NMTOKENS": AT_NMTOKENS
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
    def __init__(self, name, a_type, a_decl, a_def=None):
        self.name = str(name)
        a_type_type = type(a_type)
        #a_decl_type = type(a_decl)
        if a_type_type is unicode: # from the parser
            self.a_type = _ATTRTYPEMAP.get(str(a_type), a_type)
#       elif a_type_type is tuple or a_type_type is list:
#           self.a_type = a_type # XXX
        elif a_type_type is int: # from the generated file
            self.a_type = _ATTRCLASSMAP.get(a_type, a_type)
        elif a_type_type is list:
            self.a_type = Enumeration(map(str, a_type))
        else:
            self.a_type = a_type
        # declaration
        # convert string to int value when generating, just use the int when imported from Python dtd format.
        self.a_decl = _DEFAULTMAP.get(a_decl, a_decl)
        self.default = a_def
        # save the type to speed verify
        self.a_type_type = type(self.a_type)

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r, %r, %r)" % (cl.__module__, cl.__name__, self.name, self.a_type, self.a_decl, self.default)

    def verify(self, value):
        if issubclass(type(self.a_type), list):
            if value not in self.a_type:
                raise ValidationError, "Enumeration has wrong value. %s is not one of %r." % (value, self.a_type)
        elif self.a_decl == FIXED:
            if value != self.default:
                raise ValidationError, "Bad value for FIXED attributed. %r must be %r." % (value, self.default)
        return True


#########################################################
# Utility functions
#########################################################

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
            raise ValidationError, "no such element name in modules"
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
    if '&' not in s:
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

