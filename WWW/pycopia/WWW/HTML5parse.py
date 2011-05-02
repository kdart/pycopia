#!/usr/bin/python2
# -*- coding: utf8 -*-
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
Document generation for HTML5.

"""

#import locale

#import lxml
from lxml.builder import E
from lxml import etree

#from lxml import etree
#lxml.html.html5parser




DEFAULT_LANG, DEFAULT_ENCODING = "en", "UTF-8"
MIME_XHTML5="application/xhtml+xml"

xhtml_parser = None

"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>JavaScript Playground.</title>
    <script src="program.js" type="text/javascript;version=1.8"></script>
</head>
<body>
    <pre id="work">
    </pre>
</body>
</html>
"""

class ContainerMixin(object):
    def __init__(self, encoding=DEFAULT_ENCODING, language="en"):
        self.encoding = encoding
        self.language = language


class HTML5Document(ContainerMixin):
    """HTML5Document represents the top-level document of an HTML5 document.
    """
    XMLHEADER = '<?xml version="1.0" encoding="%s"?>\n' % DEFAULT_ENCODING
    MIMETYPE=MIME_XHTML5
    DOCTYPE = '<!DOCTYPE html>\n'

    def initialize(self):
        head = E("head")
        body = E("body")
        self.root = E("html", head, body, lang=self.language, xmlns="http://www.w3.org/1999/xhtml")
        self.head = head
        self.body = body
        meta = E("meta", content=self.MIMETYPE, charset=self.encoding)
        meta.attrib["http-equiv"] = "Content-Type"
        self.head.append(meta)


    def set_encoding(self, encoding):
        self.XMLHEADER = '<?xml version="1.0" encoding="%s"?>\n' % (encoding,)
        self.encoding = encoding

    def __str__(self):
        return self.encode(self.encoding, True)

    def encode(self, encoding=DEFAULT_ENCODING, pretty=False):
        if encoding != self.encoding:
            self.set_encoding(encoding)
        return self.XMLHEADER + self.DOCTYPE + etree.tostring(self.root, 
                        pretty_print=pretty, encoding=self.encoding)

    def emit(self, fo, encoding=DEFAULT_ENCODING):
        if encoding != self.encoding:
            self.set_encoding(encoding)
        fo.write(self.XMLHEADER)
        fo.write(self.DOCTYPE)
        self.root.emit(fo, encoding)
        fo.write("\n")


def new_document(mimetype=None, encoding=DEFAULT_ENCODING, language=DEFAULT_LANG):
    doc = HTML5Document(encoding, language)
    doc.initialize()
    return doc


def get_document(url, data=None, encoding=DEFAULT_ENCODING,
        mimetype=MIME_XHTML5, useragent=None, logfile=None):
    """Fetches a document from the given source, including remote hosts."""


def get_parser(document=None, namespaces=0, strict=False, mimetype=None, logfile=None):
    global xhtml_parser

    if xhtml_parser is None:
        from html5lib import XHTMLParser as _XHTMLParser
        from lxml.html._html5builder import TreeBuilder

        class XHTMLParser(_XHTMLParser):
            """An html5lib XHTML Parser with lxml as tree."""

            def __init__(self, strict=strict):
                _XHTMLParser.__init__(self, strict=strict, tree=TreeBuilder)

        xhtml_parser = XHTMLParser()
    return xhtml_parser


def parseString(string):
    raise NotImplementedError
    #return doc


def parse(filename_url_or_file, parser=None, encoding=None, useragent=None, accept=None):
    """Parse a filename, URL, or file-like object into an HTML document
    tree.  Note: this returns a tree, not an element.  Use
    ``parse(...).getroot()`` to get the document root.
    """
    if parser is None:
        parser = get_parser()
    if isinstance(filename_url_or_file, basestring):
        from pycopia.WWW import urllibplus
        fp = urllibplus.urlopen(filename_url_or_file, encoding=encoding, useragent=useragent, accept=accept)
    else:
        fp = filename_url_or_file
    return parser.parse(fp, useChardet=True)


if __name__ == "__main__":
    from pycopia import autodebug
    doc = new_document()
    print str(doc)

