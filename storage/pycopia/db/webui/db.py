#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
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
Basic database editor, server side.
"""

from pycopia.WWW import framework
from pycopia.WWW import HTML5
from pycopia.WWW.middleware import auth

CHARSET = "utf-8"

def dbedit_page_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheets = ["common.css", "ui.css", "db.css"]
    doc.scripts = [ "MochiKit.js", "proxy.js", "ui.js", "db.js", "dbedit.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    add_nav_section(doc, kwargs)
    container = doc.add_section("container", id="container")
    content = container.add_section("container", id="content")
    messages = container.add_section("container", id="messages")
    sidebar = container.add_section("container", id="sidebar")
    return doc


def metadata_page_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheets = ["common.css", "ui.css", "db.css"]
    doc.scripts = [ "MochiKit.js", "proxy.js", "ui.js", "db.js", "dbmetaapp.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    add_nav_section(doc, kwargs)
    container = doc.add_section("container")
    wrapper = container.add_section("container", id="wrapper")
    content = wrapper.add_section("container", id="content")
    sidebar = container.add_section("container", id="sidebar")
    return doc

def add_nav_section(doc, kwargs):
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    NBSP = NM("_", None)
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NBSP,
         NM("A", {"href":".."}, "Up"), NBSP,
    ))
    nav.append(NM("P", {"class_": "title"}, kwargs["title"]))
    nav.append(NM("P", None, NM("A", {"href": "/auth/logout"}, "logout")))


@auth.need_login
def main(request):
    resp = framework.ResponseDocument(request, dbedit_page_constructor, title="Database Editor")
    return resp.finalize()


@auth.need_login
def metadata(request):
    resp = framework.ResponseDocument(request, metadata_page_constructor, title="Metadata Viewer")
    return resp.finalize()

