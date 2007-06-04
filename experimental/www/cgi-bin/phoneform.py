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
Produce the main answering machine interface.

"""

import sys

import XML.POM as POM
import XML.XHTML as XHTML

def main(argv):
    htd = XHTML.new_document(XHTML.STRICT)
    htd.stylesheet = "/stylesheet/phonemain.css"
    htd.title = "Answering Machine - Main Page"

    htd.add_header(1, 'Answering Machine')

    BR = htd.get_element("Br")
    A = htd.get_element("A", href="somelink.html")
    A.add_text("some link")
    p = htd.get_para()
    p.append(A)
    p.add_text(" This is ")
    b = p.bold("bold")
    p.add_text(" text. using ")
    stb = htd.get_element("B")
    stb.add_text("bold tags")
    p.text(stb)
    rp = str(p)
    htd.append(POM.ASIS(rp))
    t = htd.add_table(border=1)
    t.summary = "This is a test table."
    t.caption("table caption")
    h = t.set_heading(2, "heading col 2")
    h.set_attribute("class", "headerclass")
    t.set_heading(1, "heading col 1")
    t.set(1,1,"row 1, col 1")
    t.set(1,2,"row 2, col 1")
    t.set(2,1,"row 1, col 2")
    t.set(2,2,"row 2, col 2")

    htd.add_comment("the name attribute is required for all but submit & reset")
    f = htd.add_form(action="http://localhost:4001/cgi-bin/testing.py", method="post")

    f.add_textarea(""" XHTML POM parser. This parser populates the POM with XHTML objects, so this
HTML parser essentially translates HTML to XHTML, hopefully with good
results.""", name="mytextarea") ; f.append(BR)
    f.add_input(type="text", name="mytext", value="mytext text") ; f.append(BR)
    f.add_input(type="button", name="button1", src="button.png", value="Button") ; f.append(BR)
    f.add_input(type="submit", name="submit1", src="submit.png", value="Ok") ; f.append(BR)
    f.add_radiobuttons("radlist", ["one", "two", "three", "four"], vertical=False) ; f.append(BR)
    f.add_checkboxes("checks", ["one", "two", "three", "four"], vertical=True) ; f.append(BR)
    f.add_fileinput(name="myfile", default="/etc/hosts") ; f.append(BR)
    f.add_textinput(name="mytext", label="Enter text") ; f.append(BR)
    f.add_select(["one", "two", "three", "four"], name="myselect") ; f.append(BR)

    htd.emit(sys.stdout)

main(sys.argv)

