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
Provides a web service interface to the Pycopia database model. Also
provides a basic database editor application.

Usually mapped to /storage/ URL. See storage.conf.example for details.

"""

import sys
import itertools

from pycopia.aid import IF
from pycopia.db import types
from pycopia.db import models
from pycopia.db import webhelpers

from pycopia.WWW import json
from pycopia.WWW import framework
from pycopia.WWW.middleware import auth

from sqlalchemy.exc import DataError, IntegrityError


_tables = set(models.class_names())



def get_tables():
    return _tables


def get_model(modelname):
    try:
        return getattr(models, modelname)
    except AttributeError:
        raise framework.HHttpErrorNotFound("No model %r found." % modelname)


def update(modelname, entry_id, data):
    klass = get_model(modelname)
    dbrow = webhelpers.get_row(klass, entry_id)
    pass # XXX


def table_get(modelname, filt, order_by=None, start=None, end=None):
    klass = get_model(modelname)
    return webhelpers.table_get(klass, filt, order_by, start, end)


def get_table_metadata(modelname):
    klass = get_model(modelname)
    return models.get_metadata(klass)


def get_choices(modelname, attribute, order_by=None):
    modelclass = get_model(modelname)
    return models.get_choices(webhelpers.dbsession, modelclass, attribute, order_by)


def deleterow(modelname, entry_id):
    klass = get_model(modelname)
    try:
        obj = webhelpers.dbsession.query(klass).get(entry_id)
        name = str(obj)
        webhelpers.dbsession.delete(obj)
        webhelpers.dbsession.commit()
    except:
        ex, val, tb = sys.exc_info()
        return (False, str(val))
    return (True, name)


# DB model serializer and checker
def _convert_instance(obj):
    values = {}
    for field in obj._sa_class_manager.keys():
        value = getattr(obj, field)
        values[field] = value
    return {"_class_": obj.__class__.__name__,
            "_str_": str(obj),
            "value":values}


def _modelchecker(obj):
    try:
        return obj.__class__.__name__ in _tables
    except AttributeError:
        return False


_exported = [get_tables, get_table_metadata, table_get, get_choices, update, deleterow]


dispatcher = json.JSONDispatcher(_exported)
dispatcher.register_encoder("models", _modelchecker, _convert_instance)
dispatcher = auth.need_authentication(webhelpers.setup_dbsession(dispatcher))



##### for server-side markup requests that provide a basic database editor. ####
####  Almost everything below this line will disappear once I get the
####  client/javascript version written.

def doc_constructor(request, **kwargs):
    doc = framework.get_acceptable_document(request)
    doc.stylesheet = request.get_url("css", name="tableedit.css")
    doc.add_javascript2head(url=request.get_url("js", name="MochiKit.js"))
    doc.add_javascript2head(url=request.get_url("js", name="proxy.js"))
    doc.add_javascript2head(url=request.get_url("js", name="db.js"))
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NM("ASIS", None, "&nbsp;"),
         NM("A", {"href": request.get_url(listall)}, "Top"), NM("ASIS", None, "&nbsp;"),
         IF(request.path.count("/") > 2, NM("A", {"href":".."}, "Up")), NM("ASIS", None, "&nbsp;"),
    ))
    nav.append(NM("P", {"class_": "title"}, "Storage Editor"))
    nav.append(NM("P", None, 
            NM("A", {"href": "/auth/logout"}, "logout")))
    doc.add_section("messages", id="messages")
    return doc



@auth.need_login
@webhelpers.setup_dbsession
def listtable(request, tablename=None):
    klass = get_model(tablename)
    resp = framework.ResponseDocument(request, doc_constructor, 
             title="Table %s" % (tablename,))
    NM = resp.nodemaker
    resp.new_para(NM("A", {"href": request.get_url(addentry, tablename=tablename)}, 
            resp.get_icon("add")))
    cycler = itertools.cycle(["row1", "row2"]) # For alternating row styles.
    tbl = resp.doc.add_table(width="100%")
    tbl.caption(tablename)
    colnames = models.get_rowdisplay(klass)
    tbl.new_headings("", *colnames)
    for dbrow in table_get(tablename, {}):
        row = tbl.new_row(id="rowid_%s" % dbrow.id, class_=cycler.next())
        col = row.new_column(
            NM("Fragments", {}, 
                NM("A", {"href": "edit/%s/" % (dbrow.id,)}, 
                    resp.get_small_icon("edit")),
                NM("A", {"href": "javascript:doDeleteRow(%r, %r);" % (tablename, dbrow.id)}, 
                    resp.get_small_icon("delete")),
            )
        )
        firstname = colnames[0]
        row.new_column(
            NM("A", {"href": request.get_url(view, tablename=tablename, rowid=dbrow.id)}, 
                    getattr(dbrow, firstname))
        )
        for colname in colnames[1:]:
            row.new_column(getattr(dbrow, colname))

    return resp.finalize()


@auth.need_login
@webhelpers.setup_dbsession
def listall(request):
    resp = framework.ResponseDocument(request, doc_constructor, 
             title="Tables")
    cycler = itertools.cycle(["row1", "row2"])
    tbl = resp.doc.add_table(width="100%")
    tbl.caption("Tables")
    tbl.new_headings("Model name")
    for tname in sorted(list(get_tables())):
        if not hasattr(getattr(models, tname), "ROW_DISPLAY"):
            continue
        row = tbl.new_row()
        setattr(row, "class_", cycler.next())
        col = row.new_column(resp.nodemaker("A", 
                {"href": request.get_url(listtable, tablename=tname)},  tname))
    return resp.finalize()


@auth.need_login
@webhelpers.setup_dbsession
def view(request, tablename=None, rowid=None):
    klass = get_model(tablename)
    dbrow = webhelpers.get_row(klass, rowid)
    resp = framework.ResponseDocument(request, doc_constructor, 
             title="Table %s %s" % (tablename, dbrow))
    NM = resp.nodemaker
    resp.new_para(
            (NM("A", {"href": request.get_url(addentry, tablename=tablename)}, 
                resp.get_icon("add")), 
            NM("A", {"href": request.get_url(edit, tablename=tablename, rowid=rowid)}, 
                resp.get_icon("edit")),
            ))
    cycler = itertools.cycle(["row1", "row2"])
    tbl = resp.doc.add_table(width="100%", class_="rowdisplay")
    tbl.caption("%s #%s" % (tablename, rowid))
    tbl.new_headings("Field", "Value")
    for metadata in sorted(models.get_metadata(klass)):
        row = tbl.new_row()
        setattr(row, "class_", cycler.next())
        row.new_column(metadata.colname)
        row.new_column(str(getattr(dbrow, metadata.colname)))
    return resp.finalize()



class CreateRequestHandler(framework.RequestHandler):

    def get(self, request, tablename=None):
        klass = get_model(tablename)
        title = "Creating new %s" % (tablename, )
        resp = framework.ResponseDocument(request, doc_constructor, title=title)
        resp.new_para(title)
        form = resp.add_form(action=request.get_url(addentry, tablename=tablename))
        webhelpers.build_add_form(form, klass)
        return resp.finalize()

    def post(self, request, tablename=None):
        klass = get_model(tablename)
        dbrow = klass()
        try:
            webhelpers.update_row(request, klass, dbrow)
        except types.ValidationError, err:
            webhelpers.dbsession.rollback()
            request.log_error("create ValidationError: %s: %s\n" % (tablename, err))
            title = "Recreate new %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            resp.new_para(err, class_="error")
            form = resp.add_form(action=request.get_url(addentry, tablename=tablename))
            webhelpers.build_add_form(form, klass)
            return resp.finalize()
        webhelpers.dbsession.add(dbrow)

        try:
            webhelpers.dbsession.commit()
        except (DataError, IntegrityError), err:
            webhelpers.dbsession.rollback()
            request.log_error("create error: %s: %s\n" % (tablename, err))
            title = "Create new %s" % (tablename, )
            resp = self.get_response(request, title=title)
            resp.new_para(title + ", again.")
            resp.new_para(err, class_="error")
            form = resp.add_form(action=request.get_url(addentry, tablename=tablename))
            webhelpers.build_add_form(form, klass)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.get_url(listtable, tablename=tablename))

addentry = auth.need_login(webhelpers.setup_dbsession(CreateRequestHandler(doc_constructor)))



class EditRequestHandler(framework.RequestHandler):
 
    def get(self, request, tablename=None, rowid=None):
        klass = get_model(tablename)
        dbrow = webhelpers.get_row(klass, rowid)
        title = "Edit %s %s" % (tablename, dbrow)
        resp = self.get_response(request, title=title)
        resp.new_para(title)
        form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
        webhelpers.build_edit_form(form, klass, dbrow)
        return resp.finalize()

    def post(self, request, tablename=None, rowid=None):
        klass = get_model(tablename)
        dbrow = webhelpers.get_row(klass, rowid)
        try:
            webhelpers.update_row(request, klass, dbrow)
        except types.ValidationError, err:
            webhelpers.dbsession.rollback()
            title = "Re-edit %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
            webhelpers.build_edit_form(form, klass, dbrow, err)
            return resp.finalize()

        try:
            webhelpers.dbsession.commit()
        except (DataError, IntegrityError), err:
            webhelpers.dbsession.rollback()
            title = "Re-edit %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
            webhelpers.build_edit_form(form, klass, dbrow, err)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.get_url(listtable, tablename=tablename))

edit = auth.need_login(webhelpers.setup_dbsession(EditRequestHandler(doc_constructor)))



if __name__ == "__main__":
    pass

