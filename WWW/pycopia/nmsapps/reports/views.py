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

from pycopia.nmsapps import core, _

TITLE = _("Reports")

def main(request):
    if request.method == "GET":
        resp = core.ResponseDocument(request, title=TITLE,
                                    javascriptlink="reports.js")
        resp.fill_nav(resp.config.DEFAULTNAV)
        resp.header.add_header(1, TITLE)
        p = resp.NM("P", None, 
              resp.NM("A", {"href":resp.get_url(reports, report="sample")}, 
                 _("Sample Report")))
        resp.sidebar.append(p)
        return resp.finalize()
    else:
        return core.ONLY_GET


def reports(request, report):
    if request.method == "GET":
        resp = core.ResponseDocument(request, title="Report for %s." % (report,))
        resp.content.new_para("Stay tuned...")
        return resp.finalize()
    else:
        return core.ONLY_GET

