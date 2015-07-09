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
This module implements the XML POM -- the Python Object Model for XML. It is
something like DOM, but more Pythonic, and easier to use. These base classes
are used to build POM source files which are self-validating python-based XML
constructor objects. The major parts of the dtd2py command line tool are also
here.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


import sys, os, re
import codecs
import unicodedata

try: # python 3 compatibility
    maxint = sys.maxint
except AttributeError:
    maxint = sys.maxsize

from pycopia.textutils import identifier, keyword_identifier
from pycopia import dtds
from pycopia.XML import XMLVisitorContinue, ValidationError, XMLPathError

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
    except LookupError as err:
        raise ValueError(err.args[0])

set_default_encoding("utf-8")


if sys.version_info.major == 2:
    def to_unicode(arg, encoding):
        if isinstance(arg, unicode):
            return arg
        return unicode(str(arg), encoding or DEFAULT_ENCODING)
else:
    def to_unicode(arg, encoding):
        if isinstance(arg, bytes):
            return str(arg, encoding)
        return str(arg)


# attribute types
REQUIRED = 11   # attribute is mandatory
IMPLIED = 12    # inherited from environment if not specified
DEFAULT = 13    # default value for enumerated types (added by parser)
FIXED = 14      # always the same, fixed, value.


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
        self.data = uunescape(to_unicode(data, encoding))
        self.encoding = encoding
    def get_text(self):
        return self.data
    def insert(self, data):
        self.data = unescape(data) + self.data
    def add_text(self,data):
        self.data += unescape(data)
    append = add_text
    __iadd__ = add_text
    def __add__(self, other):
        return self.__class__(self.data + other.data)
    def emit(self, fo, encoding=None):
        fo.write( escape(self.data.encode(encoding or self.encoding) ))
    def encode(self, encoding):
        return escape(self.data.encode(encoding))
    def __str__(self):
        return self.encode(self.encoding)
    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r, %r)" % (cl.__module__, cl.__name__, self.data, self.encoding)
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
            return repr(self.data)
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
        return b"\n<![CDATA[%s]]>\n" % self.data.encode(encoding)

    def __repr__(self):
        cl = self.__class__
        return b"%s.%s(%r)" % (cl.__module__, cl.__name__, self.data)

    def emit(self, fo, encoding=None):
        fo.write(b"\n<![CDATA[")
        fo.write( self.data.encode(encoding or self.encoding) )
        fo.write(b"]]>\n")


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
        return b"<!-- %s -->" % self._fix(self.data.encode(encoding))
    def emit(self, fo, encoding=None):
        fo.write( b"<!-- %s -->" % self._fix(self.data.encode(encoding or self.encoding) ))
    def get_text(self):
        return self.data
    def insert(self, data, encoding=None):
        self.data = to_unicode(data, encoding) + self.data
    def add_text(self, data, encoding=None):
        self.data += to_unicode(data, encoding)
    append = add_text
    def _fix(self, data):
        data = escape(data)
        if data.find("--") != -1:
            data = data.replace("--", "- ")
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
        raise NotImplementedError("Cannot insert into ASIS")
    def add_text(self,data, encoding=None):
        self.data += to_unicode(data, encoding or self.encoding)
    append = add_text
    __iadd__ = add_text
    def __str__(self):
        return self.data.encode(self.encoding)
    def encode(self, encoding):
        return self.data.encode(encoding)
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


