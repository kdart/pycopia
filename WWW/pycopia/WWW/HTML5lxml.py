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
Document generation for HTML5.

"""

BASIC = """<?xml version="1.0" encoding="UTF-8"?>
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

#import locale

#import lxml
from lxml.builder import E
from lxml import etree

#from lxml import etree
#lxml.html.html5parser




DEFAULT_LANG, DEFAULT_ENCODING = "en", "UTF-8"
MIME_XHTML5="application/xhtml+xml"



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



if __name__ == "__main__":
    from pycopia import autodebug
    doc = new_document()
    print str(doc)

