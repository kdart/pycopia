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