# runtime attribute object
class POMAttribute(object):
    __slots__ = ["name", "value", "namespace"]
    def __init__(self, name, value, namespace="", encoding=DEFAULT_ENCODING):
        self.name = to_unicode(name, encoding)
        self.value = to_unicode(value, encoding)
        self.namespace = to_unicode(namespace, encoding)

    def __hash__(self):
        return hash((self.name, self.value, self.namespace))

    def __str__(self):
        return '%s="%s"' % (name, value)

    def encode(self, encoding=DEFAULT_ENCODING):
        name = self.name.encode(encoding or self.encoding)
        value = escape(self.value.encode(encoding or self.encoding))
        return b'%s="%s"' % (name, value)

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self.name, self.value, self.namespace)

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
        self.__dict__["_namespace"] = ""
        self.__dict__["_encoding"] = DEFAULT_ENCODING
        for key, value in attribs.items():
            xmlattr = self.__class__.KWATTRIBUTES.get(key)
            if type(value) is tuple:
                atns, value = value
            else:
                atns = ""
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
                return xmlattr.default or ""
        return None
    getAttribute = get_attribute # JS compatibility

    def set_attribute(self, name, val, ns=""):
        """set_attribute(name, value)
        Set the element node attribute "name" to "value".
        The name can be the shorthand identifier, or the real name.
        """
        if ":" in name:
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
        raise AttributeError("Element %r has no attribute %r." % (self._name, name))

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
            raise ValueError("Must replace with another ElementNode")
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
        verify_encoding(encoding)
        self._encoding = encoding

    def index(self, obj):
        objid = id(obj)
        i = 0
        for o in self._children:
            if id(o) == objid:
                return i
            i += 1
        raise ValueError("ElementNode: Object not contained here.")

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
            self._children[-1].add_text(text)
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
            self._children[-1].add_text(text)
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
            raise IndexError("no elements match")
        else:
            return index

    def __getitem__(self, index):
        if type(index) is str:
            try:
                el =  self.get_element(index)
            except XMLPathError as err:
                raise KeyError(err)
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

    def encode(self, encoding, verify=False):
        if verify:
            self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            return self._empty_str(encoding)
        else:
            return self._non_empty_str(encoding)

    def set_namespace(self, ns):
        self._namespace = ns

    def del_namespace(self):
        self._namespace = ""

    namespace = property(lambda s: s._namespace, set_namespace, del_namespace)

    def _get_ns(self, encoding):
        return self._namespace.encode(encoding)

    def _non_empty_str(self, encoding):
        ns = self._get_ns(encoding)
        name = self._name.encode(encoding)
        s = [b"<%s%s%s>" % (ns, name, self._attr_str(encoding))]
        map(s.append, map(lambda o: o.encode(encoding), self._children))
        s.append(b"</%s%s>" % (ns, name))
        return b"".join(s)

    def _empty_str(self, encoding):
        return b"<%s%s%s />" % (self._get_ns(encoding), self._name.encode(encoding),
                       self._attr_str(encoding))

    def _attr_str(self, encoding):
        attrs = map(lambda o: o.encode(encoding), self._attribs.values())
        attrs.insert(0, b"") # for space before first attribute
        return b" ".join(attrs)

    def emit(self, fo, encoding=None, verify=False):
        enc = encoding or self._encoding
        if verify:
            self._verify_attributes()
        if not self.CONTENTMODEL or self.CONTENTMODEL.is_empty():
            fo.write(self._empty_str(enc))
        else:
            ns = self._get_ns(enc)
            name = self._name.encode(enc)
            fo.write(b"<%s%s%s>" % (ns, name, self._attr_str(enc)))
            map(lambda o: o.emit(fo, enc), self._children)
            fo.write(b"</%s%s>" % (ns, name))

    def validate(self, encoding=DEFAULT_ENCODING):
        ff = FakeFile(None)
        # Will raise a ValidationError if not valid.
        # Don't need full backtrace for this type of error.
        try:
            self.emit(ff, encoding)
        except ValidationError as err:
            raise ValidationError(err)

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
                raise ValueError("Path element %r not found." % (pathelement,))

    def find_elements(self, pathelement):
        rv = []
        for child in self._children:
            if child.matchpath(pathelement):
                rv.append(child)
        return rv


    def get_element(self, pathelement):
        mo = ElementNode._xpath_index_re.match(pathelement)
        if mo:
            elname = mo.group(1)
            elidx = int(mo.group(2)) - 1
            idx = 0
            for el in self._children:
                if isinstance(el, ElementNode) and el._name == elname:
                    if elidx == idx:
                        return el
                    else:
                        idx += 1
            raise XMLPathError("%s not indexed in %r." % (elname, self))
        else:
            for child in self._children:
                if child.matchpath(pathelement):
                    return child
        raise XMLPathError("%s not found in %r." % (pathelement, self))

    def elements(self, elclass):
        """Return iterator that iterates over list of elements matching elclass"""
        return NodeIterator(self, elclass)

    def getall(self, elclass, depth=maxint, collect=None):
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
            return " "
        else:
            nodes = self.getall(Text, maxint)
            return "".join(map(lambda s: s.get_text(), nodes))

    # XPath-like functions
    def comment(self):
        return self.getall(Comment, maxint)

    def text(self):
        return self.getall(Text, maxint)

    def processing_instruction(self):
        return self.getall(ProcessingInstruction, maxint)

    def node(self):
        return self.getall(ElementNode, maxint)


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
    XMLHEADER = b'<?xml version="1.0" encoding="%s"?>\n' % DEFAULT_ENCODING
    DOCTYPE = b""
    MIMETYPE = b"application/xml" # reset in subclass

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
                print ("Document warning: unknown root element.", file=sys.stderr)
            else:
                self.set_root(root)
        self.set_encoding(encoding)
        self.set_language(lang)

    def initialize(self):
        """New document initializer."""
        pass

    def set_encoding(self, encoding):
        verify_encoding(encoding)
        self.XMLHEADER = b'<?xml version="1.0" encoding="%s"?>\n' % (encoding,)
        self.encoding = encoding

    def set_language(self, lang):
        self.lang = lang
        if lang and self.root:
            self.root.xml_lang = lang

    def set_doctype(self, doctype):
        dt = dtds.get_doctype(doctype)
        if dt:
            self.DOCTYPE = str(dt).encode("ascii")
            self.set_dtd(dtds.get_dtd_module(doctype))
            rootclass = getattr(self.dtd, identifier(dt.name))
            self.set_root(rootclass())
        else:
            raise ValidationError("Invalid doctype: %r" % (doctype,))

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
            raise ValueError("root document must be POM ElementNode.")

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
        return self.XMLHEADER + self.DOCTYPE + self.root.encode(encoding) + b"\n"

    def emit(self, fo, encoding=DEFAULT_ENCODING):
        if encoding != self.encoding:
            self.set_encoding(encoding)
        fo.write(self.XMLHEADER)
        fo.write(self.DOCTYPE)
        self.root.emit(fo, encoding)
        fo.write(b"\n")

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
        from pycopia.XML import POMparse
        return POMparse.get_parser(self, **kwargs)

    def parse(self, url, data=None, encoding=DEFAULT_ENCODING, **kwargs):
        parser = self.get_parser(**kwargs)
        parser.parse(url, data=data, encoding=encoding)
        parser.close()

    def parseFile(self, fo, **kwargs):
        parser = self.get_parser(**kwargs)
        parser.parseFile(fo)

    def parseString(self, string, **kwargs):
        parser = self.get_parser(**kwargs)
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
            return node
        else:
            raise IndexError( "first path element not found")
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


