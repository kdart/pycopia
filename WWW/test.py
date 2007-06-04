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
import webbrowser

from pycopia.aid import Enums, NULL
from pycopia.XML import POM
from pycopia import dtds

from pycopia.WWW import fcgiserver
from pycopia.WWW import framework
from pycopia.WWW import XHTML
from pycopia.WWW import rss
from pycopia.WWW import rst
from pycopia.WWW import serverconfig
from pycopia.WWW import urllibplus
from pycopia.WWW import useragents


XHTMLFILENAME = "/tmp/testXHTML.html"

MOBILEAGENT1 = "Nokia6680/1.0 ((4.04.07) SymbianOS/8.0 Series60/2.6 Profile/MIDP-2.0 Configuration/CLDC-1.1)"
MOBILEAGENT2 = 'MOT-V3/0E.41.C3R MIB/2.2.1 Profile/MIDP-2.0 Configuration/CLDC-1.0 UP.Link/6.3.1.17.06.3.1.17.0'
WML = "text/wml, text/vnd.wap.wml"

class WWWTests(unittest.TestCase):

    def test_lighttpdconfig(self):
        t = serverconfig.LighttpdConfig()
        t.add_vhost("www.pycopia.net", ["nmsapps"])
        t.add_vhost("www.pycopia.org", ["nmsapps", "webtools"])
        t.emit(sys.stdout)

    def test_XHTML(self):
        """Construct an XHTML page. Verify visually."""
        htd = XHTML.new_document(dtds.XHTML1_STRICT)
        htd.title = "This is the title."
        htd.add_header(1, 'Main document & "stuff"')
        htd.new_para("This is a test. This is text.")
        htd.add_unordered_list(["List line one.", "list line two."])
        BR = htd.get_new_element("Br")
        A = htd.get_new_element("A", href="somelink.html")
        A.add_text("some link")
        p = htd.get_para()
        p.append(A)
        p.add_text(" This is ")
        b = p.bold("bold")
        p.add_text(" text. using ")
        stb = htd.get_new_element("B")
        stb.add_text("bold tags")
        p.text(stb)
        rp = str(p)
        htd.append(POM.ASIS(rp))
        # table methods
        t = htd.add_table(border=1)
        t.summary = "This is a test table."
        t.caption("table caption")
        h = t.set_heading(2, "heading col 2")
        h.set_attribute("class", "headerclass")
        t.set_heading(1, "heading col 1")
        t.set_cell(1,1,"row 1, col 1")
        t.set_cell(1,2,"row 2, col 1")
        t.set_cell(2,1,"row 1, col 2")
        t.set_cell(2,2,"row 2, col 2")
        # sections
        div = htd.get_section("section1")
        div.add_header(1, "Div heading.")
        div.new_para("First div para.")
        htd.append(div)
        div2 = div.get_section("section2")
        div2.new_para("Second div para")
        div.append(div2)

        dl = div.add_definition_list()
        dl.add_definitions({"def1":"The definition of 1", 
                        "def2": "The definition of 2"})

        # using the nodemaker object
        NM = htd.nodemaker
        ul = NM("Ul", None, 
                NM("Li", None, "line 1"), 
                NM("Li", None, "line 2")
                )
        htd.append(ul)
        # using the creator object.
        creator = htd.creator
        parts = creator([("Just", "just/"), "How will this turn out?", ["It is hard to tell.", "Well, not too hard."]])

        htd.add_comment("the name attribute is required for all but submit & reset")
        htd.append(parts)
        f = htd.add_form(action="http://localhost:4001/cgi-bin/testing.py", method="post")

        f.add_textarea("mytextarea", """Default text in the textarea.""") ; f.append(BR)
        f.add_input(type="text", name="mytext", value="mytext text") ; f.append(BR)
        f.add_input(type="button", name="button1", src="button.png", value="Button") ; f.append(BR)
        f.add_input(type="submit", name="submit1", src="submit.png", value="Ok") ; f.append(BR)
        f.add_radiobuttons("radlist", ["one", "two", "three", "four"], vertical=False) ; f.append(BR)
        f.add_checkboxes("checks", ["one", "two", "three", "four"], vertical=True) ; f.append(BR)
        f.add_fileinput(name="myfile", default="/etc/hosts") ; f.append(BR)
        f.add_textinput(name="mytext", label="Enter text") ; f.append(BR)
        f.yes_no("What's it gonna be?")
        f.add_select(["one", "two", ("three", True), "four", 
                       {"agroup": ["group1", "group2"]}], 
                       name="myselect") ; f.append(BR)

        f.add_select({"Group1": Enums("g1one", "g1two", "g1three")+[("g1four", True)],
                      "Group2": Enums("g2one", "g2two", "g2three"),
                      "Group3": Enums("g3one", "g3two", "g3three"),
                    }, name="useenums") ; f.append(BR)

        f.add_select(["mone", "mtwo", ("mthree", True), ("mfour", True)], name="multiselect", multiple=True) ; f.append(BR)

        set = f.add_fieldset("afieldset")
        set.add_textinput(name="settext", label="Enter set text")
        set.add_textinput(name="settext2", label="Enter set text 2", default="Default text.")
        set.append(BR)
        tbl = htd.new_table([1,2,3,4,5], 
                            [NULL, NULL, NULL], 
                            ["col1", "col2", "col3"], width="100%", summary="autogenerated")

        # object 
        subdoc = XHTML.new_document(dtds.XHTML)
        parts = subdoc.creator(("Add a document object.", ["Some data.", "some more data.."]))
        subdoc.append(parts)
        sdfo = open("/tmp/subdoc.html", "w")
        subdoc.emit(sdfo)
        sdfo.close()
        htd.add_object(data="subdoc.html", type=subdoc.MIMETYPE,
                                    width="400px", height="600px")
        htd.emit(sys.stdout)
        print "-----"
        fo = open(XHTMLFILENAME, "w")
        bw = POM.BeautifulWriter(fo, XHTML.INLINE)
        htd.emit(bw)
        fo.close()
        print "----- Form values:"
        print f.fetch_form_values()
        print "----- Form elements:"
        felems = f.fetch_form_elements()
        for name, elemlist in felems.items():
            print repr(name), ": ", repr(elemlist)
            print
        # visually verify the page.
        webbrowser.open("file://%s" % (XHTMLFILENAME,))

    def test_requesthandler(self):
        class MyHandler(framework.RequestHandler):
            def get(self, request):
                pass
        h = MyHandler(framework.default_doc_constructor)
        print h._implemented

    def test_urlmap(self):
        def F(r):
            pass
        m = framework.URLMap(r'^/selftest/(?P<patt1>\S+)/(?P<patt2>\d+)/$', F)
        path = m.get_url(patt1="part1", patt2="22")
        print m
        print path
        self.assertEqual(path, "/selftest/part1/22/")
        self.assertTrue( m.match(path))

    def test_Zfetch(self):
        doc = XHTML.get_document("http://www.pycopia.net/")
        self.assertEqual(doc.title.get_text(), "Python Application Frameworks")
        # write it out for inspection
        # Note that the document was parsed, and regenerated.
        fo = open("/tmp/pycopia_net.html", "w")
        try:
            doc.emit(fo)
        finally:
            fo.close()
        print "Fetched document found here: /tmp/pycopia_net.html"

    def test_Zfetchmobile(self):
        doc = XHTML.get_document(
        "http://www.google.com/gwt/n?u=http://www.pynms.net",
        mimetype=WML,
        useragent=MOBILEAGENT2)
        print "Mobile doctype:", doc.DOCTYPE
        # write it out for inspection
        # Note that the document was parsed, and regenerated.
        fo = open("/tmp/test_WWW_mobile.html", "w")
        try:
            doc.emit(fo)
        finally:
            fo.close()
        print "Fetched document found here: /tmp/test_WWW_mobile.html"

    # fetches a chinese, transcoded WML page.
    def test_Zfetchwml(self):
        doc = XHTML.get_document(
        "http://www.google.cn/gwt/n?mrestrict=wml&site=search&q=NBA&source=m&output=wml&hl=zh-CN&ei=b99bRpDLAZzOogK1_Pwq&ct=res&cd=0&rd=1&u=http%3A%2F%2Fchina.nba.com%2F",
        mimetype=WML,
        useragent=MOBILEAGENT2)
        print "WML doctype:", doc.DOCTYPE
        self.assert_(type(doc) is XHTML.WMLDocument)
        # write it out for inspection
        # Note that the document was parsed, and regenerated.
        fo = open("/tmp/test_WWW_wml.html", "w")
        try:
            doc.emit(fo)
        finally:
            fo.close()
        print "Fetched document found here: /tmp/test_WWW_wml.html"


    def test_rst(text):
        renderer = rst.Renderer()
        text = """
Heading
=======

Some Text.
    """
        print renderer.render(text)



if __name__ == '__main__':
    unittest.main()
