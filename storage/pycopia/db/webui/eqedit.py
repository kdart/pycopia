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
Equpment editor loader.
This is the server-side component for the eqedit.js browser application.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia.WWW import framework
from pycopia.WWW import HTML5
from pycopia.WWW import json
from pycopia.WWW.middleware import auth

from pycopia.db import webhelpers
from pycopia.db import models



def eqedit_constructor(request, **kwargs):
    doc = HTML5.new_document()
    for name, val in kwargs.items():
        setattr(doc, name, val)
    doc.title = "Equipment Editor"
    doc.stylesheet = "/media/css/eqedit.css"
    doc.scripts = ["MochiKit.js", "proxy.js", "ui.js", "db.js", "sorttable.js", "eqedit.js"]
    tools = doc.add_section("container", id="tools")
    frm = tools.add_form(name="searchform", onsubmit="return equipmentSearch();")
    frm.add_input(type="text", name="filt_name")
    frm.add_input(type="button", name="search")
    doc.add_section("container", id="eqlist")
    doc.add_section("container", class_="invisible", id="eqform")
    return doc


@auth.need_login
def main(request):
    resp = framework.ResponseDocument(request, eqedit_constructor)
    return resp.finalize()


def get_equipment_list(filt=None, start=0, end=20, order_by=None):
    modelclass = models.Equipment
    if columns is None:
        q = dbsession.query(modelclass)
    else:
        attrlist = [getattr(modelclass, n) for n in columns]
        q = dbsession.query(*attrlist)
    # build filter if one is provided as a dictionary
    if filt is not None:
        for name, value in filt.items():
            attrib = getattr(modelclass, name)
            q = q.filter(attrib==value)
    if order_by:
        q = q.order_by(getattr(modelclass, order_by))

    if end is not None:
        if start is not None:
            q = q.slice(start, end)
        else:
            q = q.limit(end)
    return q.all()


dispatcher = json.JSONDispatcher([get_equipment_list])
dispatcher = auth.need_authentication(webhelpers.setup_dbsession(dispatcher))

