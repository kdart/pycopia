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
Helpers for interfacing database storage to web framework.

"""
from __future__ import print_function

import sys
import re


from pycopia.db import types
from pycopia.db import models
from pycopia.WWW import framework

#from sqlalchemy.orm.properties import RelationshipProperty
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
        with models.DatabaseContext() as dbsession:
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
    if not idlist:
        return []
    idlist = [int(i) for i in idlist]
    return dbsession.query(modelclass).filter(modelclass.id.in_(idlist)).all()


def query(modelclass, filt=None, columns=None, order_by=None, start=None, end=None):
    try:
        order_by = order_by or modelclass.ROW_DISPLAY[0]
    except AttributeError:
        pass
    # select only columns if list of column names is provided.
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


### update a row ###

# updates a row from javascript/json object
def update_row_from_data(data, klass, dbrow):
    for metadata in models.get_metadata_iterator(klass):
        value = data.get(metadata.colname, NULL)
        if value is NULL: # can't use None since its a valid value
            continue
        _update_row(data, klass, dbrow, metadata, value)


# updates a row from form data
def update_row(data, klass, dbrow):
    for metadata in models.get_metadata_iterator(klass):
        value = data.get(metadata.colname)
        _update_row(data, klass, dbrow, metadata, value)


def _update_row(data, klass, dbrow, metadata, value):
    if not value and metadata.nullable:
        value = None
    if metadata.coltype == "RelationshipProperty":
        relmodel = getattr(klass, metadata.colname).property.mapper.class_
        if isinstance(value, list) and value:
            t = dbsession.query(relmodel).filter(
                            relmodel.id.in_([int(i) for i in value])).all()
            if metadata.collection == "MappedCollection":
                t = dict((r.name, r) for r in t)
            setattr(dbrow, metadata.colname, t)
        elif value is None:
            if metadata.uselist:
                value = {} if metadata.collection == "MappedCollection" else []
            setattr(dbrow, metadata.colname, value)
        else:
            value = int(value)
            if value:
                t = dbsession.query(relmodel).get(value)
                if metadata.uselist:
                    t = {t.name: t} if metadata.collection == "MappedCollection" else [t]
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
    elif metadata.coltype == "TEXT":
        setattr(dbrow, metadata.colname, value)
    else:
        if value is None and metadata.nullable:
            setattr(dbrow, metadata.colname, None)
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
    "ARRAY": None,
    "BIGINT": validate_bigint,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": validate_bool,
    "CHAR": None,
    "Cidr": validate_cidr,
    "Inet": None,
    "DATE": None,
    "TIMESTAMP": None,
    "FLOAT": validate_float,
    "INTEGER": validate_int,
    "INTERVAL": None,
    "MACADDR": None,
    "NUMERIC": validate_bigint,
    "SMALLINT": validate_int,
    "VARCHAR": None,
    "TEXT": None,
    "TIME": None,
    "UUID": None,
    "PickleText": None,
    "RelationshipProperty": None,
    "ValueType": types.ValueType.validate,
    "TestCaseStatus": types.TestCaseStatus.validate,
    "TestCaseType": types.TestCaseType.validate,
    "PriorityType": types.PriorityType.validate,
    "SeverityType": types.SeverityType.validate,
    "LikelihoodType": types.LikelihoodType.validate,
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
    if metadata.collection == "MappedCollection":
        current = current.values()
    relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
    q = dbsession.query(relmodel)
    try:
        order_by = relmodel.ROW_DISPLAY[0]
        q = q.order_by(getattr(relmodel, order_by))
    except (AttributeError, IndexError):
        pass
    for relrow in q:
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

def create_enumtype(node, modelclass, metadata, row):
    enumtype = getattr(types, metadata.coltype)
    value = int(getattr(row, metadata.colname))
    return node.add_radiobuttons(metadata.colname, 
            enumtype.get_choices(), 
            checked=value, class_="radioset")

_CONSTRUCTORS = {
    "ARRAY": None,
    "BIGINT": create_textinput,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": create_boolean_input,
    "CHAR": create_textinput,
    "Cidr": create_textinput,
    "Inet": create_textinput,
    "DATE": create_textinput,
    "TIMESTAMP": create_textinput,
    "FLOAT": create_textinput,
    "INTEGER": create_textinput,
    "INTERVAL": create_textinput,
    "MACADDR": create_textinput,
    "NUMERIC": create_textinput,
    "SMALLINT": create_textinput,
    "VARCHAR": create_textinput,
    "TEXT": create_textarea,
    "TIME": create_textinput,
    "UUID": create_textinput,
    "PickleText": create_pickleinput,
    "ValueType": create_valuetypeinput,
    "RelationshipProperty": create_relation_input,
    "TestCaseStatus": create_enumtype,
    "TestCaseType": create_enumtype,
    "PriorityType": create_enumtype,
    "SeverityType": create_enumtype,
    "LikelihoodType": create_enumtype,
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

def new_enumtype(node, modelclass, metadata):
    enumtype = getattr(types, metadata.coltype)
    return node.add_radiobuttons(metadata.colname, 
            enumtype.get_choices(), 
            checked=enumtype.get_default(),
            class_="radioset")

_CREATORS = {
    "ARRAY": None,
    "BIGINT": new_textinput,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": new_boolean_input,
    "CHAR": new_textinput,
    "Cidr": new_textinput,
    "Inet": new_textinput,
    "DATE": new_textinput,
    "TIMESTAMP": new_textinput,
    "FLOAT": new_textinput,
    "INTEGER": new_textinput,
    "INTERVAL": new_textinput,
    "MACADDR": new_textinput,
    "NUMERIC": new_textinput,
    "SMALLINT": new_textinput,
    "VARCHAR": new_textinput,
    "TEXT": new_textarea,
    "TIME": new_textinput,
    "UUID": new_textinput,
    "PickleText": new_pickleinput,
    "ValueType": new_valuetypeinput,
    "RelationshipProperty": new_relation_input,
    "TestCaseStatus": new_enumtype,
    "TestCaseType": new_enumtype,
    "PriorityType": new_enumtype,
    "SeverityType": new_enumtype,
    "LikelihoodType": new_enumtype,
}



### test result helpers

PROJECT_RE = re.compile(r"(\w+)[ .:](\d+)\.(\d+)\.(\d+)\.(\d+)")

[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = types.OBJECTTYPES
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = types.TESTRESULTS


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

    for dbrow in q:
        vlist.append((dbrow.id, str(dbrow), False))
    name = modelclass.__name__
    elid = "id_" + name
    node.add_label(name, elid)
    return node.add_select(vlist, name=name.lower(), multiple=False, id=elid)


