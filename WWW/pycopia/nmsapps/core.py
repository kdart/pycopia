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


from pycopia.WWW import XHTML, framework

JSKIT = "mochikit/MochiKit.js"
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


