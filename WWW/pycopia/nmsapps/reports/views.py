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
        resp.extra.append(p)
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

