#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 2007  Keith Dart <keith@kdart.com>
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

"""Views for testing and debugging pyNMS and its web interface itself.
"""

from pycopia.nmsapps import core, _

from pycopia.WWW.framework import RequestHandler


def main(request):
  resp = core.ResponseDocument(request, title="pyNMS Selftest")
  resp.content.new_preformat(str(request))
  resp.extra.add_unordered_list(
             [
             resp.NM("A", {"href":request.get_url(testhandler)}, "testhandler"),
             resp.NM("A", {"href":request.get_url(reports, report="testplot")}, "reports"),
             ])
  return resp.finalize()

def reports(request, report):
  resp = core.ResponseDocument(request, title="pyNMS Selftest reports.")
  resp.content.new_para(str(report))
  resp.content.add_image(src=request.get_url("graphs.testplot"), alt="testplot")
  return resp.finalize()


class TestHandler(RequestHandler):
    def get(self, request):
        resp = self.get_response(request)
        resp.doc.new_para("Got the test from the get() method.")
        return resp.finalize()


testhandler = TestHandler(core.get_base_document)

