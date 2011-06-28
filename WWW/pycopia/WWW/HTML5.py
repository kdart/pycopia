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
Document generation for HTML5. This is kind of a quick and dirty hack on top of
the XHTML module. HTML5 does not have a DTD, so I use the existing XHTML
transitional DTD for now. 
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia.XML import POM
from pycopia.WWW import XHTML

from pycopia.dtds import html5 as DTD


DEFAULT_LANG, DEFAULT_ENCODING = b"en", b"UTF-8" # its the only one I know...
MIME_XHTML5="application/xhtml+xml" # use XML serialization since this uses the XHTML generator
DOCTYPE = b'<!DOCTYPE html>'

# Currenty using this subset of HTML5 features shared by both FF 3.6.x and Chrome 10
BROWSER_FEATURES = ['applicationcache', 'backgroundsize', 'borderimage', 'borderradius',
        'boxshadow', 'canvas', 'canvastext', 'csscolumns', 'cssgradients',
        'csstransforms', 'draganddrop', 'flexbox', 'fontface', 'geolocation',
        'hashchange', 'hsla', 'js', 'localstorage', 'multiplebgs', 'opacity',
        'postmessage', 'rgba', 'sessionstorage', 'svg', 'svgclippaths', 'textshadow',
        'webworkers']

NO_BROWSER_FEATURES = ['no-audio', 'no-cssanimations', 'no-cssreflections',
        'no-csstransforms3d', 'no-csstransitions', 'no-history', 'no-indexeddb',
        'no-inlinesvg', 'no-smil', 'no-touch', 'no-video', 'no-webgl', 'no-websockets',
        'no-websqldatabase']

FEATURE_CLASS = b" ".join(BROWSER_FEATURES) + b" " + b" ".join(NO_BROWSER_FEATURES)


class HTML5Document(XHTML.XHTMLDocument):
    XMLHEADER = b'<?xml version="1.0" encoding="%s"?>\n' % DEFAULT_ENCODING
    MIMETYPE=MIME_XHTML5

    def set_doctype(self, doctype):
        self.DOCTYPE = doctype.encode("ascii") + "\n"
        self.set_dtd(DTD)

    def initialize(self):
        dtd = self.dtd
        root = XHTML.get_container(dtd, "Html", {"class_": FEATURE_CLASS})
        self.set_root(root)
        head = XHTML.get_container(dtd, "Head", {})
        body = XHTML.get_container(dtd, "Body", {})
        head.append(dtd.Meta(charset="utf-8"))
        head.append(dtd.Meta(http_equiv="X-UA-Compatible", content="IE=edge,chrome=1"))
        root.append(head)
        root.append(body)
        root.head = head
        root.body = body



def new_document(encoding=DEFAULT_ENCODING, language=DEFAULT_LANG):
    doc = HTML5Document(doctype=DOCTYPE, encoding=encoding, lang=language)
    doc.initialize()
    doc.root.lang = language
    return doc


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    doc = new_document()
    writer = POM.BeautifulWriter(sys.stdout, XHTML.INLINE)
    doc.emit(writer)

