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
from pycopia.WWW import json
from pycopia.WWW import framework
from pycopia.WWW.middleware import auth

from sqlalchemy.exc import DataError, IntegrityError
#from sqlalchemy.sql import select

_dbsession = models.get_session()
_tables = set(models.class_names())



def get_tables():
    return _tables


def update(modelname, entry_id, data):
    pass


def table_get(modelname, filt, order_by=None, start=None, end=None):
    klass = get_model(modelname)
    q = _dbsession.query(klass)
    for name, value in filt.items():
        attrib = getattr(klass, name)
        q = q.filter(attrib==value)
    if order_by:
        q = q.order_by(getattr(klass, order_by))
    if start is not None:
        return list(q[start:end])
    else:
        return list(q)


def get_model(modelname):
    try:
        return getattr(models, modelname)
    except AttributeError:
        raise framework.HHttpErrorNotFound("No model %r found." % modelname)


def get_table_metadata(modelname):
    klass = get_model(modelname)
    return models.get_metadata(klass)


def get_row(modelclass, rowid):
    try:
        dbrow = _dbsession.query(modelclass).get(int(rowid))
        if dbrow is None:
            raise framework.HttpErrorNotFound("No such id.")
    except ValueError:
            raise framework.HttpErrorNotFound("Bad id value.")
    return dbrow


def get_choices(modelname, attribute):
    return [] # XXX


def delete(modelname, entry_id):
    klass = get_model(modelname)
    try:
        obj = _dbsession.query(klass).get(entry_id)
        name = str(obj)
        _dbsession.delete(obj)
        _dbsession.commit()
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


_exported = [get_tables, get_table_metadata, table_get, get_choices, update, delete]

dispatcher = json.JSONDispatcher(_exported)
dispatcher.register_encoder("models", _modelchecker, _convert_instance)
dispatcher = auth.need_authentication(dispatcher)



##### for server-side markup requests that provide a basic database editor. ####

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
def view(request, tablename=None, rowid=None):
    klass = get_model(tablename)
    dbrow = get_row(klass, rowid)
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
        build_add_form(form, klass)
        return resp.finalize()

    def post(self, request, tablename=None):
        klass = get_model(tablename)
        dbrow = klass()
        try:
            update_row(request, klass, dbrow)
        except types.ValidationError, err:
            _dbsession.rollback()
            request.log_error("create ValidationError: %s: %s\n" % (tablename, err))
            title = "Recreate new %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            resp.new_para(err, class_="error")
            form = resp.add_form(action=request.get_url(addentry, tablename=tablename))
            build_add_form(form, klass)
            return resp.finalize()

        _dbsession.add(dbrow)
        try:
            _dbsession.commit()
        except (DataError, IntegrityError), err:
            request.log_error("create error: %s: %s\n" % (tablename, err))
            _dbsession.rollback()
            title = "Create new %s" % (tablename, )
            resp = self.get_response(request, title=title)
            resp.new_para(title + ", again.")
            resp.new_para(err, class_="error")
            form = resp.add_form(action=request.get_url(addentry, tablename=tablename))
            build_add_form(form, klass)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.get_url(listtable, tablename=tablename))

addentry = auth.need_login(CreateRequestHandler(doc_constructor))


def build_add_form(form, modelclass):
    builder = _FORMBUILDERS.get(modelclass.__name__)
    if builder is None:
        return build_generic_add_form(form, modelclass)
    return builder(form, modelclass)


def build_test_case_add(form, modelclass):
    BR = form.get_new_element("Br")
    fs = form.add_fieldset(modelclass.__name__)

    metamap = dict((c.colname, c) for c in models.get_metadata(modelclass))

    for colname in ('name', 'purpose', 'passcriteria', 'startcondition', 'endcondition',
                    'procedure', 'reference', 'testimplementation',
                    'functionalarea', 'suite', 'prerequisite', 'automated', 'interactive'):

        metadata = metamap[colname]
        ctor = _CREATORS.get(metadata.coltype)
        node = ctor(fs, modelclass, metadata)
        node.class_ = metadata.coltype
        fs.append(BR)
    for colname in ('priority', 'cycle', 'status'):
        metadata = metamap[colname]
        ctor = _CREATORS.get(metadata.coltype)
        node = ctor(fs, modelclass, metadata)
        node.class_ = "radioset"
        fs.append(BR)

    form.add_input(type="submit", name="submit", value="submit")


