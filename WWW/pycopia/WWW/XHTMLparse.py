#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Parsing for XHTML documents.

"""

import sys
import re
import HTMLParser
from htmlentitydefs import name2codepoint

from pycopia.textutils import identifier
from pycopia import dtds
from pycopia.WWW import XHTML
from pycopia.XML import POM, ValidationError


# HTML POM parser. This parser populates the POM with XHTML objects, so this
# HTML parser essentially translates HTML to XHTML, hopefully with good
# results. Note that you can't regenerate the original HTML.
class _HTMLParser(HTMLParser.HTMLParser):
    def __init__(self, doc=None):
        self.reset()
        self.topelement = None
        self._encoding = POM.DEFAULT_ENCODING
        self.doc = doc
        self.stack = []
        self.comments = []

    def close(self):
        if self.stack:
            raise ValidationError("XHTML document has unmatched tags")
        HTMLParser.HTMLParser.close(self)
        self.doc.set_root(self.topelement)
        self.doc.comments = self.comments

    def parse(self, url, data=None, encoding=POM.DEFAULT_ENCODING, 
                                    useragent=None, accept=None):
        from pycopia.WWW import urllibplus
        fo = urllibplus.urlopen(url, data, encoding, useragent=useragent, accept=accept)
        self.parseFile(fo)
        self.close()

    def parseFile(self, fo):
        data = fo.read(16384)
        while data:
            self.feed(data)
            data = fo.read(16384)
        self.close()

    def _get_tag_obj(self, tag, attrs):
        attrdict = {}
        def fixatts(t):
            attrdict[str(t[0])] = t[1]
        map(fixatts, attrs)
        try:
            cl = getattr(self.doc.dtd, identifier(tag))
        except AttributeError, err:
            raise ValidationError("No tag in dtd: %s" % (err,))
        obj = cl(**attrdict)
        return obj

    def handle_starttag(self, tag, attrs):
        obj = self._get_tag_obj(tag, attrs)
        if obj.CONTENTMODEL.is_empty():
            self.stack[-1].append(obj)
            return
        self.stack.append(obj)

    def getContentHandler(self):
        return self # sax compatibility for our purposes...

    def handle_endtag(self, tag):
        "Handle an event for the end of a tag."
        obj = self.stack.pop()
        if self.stack:
            self.stack[-1].append(obj)
        else:
            self.topelement = obj

    def handle_startendtag(self, tag, attrs):
        obj = self._get_tag_obj(tag, attrs)
        self.stack[-1].append(obj)

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].add_text(data)
        else:
            pass

    def handle_charref(self, val):
           data = unichr(int(val))
           self.stack[-1].add_text(data)

    def handle_entityref(self, name):
        if self.stack:
            self.stack[-1].add_text(unichr(name2codepoint[name]))

    def handle_comment(self, data):
        cmt = POM.Comment(data)
        try:
            self.stack[-1].append(cmt)
        except IndexError: # comment is outside of root node
            self.comments.append(cmt)

    def handle_decl(self, decl):
        if decl.startswith("DOCTYPE"):
            if decl.find("Strict") > 1:
                self.doc = XHTML.new_document(dtds.XHTML1_STRICT, encoding=self._encoding)
            elif decl.find("Frameset") > 1:
                self.doc = XHTML.new_document(dtds.XHTML1_FRAMESET, encoding=self._encoding)
            elif decl.find("Transitional") > 1:
                self.doc = XHTML.new_document(dtds.XHTML1_TRANSITIONAL, encoding=self._encoding)
            else:
                self.doc = XHTML.new_document(dtds.XHTML1_TRANSITIONAL, encoding=self._encoding)
        else:
            print >>sys.stderr, "!!! Unhandled decl: %r" % (decl,)

    def handle_pi(self, data):
        'xml version="1.0" encoding="ISO-8859-1"?'
        mo = re.match('xml version="([0123456789.]+)" encoding="([A-Z0-9-]+)"', data, re.IGNORECASE)
        if mo:
            version, encoding = mo.groups()
            assert version == "1.0"
            self._encoding = encoding
            self.doc.set_encoding(encoding)
        else:
            print >>sys.stderr, "!!! Unhandled pi: %r" % (data,)


def get_document(url, data=None, encoding=POM.DEFAULT_ENCODING,
        mimetype=XHTML.MIME_XHTML, useragent=None, validate=0,
        logfile=None):
    """Fetchs a document from the given source, including remote hosts."""
    p = get_parser(validate=validate, mimetype=mimetype, logfile=logfile)
    p.parse(url, data, encoding, useragent=useragent, accept=mimetype)
    handler = p.getContentHandler()
    return handler.doc

def get_parser(document=None, namespaces=0, validate=0, mimetype=None,
        logfile=None):
    if mimetype == XHTML.MIME_HTML:
        if not document:
            document = XHTML.new_document(dtds.XHTML1_TRANSITIONAL, encoding=POM.DEFAULT_ENCODING)
        return _HTMLParser(document)
    else: # assume some kind of XML
        from pycopia.XML import POMparse
        return POMparse.get_parser(document, namespaces=namespaces, validate=validate, 
            external_ges=1, logfile=logfile, doc_factory=XHTML.xhtml_factory)


def parseString(string):
    p = get_parser()
    p.feed(string)
    p.close() 
    return p.getContentHandler().doc

def _test(argv):
    pass # XXX

if __name__ == "__main__":
    _test(sys.argv)

