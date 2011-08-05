#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Generate and parse SVG files.

#         PUBLIC "-//W3C//DTD SVG 1.1//EN"
#         SYSTEM "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"
"""


from pycopia import dtds
from pycopia.dtds import svg11_flat_20030114

from pycopia.XML import POM


MIME_SVG = "image/svg+xml"


class SVGMixin(object):
    pass


class SVGDocument(POM.POMDocument, SVGMixin):
    MIMETYPE = MIME_SVG


def new_document():
    return SVGDocument(svg11_flat_20030114, dtds.SVG)



def get_parser(document=None):
    from pycopia.XML import POMparse
    if not document:
        document = new_document()
    return POMparse.get_parser(document, namespaces=0, validate=0, external_ges=1)


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    fname = sys.argv[1]
    string = open(fname).read()
    parser = get_parser()
    parser.feed(string)
    parser.close() 
    doc = parser.getContentHandler().doc
    print doc
    print repr(doc.root)