def build_testcase_edit_form(form, modelclass, row, error=None):
    BR = form.get_new_element("Br")
    if error is not None:
        form.new_para(error, class_="error")
    fs = form.add_fieldset(modelclass.__name__)

    metamap = dict((c.colname, c) for c in models.get_metadata(modelclass))

    for colname in ('name', 'purpose', 'passcriteria', 'startcondition', 'endcondition',
                    'procedure', 'reference', 'testimplementation',
                    'functionalarea', 'suite', 'prerequisite', 'automated', 'interactive'):
        metadata = metamap[colname]
        ctor = _CONSTRUCTORS.get(metadata.coltype)
        node = ctor(fs, modelclass, metadata, row)
        node.class_ = metadata.coltype
        fs.append(BR)
    for colname in ('priority', 'cycle', 'status'):
        metadata = metamap[colname]
        ctor = _CONSTRUCTORS.get(metadata.coltype)
        node = ctor(fs, modelclass, metadata, row)
        node.class_ = "radioset"
        fs.append(BR)

    form.add_input(type="submit", name="submit", value="submit")


_FORMBUILDERS = {
    "TestCase": build_test_case_add,
}

_EDITFORMBUILDERS = {
    "TestCase": build_testcase_edit_form,
}

def build_generic_add_form(form, modelclass):
    BR = form.get_new_element("Br")
    fs = form.add_fieldset(modelclass.__name__)
    for metadata in sorted(models.get_metadata(modelclass)):
        ctor = _CREATORS.get(metadata.coltype)
        if ctor:
            node = ctor(fs, modelclass, metadata)
            node.class_ = metadata.coltype
        else:
            fs.new_para("No entry for type %r." % (metadata.colname,), class_="error")
        fs.append(BR)
    form.add_input(type="submit", name="submit", value="submit")

def new_textarea(node, modelclass, metadata):
    return node.add_fieldset(metadata.colname).add_textarea(metadata.colname, metadata.default or "")

def new_boolean_input(node, modelclass, metadata):
    id = "id_" + metadata.colname
    node.add_label(metadata.colname, id)
    return node.add_input(type="checkbox", name=metadata.colname, id=id, checked=metadata.default)

def new_textinput(node, modelclass, metadata):
    return node.add_textinput(metadata.colname, metadata.colname, metadata.default or "")

def new_pickleinput(node, modelclass, metadata):
    if metadata.default is None:
        default = ""
    else:
        default = repr(metadata.default)
    return node.add_textinput(metadata.colname, metadata.colname, default)

def new_relation_input(node, modelclass, metadata):
    relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
    choices = [(str(relrow), relrow.id) for relrow in _dbsession.query(relmodel).all()]
    if not choices:
        return node.new_para("%s has no choices." % metadata.colname)
    if metadata.nullable:
        choices.insert(0, ("----", 0))
    elid = "id_" + metadata.colname
    node.add_label(metadata.colname, elid)
    return node.add_select(choices, name=metadata.colname, multiple=metadata.uselist, id=elid)

def new_valuetypeinput(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, types.ValueType.get_choices(), checked=0)

def new_testcasestatus(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseStatus.get_choices(), 
            checked=types.TestCaseStatus.get_default())

def new_testcasetype(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseType.get_choices(), 
            checked=types.TestCaseType.get_default())

def new_testpriority(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestPriorityType.get_choices(), 
            checked=types.TestPriorityType.get_default())

_CREATORS = {
    "PGArray": None,
    "PGBigInteger": new_textinput,
    "PGBinary": None,
    "PGBit": None,
    "PGBoolean": new_boolean_input,
    "PGChar": new_textinput,
    "PGCidr": new_textinput,
    "PGDate": new_textinput,
    "PGDateTime": new_textinput,
    "PGFloat": new_textinput,
    "PGInet": new_textinput,
    "PGInteger": new_textinput,
    "PGInterval": new_textinput,
    "PGMacAddr": new_textinput,
    "PGNumeric": new_textinput,
    "PGSmallInteger": new_textinput,
    "PGString": new_textinput,
    "PGText": new_textarea,
    "PGTime": new_textinput,
    "PGUuid": new_textinput,
    "PickleText": new_pickleinput,
    "ValueType": new_valuetypeinput,
    "RelationProperty": new_relation_input,
    "TestCaseStatus": new_testcasestatus,
    "TestCaseType": new_testcasetype,
    "TestPriorityType": new_testpriority,
}


