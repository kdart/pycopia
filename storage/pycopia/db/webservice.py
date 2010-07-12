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
import logging

from pycopia.aid import IF
from pycopia.db import types
from pycopia.db import models
from pycopia.db import webhelpers

#from pycopia.dictlib import AttrDict
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


def get_uidata():
    cf = json.current_request.config
    return {"ICONMAP": cf.ICONMAP, 
            "ICONMAP_SMALL": cf.ICONMAP_SMALL}


def get_table_metadata(modelname):
    klass = get_model(modelname)
    return models.get_metadata(klass)


def get_table_metadata_map(modelname):
    klass = get_model(modelname)
    return models.get_metadata_map(klass)


def updaterow(modelname, entry_id, data):
    klass = get_model(modelname)
    dbrow = webhelpers.get_row(klass, entry_id)
    try:
        webhelpers.update_row(data, klass, dbrow)
    except types.ValidationError, err:
        webhelpers.dbsession.rollback()
        logging.error(err)
        return False
    try:
        webhelpers.dbsession.commit()
    except (DataError, IntegrityError), err:
        webhelpers.dbsession.rollback()
        logging.error(err)
        return False
    return True


def get_row(modelname, entry_id):
    klass = get_model(modelname)
    return webhelpers.get_row(klass, entry_id)


def get_ids(modelname, idlist):
    klass = get_model(modelname)
    return webhelpers.get_ids(klass, idlist)


def query(modelname, filt, order_by=None, start=None, end=None):
    klass = get_model(modelname)
    return webhelpers.query(klass, filt, order_by, start, end)


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


def create(modelname, data):
    """Create a new row in a table.

    Returns the new items primary key values.
    """
    klass = get_model(modelname)
    dbrow = klass()
    try:
        webhelpers.update_row(data, klass, dbrow)
    except types.ValidationError, err:
        webhelpers.dbsession.rollback()
        raise
    webhelpers.dbsession.add(dbrow)
    try:
        webhelpers.dbsession.commit()
    except (DataError, IntegrityError), err:
        webhelpers.dbsession.rollback()
        raise
    mapper = models.class_mapper(klass)
    return [getattr(dbrow, col.name) for col in mapper.primary_key]


def related_add(modelname, entry_id, colname, relmodelname, rel_id):
    klass = get_model(modelname)
    relklass = get_model(relmodelname)
    metadata = models.get_column_metadata(klass, colname)
    # fetch parent and related objects
    dbrow = webhelpers.get_row(klass, entry_id)
    reldbrow = webhelpers.get_row(relklass, rel_id)
    # now add using appropriate semantics
    if metadata.uselist:
        col = getattr(dbrow, colname)
        col.append(reldbrow)
    else:
        setattr(dbrow, colname, reldbrow)
    try:
        webhelpers.dbsession.commit()
    except (DataError, IntegrityError), err:
        webhelpers.dbsession.rollback()
        raise
    return True


def related_remove(modelname, entry_id, colname, relmodelname, rel_id):
    klass = get_model(modelname)
    relklass = get_model(relmodelname)
    metadata = models.get_column_metadata(klass, colname)
    # fetch parent and related objects
    dbrow = webhelpers.get_row(klass, entry_id)
    if metadata.uselist:
        reldbrow = webhelpers.get_row(relklass, rel_id)
        col = getattr(dbrow, colname)
        col.remove(reldbrow)
    else:
        if metadata.nullable:
            setattr(dbrow, colname, None)
        else:
            raise DataError("Removing non-nullable relation")
    try:
        webhelpers.dbsession.commit()
    except (DataError, IntegrityError), err:
        webhelpers.dbsession.rollback()
        raise
    return True


# DB model serializer and checker - returns a structure representing a
# model row instance.  Relation objects will also be recursivly encoded.
def _convert_instance(obj, depth=0):
    values = {"id": obj.id}
    for metadata in models.get_metadata_iterator(obj.__class__):
        if metadata.coltype == "RelationProperty":
            value = getattr(obj, metadata.colname)
            if value is not None:
                if depth < 3:
                    if metadata.uselist:
                        values[metadata.colname] = [_convert_instance(o, depth+1) for o in value]
                    else:
                        values[metadata.colname] = _convert_instance(value, depth+1)
                else:
                    if metadata.uselist:
                        values[metadata.colname] = [str(o) for o in value]
                    else:
                        values[metadata.colname] = str(value)
            else:
                values[metadata.colname] = value
        else:
            values[metadata.colname] = getattr(obj, metadata.colname)
    return {"_class_": obj.__class__.__name__,
            "_str_": str(obj),
            "value":values}


def _modelchecker(obj):
    try:
        return obj.__class__.__name__ in _tables
    except AttributeError:
        return False

# Functions exported to javascript via proxy.
_exported = [get_tables, get_table_metadata, get_table_metadata_map, get_choices, get_uidata,
        query, create, updaterow, deleterow, get_row, get_ids,
        related_add, related_remove]


dispatcher = json.JSONDispatcher(_exported)
dispatcher.register_encoder("models", _modelchecker, _convert_instance)
dispatcher = auth.need_authentication(webhelpers.setup_dbsession(dispatcher))



##### Restful interface document constructor

def main_constructor(request, **kwargs):
    doc = framework.get_acceptable_document(request)
    doc.stylesheet = request.get_url("css", name="common.css")
    doc.stylesheet = request.get_url("css", name="ui.css")
    doc.stylesheet = request.get_url("css", name="db.css")
    doc.add_javascript2head(url=request.get_url("js", name="MochiKit.js"))
    doc.add_javascript2head(url=request.get_url("js", name="proxy.js"))
    doc.add_javascript2head(url=request.get_url("js", name="ui.js"))
    doc.add_javascript2head(url=request.get_url("js", name="db.js"))
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    NBSP = NM("ASIS", None, "&nbsp;")
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NBSP,
         IF(request.path.count("/") > 2, NM("A", {"href":".."}, "Up")), NBSP,
    ))
    nav.append(NM("P", {"class_": "title"}, "Storage Editor"))
    nav.append(NM("P", None, 
            NM("A", {"href": "/auth/logout"}, "logout")))
    container = doc.add_section("container")
    content = container.add_section("container", id="content")
    messages = container.add_section("container", id="messages")
    extra = container.add_section("container", id="extra")
    return doc


@auth.need_login
@webhelpers.setup_dbsession
def main(request):
    resp = framework.ResponseDocument(request, main_constructor, title="Database")
    return resp.finalize()


##### for server-side markup requests that provide a basic database editor. ####

def doc_constructor(request, **kwargs):
    doc = framework.get_acceptable_document(request)
    doc.stylesheet = request.get_url("css", name="common.css")
    doc.stylesheet = request.get_url("css", name="ui.css")
    doc.stylesheet = request.get_url("css", name="db.css")
    doc.add_javascript2head(url=request.get_url("js", name="MochiKit.js"))
    doc.add_javascript2head(url=request.get_url("js", name="proxy.js"))
    doc.add_javascript2head(url=request.get_url("js", name="ui.js"))
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
    for dbrow in query(tablename, {}):
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
            webhelpers.update_row(request.POST, klass, dbrow)
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
            webhelpers.update_row(request.POST, klass, dbrow)
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
    # test db instance serialization
    from pycopia import autodebug
    disp = json.JSONDispatcher([query])
    disp.register_encoder("models", _modelchecker, _convert_instance)
    sess = models.get_session()
    with webhelpers.GlobalDatabaseContext(sess):
        rowobj = query("Equipment", {"id": 2})[0]
        jse = disp._encoder.encode(rowobj)
        print jse
    sess.close()


