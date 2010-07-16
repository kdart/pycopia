#!/usr/bin/python2.5
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
Helpers for interfacing database storage to web framework.

"""

import sys
import re


from pycopia.db import types
from pycopia.db import models
from pycopia.WWW import framework

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_, or_

dbsession = None


# nothing marker
class NULL(object):
    pass

class GlobalDatabaseContext(object):

    def __init__(self, _dbsession):
        global dbsession
        dbsession = _dbsession

    def __enter__(self):
        return dbsession

    def __exit__(self, type, value, traceback):
        global dbsession
        dbsession = None


# decorator for top-level handlers that sets up DB session.
def setup_dbsession(handler):
    def newhandler(request, *args, **kwargs):
        with framework.DatabaseContext(request) as dbsession:
            with GlobalDatabaseContext(dbsession):
                return handler(request, *args, **kwargs)
    return newhandler


def get_row(modelclass, rowid):
    try:
        dbrow = dbsession.query(modelclass).get(int(rowid))
        if dbrow is None:
            raise framework.HttpErrorNotFound("No such id.")
    except ValueError:
            raise framework.HttpErrorNotFound("Bad id value.")
    return dbrow


def get_ids(modelclass, idlist):
    assert type(idlist) is list
    idlist = [int(i) for i in idlist]
    return dbsession.query(modelclass).filter(modelclass.id.in_(idlist)).all()


def query(modelclass, filt, order_by=None, start=None, end=None):
    try:
        order_by = order_by or modelclass.ROW_DISPLAY[0]
    except AttributeError:
        pass
    q = dbsession.query(modelclass)
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
    return list(q.all())


### update a row ###

def update_row(data, klass, dbrow):
    for metadata in models.get_metadata_iterator(klass):
        value = data.get(metadata.colname, NULL)
        if value is NULL: # can't use None since its a valid value
            continue
        if not value and metadata.nullable:
            value = None
        if metadata.coltype == "RelationProperty":
            relmodel = getattr(klass, metadata.colname).property.mapper.class_
            if isinstance(value, list) and value:
                t = dbsession.query(relmodel).filter(
                                relmodel.id.in_([int(i) for i in value])).all()
                setattr(dbrow, metadata.colname, t)
            elif value is None:
                if metadata.uselist:
                    value = []
                setattr(dbrow, metadata.colname, value)
            else:
                value = int(value)
                if value:
                    t = dbsession.query(relmodel).get(value)
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
                    pass
                setattr(dbrow, metadata.colname, value)
        elif metadata.coltype == "PGText":
            setattr(dbrow, metadata.colname, value)
        else:
            validator = _VALIDATORS.get(metadata.coltype)
            if validator is not None:
                value = validator(value)
            setattr(dbrow, metadata.colname, value)


def validate_float(value):
    if value:
        return float(value)

def validate_int(value):
    if value:
        return int(value)

def validate_bigint(value):
    if value:
        return long(value)

def validate_bool(value):
    if value is None:
        return False
    if value.lower() in ("on", "1", "true", "t"):
        return True
    else:
        return False

def validate_cidr(value):
    if value.count(".") == 3:
        return value

_VALIDATORS = {
    "PGArray": None,
    "PGBigInteger": validate_bigint,
    "PGBinary": None,
    "PGBit": None,
    "PGBoolean": validate_bool,
    "PGChar": None,
    "PGCidr": validate_cidr,
    "PGDate": None,
    "PGDateTime": None,
    "PGFloat": validate_float,
    "PGInet": None,
    "PGInteger": validate_int,
    "PGInterval": None,
    "PGMacAddr": None,
    "PGNumeric": validate_bigint,
    "PGSmallInteger": validate_int,
    "PGString": None,
    "PGText": None,
    "PGTime": None,
    "PGUuid": None,
    "PickleText": None,
    "RelationProperty": None,
    "ValueType": types.ValueType.validate,
    "TestCaseStatus": types.TestCaseStatus.validate,
    "TestCaseType": types.TestCaseType.validate,
    "TestPriorityType": types.TestPriorityType.validate,
}


### edit form ####

def build_edit_form(form, modelclass, row, error=None):
    BR = form.get_new_element("Br")
    if error is not None:
        form.new_para(error, class_="error")
    outerfs = form.add_fieldset(modelclass.__name__)
    for metadata in sorted(models.get_metadata(modelclass)):
        create_input(outerfs, modelclass, metadata, row)
        outerfs.append(BR)
    form.add_input(type="submit", name="submit", value="submit")

def create_input(node, modelclass, metadata, row):
    ctor = _CONSTRUCTORS.get(metadata.coltype)
    if ctor:
        node = ctor(node, modelclass, metadata, row)
        node.class_ = metadata.coltype
        #node.add2class(metadata.coltype)
    else:
        node.new_para("No entry for type %r." % (metadata.colname,), class_="error")

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
    return node.add_radiobuttons(metadata.colname, types.ValueType.get_choices(), 
            checked=value, class_="radioset")

def create_relation_input(node, modelclass, metadata, row):
    vlist = []
    current = getattr(row, metadata.colname)
    relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
    q = dbsession.query(relmodel)
    try:
        order_by = relmodel.ROW_DISPLAY[0]
        q = q.order_by(getattr(relmodel, order_by))
    except (AttributeError, IndexError):
        pass
    for relrow in q.all():
        if metadata.uselist:
            if relrow in current:
                vlist.append((relrow.id, str(relrow), True))
            else:
                vlist.append((relrow.id, str(relrow), False))
        else:
            if relrow is current:
                vlist.append((relrow.id, str(relrow), True))
            else:
                vlist.append((relrow.id, str(relrow), False))
    if metadata.nullable:
        vlist.insert(0, (0, "----"))
    elid = "id_" + metadata.colname
    node.add_label(metadata.colname, elid)
    return node.add_select(vlist, name=metadata.colname, multiple=metadata.uselist, id=elid)

def create_testcasestatus(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseStatus.get_choices(), 
            checked=value, class_="radioset")

def create_testcasetype(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseType.get_choices(), 
            checked=value, class_="radioset")

def create_testpriority(node, modelclass, metadata, row):
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            types.TestPriorityType.get_choices(), 
            checked=value, class_="radioset")


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


### add/create form ####

def build_add_form(form, modelclass):
    BR = form.get_new_element("Br")
    outerfs = form.add_fieldset(modelclass.__name__)
    for metadata in sorted(models.get_metadata(modelclass)):
        new_input(outerfs, modelclass, metadata)
        outerfs.append(BR)
    form.add_input(type="submit", name="submit", value="submit")

def new_input(node, modelclass, metadata):
    ctor = _CREATORS.get(metadata.coltype)
    if ctor:
        node = ctor(node, modelclass, metadata)
        node.class_ = metadata.coltype
        #node.add2class(metadata.coltype)
    else:
        node.new_para("No entry for type %r." % (metadata.colname,), class_="error")

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

def new_relation_input(node, modelclass, metadata, order_by=None):
    choices = models.get_choices(dbsession, modelclass, metadata.colname, order_by)
    if not choices:
        return node.new_para("%s has no choices." % metadata.colname)
    if metadata.nullable:
        choices.insert(0, (0, "----"))
    elid = "id_" + metadata.colname
    node.add_label(metadata.colname, elid)
    return node.add_select(choices, name=metadata.colname, multiple=metadata.uselist, id=elid)

def new_valuetypeinput(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, types.ValueType.get_choices(), checked=0, 
            class_="radioset")

def new_testcasestatus(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseStatus.get_choices(), 
            checked=types.TestCaseStatus.get_default(), 
            class_="radioset")

def new_testcasetype(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestCaseType.get_choices(), 
            checked=types.TestCaseType.get_default(), 
            class_="radioset")

def new_testpriority(node, modelclass, metadata):
    return node.add_radiobuttons(metadata.colname, 
            types.TestPriorityType.get_choices(), 
            checked=types.TestPriorityType.get_default(),
            class_="radioset")

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



### test result helpers

PROJECT_RE = re.compile(r"(\w+)[ .:](\d+)\.(\d+)\.(\d+)\.(\d+)")

[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = types.OBJECTTYPES
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = types.TESTRESULTS

#_COLUMNS = {
#    "testcase": None,           # test case record
#    "environment": None,        # from config
#    "build": None,              # BUILD
#    "tester": None,             # user running the test
#    "testversion": None,        # Version of test implementation
#    "parent": None,             # container object
#    "objecttype": None,         # Object type enumeration
#    "starttime": None,          # STARTTIME (Test, Suite),    RUNNERSTART (module)
#    "endtime": None,            # ENDTIME (Test, Suite), RUNNEREND (module)
#    "arguments": None,          # TESTARGUMENTS (Test), RUNNERARGUMENTS (module)
#    "result": None,             # PASSED, FAILED, EXPECTED_FAIL, INCOMPLETE, ABORT
#    "diagnostic": None,         # The diagnostic message before failure.
#    "testresultdata": None,     # optional serialized data (reference)
#    "resultslocation": None,    # url
#    "testimplementation": None, # implementation 
#    "reportfilename": None,
#    "note": None,               # COMMENT
#    "valid": True,
#}



def resolve_environment(name):
    if name is None:
        return None
    try:
        eid = int(name)
    except ValueError:
        try:
            env = dbsession.query(models.Environment).filter(models.Environment.name==name).one()
        except NoResultFound:
            return None
    else:
        try:
            env = dbsession.query(models.Environment).get(eid)
        except NoResultFound:
            return None
    return env


def resolve_build(buildstring):
    if buildstring is None:
        return
    mo = PROJECT_RE.search(buildstring)
    if mo:
        try:
            pname, major, minor, sub, build = mo.groups()
            major = int(major); minor = int(minor); sub = int(sub); build = int(build)
        except ValueError:
            return None
        try:
            proj = dbsession.query(models.Project).filter(models.Project.name==pname).one()
        except NoResultFound:
            return None
        try:
            projectversion = dbsession.query(models.ProjectVersion).filter(and_(
                    models.ProjectVersion.project==proj,
                    models.ProjectVersion.valid==True,
                    models.ProjectVersion.major==major,
                    models.ProjectVersion.minor==minor,
                    models.ProjectVersion.subminor==sub,
                    models.ProjectVersion.build==build)
                    ).one()
        except NoResultFound:
            projectversion = models.create(
                    models.ProjectVersion, project=proj, valid=True,
                    major=major, minor=minor, subminor=sub, build=build)
            dbsession.add(projectversion)
        return projectversion
    else:
        return None


def create_pick_list(node, modelclass, filtermap=None):
    vlist = []
    q = dbsession.query(modelclass)
    try:
        order_by = modelclass.ROW_DISPLAY[0]
        q = q.order_by(getattr(modelclass, order_by))
    except (AttributeError, IndexError):
        pass

    if filtermap:
        for name, value in filtermap.items():
            attrib = getattr(modelclass, name)
            q = q.filter(attrib==value)

    for dbrow in q.all():
        vlist.append((dbrow.id, str(dbrow), False))
    name = modelclass.__name__
    elid = "id_" + name
    node.add_label(name, elid)
    return node.add_select(vlist, name=name.lower(), multiple=False, id=elid)


