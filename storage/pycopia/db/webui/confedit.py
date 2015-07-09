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
Browser based config table editor, server side.

"""

#import sys
#import itertools

from pycopia.db import config
from pycopia.db import webhelpers

from pycopia.WWW import framework
from pycopia.WWW import HTML5
from pycopia.WWW import json
from pycopia.WWW.middleware import auth



def config_page_constructor(request, **kwargs):
    doc = HTML5.new_document()
    res = request.resolver
    doc.stylesheet = res.get_url("css", name="tableedit.css")
    doc.scripts = ["MochiKit.js", "proxy.js", "ui.js", "db.js", "config.js"]
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
    doc.add_section("container", id="content")
    doc.add_section("container", id="sidebar")
    doc.add_section("container", id="messages")
    return doc


@auth.need_login
@webhelpers.setup_dbsession
def config_main(request):
    resp = framework.ResponseDocument(request, config_page_constructor, title="Config Editor")
    return resp.finalize()


def config_update(xxx):
    pass


_exported = [config_update]

dispatcher = auth.need_authentication(
        webhelpers.setup_dbsession(
            json.JSONDispatcher(_exported)))


if __name__ == "__main__":
    pass