class EditRequestHandler(framework.RequestHandler):

    def get(self, request, tablename=None, rowid=None):
        klass = get_model(tablename)
        dbrow = get_row(klass, rowid)
        title = "Edit %s %s" % (tablename, dbrow)
        resp = self.get_response(request, title=title)
        resp.new_para(title)
        form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
        build_edit_form(form, klass, dbrow)
        return resp.finalize()

    def post(self, request, tablename=None, rowid=None):
        klass = get_model(tablename)
        dbrow = get_row(klass, rowid)
        try:
            update_row(request, klass, dbrow)
        except types.ValidationError, err:
            _dbsession.rollback()
            title = "Re-edit %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
            build_edit_form(form, klass, dbrow, err)
            return resp.finalize()

        try:
            _dbsession.commit()
        except (DataError, IntegrityError), err:
            _dbsession.rollback()
            title = "Re-edit %s %s" % (tablename, dbrow)
            resp = self.get_response(request, title=title)
            resp.new_para(title)
            form = resp.add_form(action=request.get_url(edit, tablename=tablename, rowid=rowid))
            build_edit_form(form, klass, dbrow, err)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.get_url(listtable, tablename=tablename))

edit = auth.need_login(EditRequestHandler(doc_constructor))


def build_edit_form(form, modelclass, row, error=None):
    builder = _EDITFORMBUILDERS.get(modelclass.__name__)
    if builder is None:
        return build_generic_edit_form(form, modelclass, row, error)
    return builder(form, modelclass, row, error)

def build_generic_edit_form(form, modelclass, row, error=None):
    BR = form.get_new_element("Br")
    if error is not None:
        form.new_para(error, class_="error")
    fs = form.add_fieldset(modelclass.__name__)
    for metadata in sorted(models.get_metadata(modelclass)):
        ctor = _CONSTRUCTORS.get(metadata.coltype)
        if ctor:
            node = ctor(fs, modelclass, metadata, row)
            node.class_ = metadata.coltype
        else:
            fs.new_para("No entry for type %r." % (metadata.colname,), class_="error")
        fs.append(BR)
    form.add_input(type="submit", name="submit", value="submit")

def create_textarea(node, modelclass, metadata, row):
    value = getattr(row, metadata.colname)
    return node.add_fieldset(metadata.colname).add_textarea(metadata.colname, value)

def create_boolean_input(node, modelclass, metadata, row):
    id = "id_" + metadata.colname
    value = getattr(row, metadata.colname)
    node.add_label(metadata.colname, id)
    return node.add_input(type="checkbox", name=metadata.colname, id=id, checked=value)

def create_textinput(node, modelclass, metadata, row):
    value = getattr(row, metadata.colname)
    return node.add_textinput(metadata.colname, metadata.colname, value or "")

def create_pickleinput(node, modelclass, metadata, row):
    value = getattr(row, metadata.colname)
    if metadata.nullable and value is None:
        value = ""
    else:
        value = repr(value)
    return node.add_textinput(metadata.colname, metadata.colname, value)

def create_valuetypeinput(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, types.ValueType.get_choices(), checked=value)

def create_relation_input(node, modelclass, metadata, row):
    vlist = []
    current = getattr(row, metadata.colname)
    relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
    for relrow in _dbsession.query(relmodel).all():
        if metadata.uselist:
            if relrow in current:
                vlist.append((str(relrow), relrow.id, True))
            else:
                vlist.append((str(relrow), relrow.id, False))
        else:
            if relrow is current:
                vlist.append((str(relrow), relrow.id, True))
            else:
                vlist.append((str(relrow), relrow.id, False))
    if metadata.nullable:
        vlist.insert(0, ("----", 0))
    elid = "id_" + metadata.colname
    node.add_label(metadata.colname, elid)
    return node.add_select(vlist, name=metadata.colname, multiple=metadata.uselist, id=elid)

def create_testcasestatus(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseStatus.get_choices(), 
            checked=value)

def create_testcasetype(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseType.get_choices(), 
            checked=value)

