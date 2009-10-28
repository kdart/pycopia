#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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
Web interface for QA reports and tools.

"""

import itertools

from pycopia.WWW import framework
from pycopia.WWW.middleware import auth

from pycopia.db import models

### test result reports 

def testresult_constructor(request, **kwargs):
    doc = framework.get_acceptable_document(request)
    doc.stylesheet = request.get_url("css", name="qawebui.css")
#    doc.add_javascript2head(url=request.get_url("js", name="MochiKit.js"))
#    doc.add_javascript2head(url=request.get_url("js", name="proxy.js"))
#    doc.add_javascript2head(url=request.get_url("js", name="db.js"))
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    #doc.add_section("content")
    NM = doc.nodemaker
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"),
    ))
    nav.append(NM("P", {"class_": "title"}, "Test Automation Interface"))
    nav.append(NM("P", None, 
            NM("A", {"href": "/auth/logout"}, "logout")))
    #doc.add_section("messages", id="messages")
    return doc


class TestResultHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)

        TR = models.TestResult
        cycler = itertools.cycle(["row1", "row2"])
        tbl = resp.doc.add_table(width="100%")
        tbl.caption("Test Runs")
        tbl.new_headings("Runner", "Result", "Results Location")

        for res in TR.get_latest_results(request.dbsession):
            row = tbl.new_row()
            setattr(row, "class_", cycler.next())
            row.new_column(str(res))
            row.new_column(res.result)
            row.new_column(resp.nodemaker("A", 
                    {"href": res.resultslocation},  "Results location"))
        return resp.finalize()


#    def post(self, request, tablename=None, rowid=None):
#        pass

testresults = auth.need_login(TestResultHandler(testresult_constructor))


class MainHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        NM = resp.doc.nodemaker
        resp.new_para("QA main page.") # XXX
        resp.doc.append(NM("P", None,
         NM("A", {"href": request.get_url(testresults)}, "Latest test results."),
        ))
        return resp.finalize()

main = auth.need_login(MainHandler(testresult_constructor))


if __name__ == "__main__":
    pass
