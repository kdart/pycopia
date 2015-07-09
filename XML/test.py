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

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import unittest

from pycopia.XML import POM
from pycopia.XML import DTD
from pycopia.XML import Plaintext

import pycopia.dtds
import pycopia.dtds.pomtest

class XMLTests(unittest.TestCase):

    def test_1CommentEncoding(self):
        cmt =  POM.Comment("some ------- comment-")
        self.assert_(str(cmt) == '<!-- some - - - - comment- -->')

    def test_3DTD(self):
        dtdp = DTD.get_dtd_compiler(sys.stdout)
        dtdp.parse_resource("etc/dtd/pomtest.dtd")

    def test_4DTDcompile(self):
        fo = open("pomtest.py", "w")
        try:
            dtdp = DTD.get_dtd_compiler(fo)
            dtdp.parse_resource("etc/dtd/pomtest.dtd")
        finally:
            fo.close()

    def test_4doctypefetch(self):
        doctype = pycopia.dtds.get_doctype(pycopia.dtds.XHTML)
        print(doctype)
        self.assertEqual(doctype.name.lower(), "html")

    def test_4modfile(self):
         pythonfile, doctype = pycopia.dtds.get_mod_file("/var/tmp/dtds", "sample.dtd")
         self.assertEqual(pythonfile, "/var/tmp/dtds/sample.py")
         self.assertEqual(doctype, None)

    def test_4modfilewithdoctype(self):
         pythonfile, doctype = pycopia.dtds.get_mod_file("/var/tmp/dtds", "xhtml11.dtd")
         self.assertEqual(pythonfile, "/var/tmp/dtds/xhtml11.py")
         self.assert_(pycopia.dtds.DOCTYPES[pycopia.dtds.XHTML] is doctype)

    def test_6POMemit(self):
        import pomtest
        doc = POM.POMDocument(dtd=pomtest)
        doc.set_root(pomtest.Toplevel())
        doc.root.idval = "someid" # satisfy #REQUIRED attribute
        doc.emit(sys.stdout)

    def test_negdocencoding(self):
        import pomtest
        doc = POM.POMDocument(dtd=pomtest)
        self.assertRaises(ValueError, doc.set_encoding, "xxx")

    def test_docencoding(self):
        import pomtest
        doc = POM.POMDocument(dtd=pomtest)
        doc.set_encoding("iso-8859-1")
        self.assertEqual(doc.encoding, "iso-8859-1")

#   import dtds.xhtml1_strict
#   doc = POMDocument(dtds.xhtml1_strict)
#   doc.set_root(doc.get_elementnode("html")())
#   print doc



if __name__ == '__main__':
    unittest.main()