def create_testpriority(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestPriorityType.get_choices(), 
            checked=value)


_CONSTRUCTORS = {
    "PGArray": None,
    "PGBigInteger": create_textinput,
    "PGBinary": None,
    "PGBit": None,
    "PGBoolean": create_boolean_input,
    "PGChar": create_textinput,
    "PGCidr": create_textinput,
    "PGDate": create_textinput,
    "PGDateTime": create_textinput,
    "PGFloat": create_textinput,
    "PGInet": create_textinput,
    "PGInteger": create_textinput,
    "PGInterval": create_textinput,
    "PGMacAddr": create_textinput,
    "PGNumeric": create_textinput,
    "PGSmallInteger": create_textinput,
    "PGString": create_textinput,
    "PGText": create_textarea,
    "PGTime": create_textinput,
    "PGUuid": create_textinput,
    "PickleText": create_pickleinput,
    "ValueType": create_valuetypeinput,
    "RelationProperty": create_relation_input,
    "TestCaseStatus": create_testcasestatus,
    "TestCaseType": create_testcasetype,
    "TestPriorityType": create_testpriority,
}

def update_row(request, klass, dbrow):
    for metadata in models.get_metadata(klass):
        value = request.POST.get(metadata.colname)
        if metadata.coltype == "RelationProperty":
            relmodel = getattr(klass, metadata.colname).property.mapper.class_
            if isinstance(value, list) and value:
                t = _dbsession.query(relmodel).filter(
                                relmodel.id.in_([int(i) for i in value])).all()
                setattr(dbrow, metadata.colname, t)
            elif value is None:
                if metadata.uselist:
                    value = []
                setattr(dbrow, metadata.colname, value)
            else:
                value = int(value)
                if value:
                    t = _dbsession.query(relmodel).get(value)
                    if metadata.uselist:
                        t = [t]
                    setattr(dbrow, metadata.colname, t)
        elif metadata.coltype == "PickleText":
            if value is None:
                if metadata.nullable:
                    setattr(dbrow, metadata.colname, value)
                else:
                    setattr(dbrow, metadata.colname, "")
            else:
                try:
                    value = eval(value, {}, {})
                except: # allows use of unquoted strings.
                    ex, exval, tb = sys.exc_info()
                    request.log_error("warning: %r did not evaluate: %s.\n" % (value, exval))
                setattr(dbrow, metadata.colname, value)
        elif metadata.coltype == "PGText":
            if not value and metadata.nullable:
                value = None
            setattr(dbrow, metadata.colname, value)
        else:
            validator = _VALIDATORS.get(metadata.coltype)
            if validator is not None:
                value = validator(value)
            setattr(dbrow, metadata.colname, value)



def validate_float(value):
    if value is None:
        return None
    return float(value)

def validate_int(value):
    if value is None:
        return None
    return int(value)

def validate_bigint(value):
    if value is None:
        return None
    return long(value)

def validate_datetime(value):
    if not value:
        return None
    else:
        return value

def validate_bool(value):
    if value is None:
        return False
    if value.lower() in ("on", "1", "true", "t"):
        return True
    else:
        return False


_VALIDATORS = {
    "PGArray": None,
    "PGBigInteger": validate_bigint,
    "PGBinary": None,
    "PGBit": None,
    "PGBoolean": validate_bool,
    "PGChar": None,
    "PGCidr": None,
    "PGDate": validate_datetime,
    "PGDateTime": validate_datetime,
    "PGFloat": validate_float,
    "PGInet": None,
    "PGInteger": validate_int,
    "PGInterval": None,
    "PGMacAddr": None,
    "PGNumeric": validate_bigint,
    "PGSmallInteger": validate_int,
    "PGString": None,
    "PGText": None,
    "PGTime": validate_datetime,
    "PGUuid": None,
    "PickleText": None,
    "RelationProperty": None,
    "ValueType": types.ValueType.validate,
    "TestCaseStatus": types.TestCaseStatus.validate,
    "TestCaseType": types.TestCaseType.validate,
    "TestPriorityType": types.TestPriorityType.validate,
}


if __name__ == "__main__":
    pass
#    from pycopia.WWW import framework
#    rq = framework.HTTPRequest
    #print _convert_instance(test_results(0, 10)[0])
    print _tables
    print table_get("InterfaceType", {"enumeration": 3})[0]

