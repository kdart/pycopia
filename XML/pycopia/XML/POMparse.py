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
Pythonic Object Model parser.
"""

import sys
import re

from htmlentitydefs import name2codepoint

from pycopia.XML import POM
from pycopia import dtds
from pycopia.textutils import identifier, keyword_identifier

def write_error(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")

XML_HEADER_RE = re.compile(r'xml version="([0123456789.]+)" encoding="([A-Z0-9-]+)"', re.IGNORECASE)
POMMODULE = POM.__name__


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


PCDATA = POM.Text
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
    u'#REQUIRED': POM.REQUIRED,
    u'#IMPLIED': POM.IMPLIED,
    u'#DEFAULT': POM.DEFAULT,
    u'#FIXED': POM.FIXED,
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
            self.a_type = POM._ATTRCLASSMAP.get(a_type, a_type)
        elif a_type_type is unicode: # from the parser
            self.a_type = _ATTRTYPEMAP.get(a_type, a_type)
        elif issubclass(a_type_type, list):
            self.a_type = POM.Enumeration(a_type)
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
        return "%s.%s(%r, %r, %r, %r)" % (POMMODULE, cl.__name__,
                               self.name, self.a_type, self.a_decl, self.default)

    def __hash__(self):
        return hash((self.name, self.a_type, self.a_decl, self.default))

    def __nonzero__(self):
        return True

    # Generate a unique identifier for internal use in dtd module.
    def get_identifier(self):
        h = self.__hash__()
        h = h**2 if h < 0 else h # make non-negative
        return "attrib%s_%s" % (identifier(POM.normalize_unicode(self.name)), h)

    def verify(self, value):
        if self._is_enumeration:
            if value not in self.a_type:
                raise POM.ValidationError(
                        "Enumeration has wrong value for %r. %r is not one of %r." % (
                        self.name, value, self.a_type))
        elif self.a_decl == FIXED:
            if value != self.default:
                raise POM.ValidationError(
                        "Bad value for FIXED attrib for %r. %r must be %r." % (
                        self.name, value, self.default))
        return True


class UnknownXMLAttribute(object):
    def verify(self, value):
        raise POM.ValidationError("Can't validate unknown attribute: %r" % (self.name,))


#### new sax2 parser ###
class ContentHandler(object):

    def __init__(self, doc=None, doc_factory=POM.new_document, logfile=None):
        self._locator = None
        self.stack = []
        self.msg = None
        self.doc = doc # call set_root on this when document fully parsed.
        self._doc_factory = doc_factory
        self.encoding = POM.DEFAULT_ENCODING # default to regenerate as
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
            raise POM.ValidationError("unbalanced document!")
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
            raise POM.ValidationError("Undefined element tag: " + name)
        attr = {}
        for name, value in atts.items():
            attr[keyword_identifier(POM.normalize_unicode(name))] = POM.unescape(value)
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
            self.stack[-1].append(POM.Text(text))

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
            raise POM.ValidationError("unknown DOCTYPE: %r" % (publicId,))
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
        logfile=None, doc_factory=POM.new_document):
    import xml
    if hasattr(xml, "use_pyxml"):
        xml.use_pyxml()
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
    def parse(self, url, data=None, encoding=POM.DEFAULT_ENCODING,
                                    useragent=None, accept=None):
        from pycopia.WWW import urllibplus
        fo = urllibplus.urlopen(url, data, encoding, useragent=useragent, accept=accept)
        if logfile:
            from pycopia import UserFile
            fo = UserFile.FileWrapper(fo, logfile=logfile)
        return self.parse_orig(fo)
    parser.parse = new.instancemethod(parse, parser, parser.__class__)
    return parser

def _test(argv):
    pass # XXX

if __name__ == "__main__":
    _test(sys.argv)

