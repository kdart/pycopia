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

