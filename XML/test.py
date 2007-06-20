#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
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


"""

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

    def test_2POMString(self):
        print repr(POM.POMString(u'This is a test.'))
        print repr(POM.POMString(u'This is a test.', 'utf-8'))
        print repr(POM.POMString('This is a test.', 'utf-8'))

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
        print doctype
        self.assertEqual(doctype.name.lower(), "html")

    def test_4modfile(self):
         pythonfile, doctype = pycopia.dtds.get_mod_file("/var/tmp/dtds", "sample.dtd")
         self.assertEqual(pythonfile, "/var/tmp/dtds/sample.py")
         self.assertEqual(doctype, None)

    def test_4modfilewithdoctype(self):
         pythonfile, doctype = pycopia.dtds.get_mod_file("/var/tmp/dtds", "xhtml11.dtd")
         self.assertEqual(pythonfile, "/var/tmp/dtds/xhtml11.py")
         self.assert_(pycopia.dtds.DOCTYPES[pycopia.dtds.XHTML] is doctype)

    def test_5POMvalidation(self):
        import pomtest # previous test just created this.
        doc = POM.POMDocument(dtd=pomtest)
        doc.set_root(pomtest.Toplevel())
        self.assertRaises(POM.ValidationError, str, doc)

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
