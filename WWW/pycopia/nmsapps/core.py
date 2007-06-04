#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 2007  Keith Dart <keith@dartworks.biz>
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



from pycopia.WWW import XHTML, framework

JSKIT = "MochiKit.js"
UILIB = "nms.js"
DEFAULTSTYLE = "default.css"


def get_base_document(request, **kwargs):
    doc = XHTML.new_document()
    ss = kwargs.pop("stylesheet", DEFAULTSTYLE)
    js = kwargs.pop("javascriptlink", None)
    for name, val in kwargs.items():
        setattr(doc, name, val)
    doc.stylesheet = request.get_url("css", name=ss)
    doc.javascriptlink = request.get_url("js", name=JSKIT)
    doc.javascriptlink = request.get_url("js", name=UILIB)
    if js:
        doc.javascriptlink = request.get_url("js", name=js)
    container = doc.add_section("container")
    header = container.add_section("container", id="header")
    wrapper = container.add_section("container", id="wrapper")
    content = wrapper.add_section("container", id="content")
    navigation = container.add_section("container", id="navigation")
    extra = container.add_section("container", id="extra")
    footer = container.add_section("container", id="footer")
    doc.header = header
    doc.content = content
    doc.nav = navigation
    doc.extra = extra
    doc.footer = footer
    return doc


class ResponseDocument(framework.ResponseDocument):
    def __init__(self, request, **kwargs):
        return super(ResponseDocument, self).__init__(request, 
                                          get_base_document, **kwargs)

    def get_nav(self, navitems):
        gurl = self.get_url
        ul = self._doc.get_unordered_list()
        for loc, txt in navitems:
            a = ul.get_anchor(href=gurl(loc))
            a.add_text(txt)
            ul.add_item(a)
        return ul

    def fill_nav(self, navitems):
        navs = self.get_object(id(navitems), self.get_nav, navitems=navitems)
        self._doc.nav.append(navs)