class ContentModel(object):
    """Represents and validates a content model.  """
    def __init__(self, rawmodel=None):
        self.model = rawmodel

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%r)" % (cl.__module__, cl.__name__, self.model)

    def is_empty(self):
        return not self.model


class Enumeration(tuple):

    def __repr__(self):
        cl = self.__class__
        return "%s.%s(%s)" % (cl.__module__, cl.__name__, tuple.__repr__(self))

    def __str__(self):
        return "(%s)" % ", ".join(map(repr, self))

    def verify(self, value):
        return True


class XMLAttribute(object):
    """Holds information from the DTD, instantiated from compiled dtd
    module.
    """
    __slots__ = ["name", "a_type", "a_decl", "default", "_is_enumeration"]
    def __init__(self, name, a_type, a_decl, a_def=None):
        self.name = name
        self.a_type = a_type
        self.a_decl = a_decl
        self.default = a_def
        self._is_enumeration = False

        a_type_type = type(a_type)
        if a_type_type is int: # from the generated file
            self.a_type = object
        elif issubclass(a_type_type, list):
            self.a_type = Enumeration(a_type)
            self._is_enumeration = True

    def __nonzero__(self):
        return True

    def verify(self, value):
        return True


# Document constructors

def new_document(doctype, encoding=DEFAULT_ENCODING):
    dtd = dtds.get_dtd_module(doctype)
    doc = POMDocument(dtd=dtd)
    doc.set_encoding(encoding)
    return doc


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
            raise ValidationError("no such element name %r in modules" % (name,))
        return nc() # node
    else:
        xpath_re = re.compile(r'(\w*)(\[.*])')
        mo = xpath_re.match(name)
        if mo:
            attdict = {}
            ename, attribs = mo.groups()
            nc = _find_element(ename, modules)
            if nc is None:
                raise ValidationError("no such element name in modules")
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
    if b'&' not in s:
        return s
    s = s.replace(b"&lt;", b"<")
    s = s.replace(b"&gt;", b">")
    s = s.replace(b"&apos;", b"'")
    s = s.replace(b"&quot;", b'"')
    s = s.replace(b"&amp;", b"&") # Must be last
    return s

def uunescape(s):
    if '&' not in s:
        return s
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&") # Must be last
    return s


def escape(s):
    s = s.replace(b"&", b"&amp;") # Must be first
    s = s.replace(b"<", b"&lt;")
    s = s.replace(b">", b"&gt;")
    s = s.replace(b"'", b"&apos;")
    s = s.replace(b'"', b"&quot;")
    return s

if __name__ == "__main__":
    from pycopia import autodebug

