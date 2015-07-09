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
Objects for RSS.

"""

import sys
import re

from pycopia.aid import newclass
from pycopia.XML import POM
from pycopia import dtds

from htmlentitydefs import name2codepoint


class RSSMixin(object):
    pass


class RSSDocument(POM.POMDocument, RSSMixin):
    pass


def new_document(doctype=dtds.RSS2, encoding=POM.DEFAULT_ENCODING):
    doc = RSSDocument(doctype=doctype)
    doc.set_encoding(encoding)
    return doc


def get_parser(document=None, namespaces=1, validate=0, external_ges=1,
        logfile=None, doc_factory=new_document):
    import xml
    if hasattr(xml, "use_pyxml"):
        xml.use_pyxml()
    import xml.sax.sax2exts
    import xml.sax.handler
    handler = POM.ContentHandler(document, doc_factory=doc_factory, logfile=logfile)
    errorhandler = POM.ErrorHandler(logfile)
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
    return parser


def parseString(string, encoding=POM.DEFAULT_ENCODING):
    doc = new_document(encoding=encoding)
    p = get_parser(doc)
    p.feed(string)
    p.close()
    return p.getContentHandler().doc


if __name__ == "__main__":
    from pycopia import autodebug
    body = open("/home/keith/gmapi_response_sample.xml").read()
    doc = parseString(body)
    print doc
    print doc.root[1][1]._namespace

