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
Browser based config table editor, server side.

"""

#import sys
#import itertools

from pycopia.db import config
from pycopia.db import webhelpers

from pycopia.WWW import framework
from pycopia.WWW.middleware import auth

from sqlalchemy.exc import DataError, IntegrityError


def config_page_constructor(request, **kwargs):
    doc = framework.get_acceptable_document(request)
    doc.stylesheet = request.get_url("css", name="tableedit.css")
    doc.add_javascript2head(url=request.get_url("js", name="MochiKit.js"))
    doc.add_javascript2head(url=request.get_url("js", name="proxy.js"))
    #doc.add_javascript2head(url=request.get_url("js", name="ui.js"))
    doc.add_javascript2head(url=request.get_url("js", name="db.js"))
    doc.add_javascript2head(url=request.get_url("js", name="confedit.js"))
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    NBSP = NM("ASIS", None, "&nbsp;")
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NBSP,
    ))
    nav.append(NM("P", {"class_": "title"}, "Config Editor"))
    nav.append(NM("P", None, NM("A", {"href": "/auth/logout"}, "logout")))
    doc.add_section("messages", id="messages")
    return doc


@auth.need_login
@webhelpers.setup_dbsession
def config_main(request):
    resp = framework.ResponseDocument(request, config_page_constructor, 
             title="Config Editor")
    return resp.finalize()


@auth.need_login
@webhelpers.setup_dbsession
def config_update(request):
    pass


if __name__ == "__main__":
    pass
