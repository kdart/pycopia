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
Provides a web service interface to the Pycopia database model. Also
provides a basic database editor application.

Usually mapped to /storage/ URL. See storage.conf for details.

"""

import sys
import itertools

from pycopia import logging
from pycopia.db import types
from pycopia.db import models
from pycopia.db import webhelpers

#from pycopia.dictlib import AttrDict
from pycopia.WWW import json
from pycopia.WWW import framework
from pycopia.WWW import HTML5
from pycopia.WWW.middleware import auth

from sqlalchemy.exc import DataError, IntegrityError


_tables = set(models.class_names())



def get_tables():
    return _tables


def get_model(modelname):
    try:
        return getattr(models, modelname)
    except AttributeError:
        raise framework.HttpErrorNotFound("No model %r found." % modelname)


def get_uidata():
    cf = json.current_request.config
    return {"ICONMAP": cf.ICONMAP}


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
        webhelpers.update_row_from_data(data, klass, dbrow)
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


def query(modelname, filt=None, columns=None, order_by=None, start=None, end=None):
    klass = get_model(modelname)
    return webhelpers.query(klass, filt, columns, order_by, start, end)


def get_choices(modelname, attribute, order_by=None):
    modelclass = get_model(modelname)
    return models.get_choices(webhelpers.dbsession, modelclass, attribute, order_by)


def get_rowdisplay(modelname):
    modelclass = get_model(modelname)
    return models.get_rowdisplay(modelclass)


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
        webhelpers.update_row_from_data(data, klass, dbrow)
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
def _convert_instance(obj):
    values = {"id": obj.id}
    for metadata in models.get_metadata_iterator(obj.__class__):
        if metadata.coltype == "RelationshipProperty":
            value = getattr(obj, metadata.colname)
            if value is not None:
                if metadata.uselist:
                    if metadata.collection == "MappedCollection":
                        value = value.itervalues()
                    values[metadata.colname] = [_obj_representation(o, {"id": o.id}) for o in value]
                else:
                    values[metadata.colname] = _obj_representation(value, {"id": value.id})
            else:
                values[metadata.colname] = value # None/null
        else:
            values[metadata.colname] = getattr(obj, metadata.colname)
    return _obj_representation(obj, values)

def _obj_representation(obj, values):
    return {"_class_": obj.__class__.__name__,
            "_dbmodel_": True,
            "_str_": str(obj),
            "value": values}

def _modelchecker(obj):
    try:
        return obj.__class__.__name__ in _tables
    except AttributeError:
        return False

# Functions exported to javascript via proxy.
_exported = [get_tables, get_table_metadata, get_table_metadata_map, get_choices, get_uidata,
        query, create, updaterow, deleterow, get_row, get_ids, get_rowdisplay,
        related_add, related_remove]


dispatcher = json.JSONDispatcher(_exported)
dispatcher.register_encoder("models", _modelchecker, _convert_instance)
dispatcher = auth.need_authentication(webhelpers.setup_dbsession(dispatcher))



##### for server-side markup requests that provide a basic database editor. ####
##### Code below here will eventually disappear.

def doc_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheets = ["common.css", "ui.css", "db.css"]
    doc.scripts = ["MochiKit.js", "proxy.js", "ui.js", "sorttable.js", "db.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    NBSP = NM("_", None)
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NBSP,
         NM("A", {"href": request.get_url(listall)}, "Top"), NBSP,
         NM("A", {"href":".."}, "Up") if request.path.count("/") > 2 else NBSP, NBSP,
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
    tbl = resp.doc.add_table(class_="sortable", width="100%")
    tbl.caption(tablename)
    colnames = models.get_rowdisplay(klass)
    tbl.new_headings("", *colnames)
    tbl.headings[0].class_ = "sorttable_nosort"
    tbl.new_footer("", *colnames)
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
            NM("A", {"href": "javascript:doDeleteItem(%r, %r);" % (tablename, rowid)},
                resp.get_icon("delete")),
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
        #rows = query("Equipment", {"active":True}, ["name", "model", "serno"], None, 0, 5)
        #for rowobj in rows:
        #    #print rowobj
        #    jse = disp._encoder.encode(rowobj)
        #    print jse
        md = get_table_metadata("TestCase")
        print(md)
        json = disp._encoder.encode(md)
        print json
        print type(json)
        print len(json)
    sess.close()


