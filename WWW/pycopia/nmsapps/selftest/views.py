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

