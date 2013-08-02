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
Supply server-side components of the countryset editor. A country set is
an arbitrary set of countries selected from a list.

This also serves as an example of dynamic web applications using the
Pycopia framework.

"""


from pycopia.WWW import framework
from pycopia.WWW import HTML5
from pycopia.WWW.middleware import auth


def cs_page_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheets = ["common.css", "ui.css", "db.css"]
    doc.scripts = ["MochiKit.js", "proxy.js", "ui.js", "db.js", "countryset.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    NBSP = NM("_", None)
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NBSP,
         NM("A", {"href":".."}, "Up"), NBSP,
    ))
    nav.append(NM("P", {"class_": "title"}, kwargs["title"]))
    nav.append(NM("P", None, NM("A", {"href": "/auth/logout"}, "logout")))
    content = doc.add_section("container", id="content")
    messages = doc.add_section("container", id="messages")
    return doc


@auth.need_login
def main(request):
    resp = framework.ResponseDocument(request, cs_page_constructor, title="Countryset Editor")
    return resp.finalize()


