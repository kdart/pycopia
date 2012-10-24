#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""
Widgets for DB editor.

"""

from datetime import datetime
import urwid

from pycopia.db import types
from pycopia.db import models


PALETTE = [
    ('banner', 'black', 'light gray', 'standout,underline'),
    ('bg', 'black', 'dark blue'),
    #('body','black','light gray', 'standout'),
    ('body','default', 'default'),
    ('top','default', 'default'),
    ('border','black','dark blue'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('buttn','black','dark cyan'),
    ('buttnf','white','dark blue','bold'),
    ('dirmark', 'black', 'dark cyan', 'bold'),
    ('editbx','light gray', 'dark blue'),
    ('editcp','black','light gray', 'standout'),
    ('editfc','white', 'dark blue', 'bold'),
    ('error', 'black', 'dark red'),
    ('flag', 'dark gray', 'light gray'),
    ('flagged', 'black', 'dark green', ('bold','underline')),
    ('flagged focus', 'yellow', 'dark cyan', ('bold','standout','underline')),
    ('butfocus', 'light gray', 'dark blue', 'standout'),
    ('focus','white','black','bold'),
    ('focustext','light gray','dark blue'),
    ('foot', 'light gray', 'black'),
    ('head', 'white', 'black', 'standout'),
    ('subhead', 'yellow', 'black', 'standout'),
    ('important','light magenta','default',('standout','underline')),
    ('key', "black", 'light cyan', 'underline'),
    ('reverse','light gray','black'),
    ('selectable','black', 'dark cyan'),
    ('shadow','white','black'),
    ('notimplemented', 'dark red', 'black'),
    ('streak', 'black', 'dark red', 'standout'),
    ('title', 'white', 'black', 'bold'),
    ('colhead', 'light blue', 'black', 'default'),
]


### shorthand notation

AM = urwid.AttrMap



class BaseInput(urwid.WidgetWrap):
    signals = ["update"]

    def _col_creator(self, metadata, widget, legend=None):
        return urwid.Columns([
                ('fixed', 25,
                        urwid.Padding(AM(urwid.Text(legend or metadata.colname), 'reverse'), align="right", right=2)),
                 widget ])

    def _not_implemented(self, metadata):
        return urwid.Text([metadata.coltype, ("notimplemented", " Not implemented yet")])

    @property
    def value(self):
        return None


class BooleanInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.CheckBox(metadata.colname, state=value)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return bool(self.wid.get_state())


class IntInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = 0 if value is None else value
        self.wid = urwid.IntEdit(default=val)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.value()


class FloatInput(BaseInput):
    signals = ["update"]
    def __init__(self, model, metadata, value, legend=None):
        val = 0.0 if value is None else value
        self.wid = self._not_implemented(metadata)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.value()


class CharInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class TextInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class PythonInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=True)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class JsonInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=True)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class CidrInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend or "Network (x.x.x.x/m)"))

    @property
    def value(self):
        return self.wid.edit_text


class InetInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend or "IP address (x.x.x.x/m)"))

    @property
    def value(self):
        return self.wid.edit_text


class MACInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend or "MAC (xx:xx:xx:xx:xx:xx)"))

    @property
    def value(self):
        return self.wid.edit_text


class DateInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class TimeInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class TimestampInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.Edit(edit_text=str(value), multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        return self.wid.edit_text


class ValueTypeInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        blist = []
        glist = []
        maxl = 0
        for num, name in types.ValueType.get_choices():
            maxl = max(maxl, len(name))
            b = urwid.RadioButton(blist, name, False, user_data=num)
            b.value = num
            glist.append(AM(b, 'buttn','buttnf'))
        # set the right value
        for b in blist:
            if b.value == value:
                b.state = True
        self.wid = urwid.GridFlow(glist, maxl+4, 1, 1, 'left')
        self.blist = blist
        self.__super.__init__(self._col_creator(metadata, self.wid))

    @property
    def value(self):
        for b in self.blist:
            if b.state is True:
                return b.value


class EnumTypeInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = self._not_implemented(metadata)
        self.__super.__init__(self._col_creator(metadata, self.wid))


class RelationshipInput(BaseInput):
    def __init__(self, session, model, metadata, value, legend=None):
        self.session = session
        self.modelclass = model
        self.metadata = metadata
        if value is None:
            but = urwid.Button("Select to edit")
            if metadata.uselist:
                self.dbvalue = []
            else:
                self.dbvalue = 0
        else:
            self.dbvalue = value
            but = urwid.Button("{} (Edit)".format(value))
        urwid.connect_signal(but, 'click', self._expand)
        wid = AM(but, "butn", "buttnf")
        #wid = urwid.GridFlow([urwid.Text(str(value)), AM(but, "butn", "buttnf")], 20, 1, 1, 'left')
        self.__super.__init__(self._col_creator(metadata, wid, legend))

    @property
    def value(self):
        return self.dbvalue

    def _create_relation_input(self):
        choices = models.get_choices(self.session, self.modelclass, self.metadata.colname, None)
        if not choices:
            but = urwid.Button("Create one")
            return urwid.Columns([
                        urwid.Padding(AM(urwid.Text("No choices"), 'reverse'), align="left"),
                 AM(but, "selectable", "focus")])
        wlist = []
        if self.metadata.uselist:
            self.dbvalue = set(self.dbvalue)
            addnew = urwid.Button("Add New")
            urwid.connect_signal(addnew, 'click', self._add_new)
            wlist.append(AM(addnew, "butn", "buttnf"))
            for cid, cname in choices:
                but = urwid.CheckBox(cname, state=False)
                urwid.connect_signal(but, 'change', self._multi_select, cid)
                #entry = ListEntry(but)
                wlist.append(but)
            done = urwid.Button("Done")
            urwid.connect_signal(done, 'click', self._done_multiselect)
            wlist.append(AM(done, "butn", "buttnf"))
            listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))
            return urwid.BoxAdapter(listbox, 7)
        else:
            if self.metadata.nullable:
                entry = ListEntry(urwid.Text("None (remove)"))
                urwid.connect_signal(entry, 'activate', self._single_select, (0, "None"))
                wlist.append(entry)
            for cid, cname in choices:
                entry = ListEntry(urwid.Text(cname))
                urwid.connect_signal(entry, 'activate', self._single_select, (cid, cname))
                wlist.append(entry)
            listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))
            return urwid.BoxAdapter(listbox, 7)

    def _expand(self, b):
        newwid = self._create_relation_input()
        self._w.widget_list[1] = newwid

    def _add_new(self, b):
        pass # TODO
        cname = self.metadata.colname
        but = urwid.Button("{} (Edit)".format(cname))
        urwid.connect_signal(but, 'click', self._expand)
        wid = AM(but, "butn", "buttnf")
        self._w.widget_list[1] = wid

    def _single_select(self, le, data):
        cid, cname = data
        self.dbvalue = cid
        but = urwid.Button("{} (Edit)".format(cname))
        urwid.connect_signal(but, 'click', self._expand)
        wid = AM(but, "butn", "buttnf")
        self._w.widget_list[1] = wid

    def _done_multiselect(self, b):
        self.dbvalue = list(self.dbvalue)
        but = urwid.Button("{} (Edit)".format(",".join(map(str, self.dbvalue))))
        urwid.connect_signal(but, 'click', self._expand)
        wid = AM(but, "butn", "buttnf")
        self._w.widget_list[1] = wid


    def _multi_select(self, b, newstate, val):
        if newstate is True:
            self.dbvalue.add(val)
        else:
            try:
                self.dbvalue.remove(val)
            except KeyError:
                pass

#    def selectable(self):
#        return True
#
#    def keypress(self, size, key):
#        if self._command_map[key] != 'activate':
#            return key
#        self._emit('activate')


    #choices = models.get_choices(_session, modelclass, metadata.colname, None)
    #if not choices:
    #    ui.Print("%s has no choices." % metadata.colname)
    #    if metadata.uselist:
    #        return []
    #    else:
    #        return None
    #if metadata.uselist:
    #    return ui.choose_multiple_from_map(dict(choices), None, "%%I%s%%N" % metadata.colname).keys()
    #else:
    #    if metadata.nullable:
    #        choices.insert(0, (0, "Nothing"))
    #        default = 0
    #    else:
    #        default = choices[0][0]
    #    return ui.choose_key(dict(choices), default, "%%I%s%%N" % metadata.colname)


# Map database types and psuedo-types to a form element
_TYPE_CREATE_WIDGETS = {
    "ARRAY": None,
    "BIGINT": IntInput,
    "BYTEA": None,
    "BIT": None,
    "BOOLEAN": BooleanInput,
    "CHAR": CharInput,
    "Cidr": CidrInput,
    "Inet": InetInput,
    "DATE": DateInput,
    "TIMESTAMP": TimestampInput,
    "FLOAT": FloatInput,
    "INTEGER": IntInput,
    "INTERVAL": None,
    "MACADDR": MACInput,
    "NUMERIC": None,
    "SMALLINT": IntInput,
    "VARCHAR": CharInput,
    "TEXT": TextInput,
    "TIME": TimeInput,
    "UUID": CharInput,
    "PickleText": PythonInput,
    "JsonText": JsonInput,
    "ValueType": ValueTypeInput,
    "TestCaseStatus": EnumTypeInput,
    "TestCaseType": EnumTypeInput,
    "PriorityType": EnumTypeInput,
    "SeverityType": EnumTypeInput,
    "LikelihoodType": EnumTypeInput,
}


class UnknownInput(BaseInput):
    def __init__(self, model, metadata, value):
        self.wid = urwid.Text([metadata.coltype, ("error", " Unkown input type: {}".format(metadata.coltype))])
        self.__super.__init__(self._col_creator(metadata, self.wid))


# For new, unknown, and currently unimplemented column types
class NotImplementedInput(BaseInput):
    def __init__(self, model, metadata, value):
        self.wid = self._not_implemented(metadata)
        self.__super.__init__(self._col_creator(metadata, self.wid))


##### specialized form widgets

class TableItemWidget(urwid.WidgetWrap):
    signals = ["activate"]

    def __init__ (self, modelname):
        self.modelname = modelname
        w = AM(urwid.Text(modelname), 'body', 'focus')
        self.__super.__init__(w)


    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._command_map[key] != 'activate':
            return key
        self._emit('activate')


class ListEntry(urwid.WidgetWrap):
    signals = ["activate"]

    def __init__ (self, w):
        w = AM(w, 'body', 'focus')
        self.__super.__init__(w)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._command_map[key] != 'activate':
            return key
        self._emit('activate')


###### Forms

class Form(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["pushform", "popform"]

    def __init__(self, session=None, modelclass=None, row=None):
        self.session = session
        self.modelclass = modelclass
        if modelclass is not None:
            self.metadata = models.get_metadata_map(modelclass)
        else:
            self.metadata = None
        self.row = row
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        raise NotImplementedError("Override in subclass: return a top-level box widget")

    def get_buttons(self):
        l = [
            AM(urwid.Button("OK", self._ok), 'selectable', 'focus'),
            AM(urwid.Button("Cancel", self._cancel), 'selectable', 'focus'),
            ]
        butgrid = urwid.GridFlow(l, 10, 3, 1, 'center')
        return urwid.Pile([urwid.Divider(), butgrid ], focus_item=1)


    def _subform(self, b):
        subform = get_create_form(session, modelclass)
# XXX

    def _ok(self, b):
        DEBUG("OK pressed")

    def _cancel(self, b):
        DEBUG("Cancel pressed")


class TableForm(Form):

    _EDITABLE_CLASSES = [
        "Address",
        "AttributeType",
        "CapabilityGroup",
        "CapabilityType",
        "Component",
        "Contact",
        "CorporateAttributeType",
        "Corporation",
        "Environment",
        "EnvironmentAttributeType",
        "Equipment",
        "EquipmentCategory",
        "EquipmentModel",
        "FunctionalArea",
        "Interface",
        "Location",
        "LoginAccount",
        "Network",
        "Project",
        "ProjectCategory",
        "ProjectVersion",
        "Requirement",
        "RiskCategory",
        "RiskFactor",
        "Schedule",
        "Software",
        "SoftwareCategory",
        "SoftwareVariant",
        "TestCase",
        "TestEquipment",
        "TestJob",
        "TestSuite",
    ]

    def build(self):
        header = urwid.AttrMap(urwid.Text("Tables"), "subhead")
        self.blist = [TableItemWidget(s) for s in self._EDITABLE_CLASSES]
        for b in self.blist:
            urwid.connect_signal(b, 'activate', self._select)
        listbox = urwid.ListBox(urwid.SimpleListWalker(self.blist))
        return urwid.Frame(urwid.AttrMap(listbox, 'top'), header=header)

    def _select(self, selb):
        for b in self.blist:
            urwid.disconnect_signal(b, 'activate', self._select)
        form = get_list_form(self.session, getattr(models, selb.modelname))
        self._emit("pushform", form)


class GenericListForm(Form):
    # TODO DB paging
    _FORMATS = {
        "BIGINT": ("{!s:>20}", 20),
        "BOOLEAN": ("{!s:5.5s}", 5),
        "CHAR": ("{}", 1),
        "Cidr": ("{!s:>15.15}", 15),
        "DATE": ("{:%Y-%m-%d}", 10),
        "TIMESTAMP": ("{:%Y-%m-%d %H:%M:%S}", 19),
        "FLOAT": ("{:>16.3f}", 20),
        "Inet": ("{!s:>15.15}", 15),
        "INTEGER": ("{!s:>20}", 20),
        "MACADDR": ("{!s:<17.17}", 17),
        "SMALLINT": ("{!s:>10}", 10),
        "VARCHAR": ("{:<30.30}", 30),
        "TEXT": ("{:<30.30}", 30),
        "TIME": ("{:%H:%M:%S}", 8),
        "UUID": ("{:<20.20}", 20),
        "PickleText": ("{!r:25.25}", 25),
        "JsonText": ("{!r:25.25}", 25),
        "RelationshipProperty": ("{!s:15.15}", 15),
    }

    def build(self):
        mapper = models.class_mapper(self.modelclass)
        pkname = str(mapper.primary_key[0].name)
        clsname = self.modelclass.__name__
        q = self.session.query(self.modelclass).order_by(pkname)

        colnames = models.get_rowdisplay(self.modelclass)
        # col headings
        l = [('fixed', 6, urwid.Text(("colhead", pkname))) ]
        for colname in colnames:
            md = self.metadata[colname]
            fmt, width = self._FORMATS.get(md.coltype, ("{!s:10.10}", 10))
            l.append( ('fixed', width, urwid.Text(("colhead", md.colname))) )
        cb = urwid.Button("Create new {}".format(clsname.lower()))
        urwid.connect_signal(cb, 'click', self._create)
        header = urwid.Pile(
                [urwid.Columns([AM(urwid.Text(clsname), "subhead"), AM(cb, "selectable", "focus") ],
                focus_column=1), urwid.Columns(l, dividechars=1)])
        # data
        items = []
        for row in q.all():
            disprow = []
            pk = getattr(row, pkname)
            disprow.append( ('fixed', 6, urwid.Text(str(pk))) )
            for colname in colnames:
                md = self.metadata[colname]
                fmt, width = self._FORMATS.get(md.coltype, ("{!s:10.10}", 10))
                disprow.append( ('fixed', width, urwid.Text(fmt.format(getattr(row, colname)))) )
            lw = ListEntry(urwid.Columns(disprow, dividechars=1))
            urwid.connect_signal(lw, 'activate', self._edit, pk)
            items.append(lw)
        listbox = urwid.ListBox(urwid.SimpleListWalker(items))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header, focus_part="body")

    def _create(self, b):
        cform = get_create_form(self.session, self.modelclass)
        self._emit("pushform", cform)

    def _edit(self, b, pk):
        row = self.session.query(self.modelclass).get(pk)
        eform = get_edit_form(self.session, row)
        self._emit("pushform", eform)

    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            self._w.keypress(size, key)
            return key
        self._w.set_focus("header" if self._w.get_focus() == "body" else "body")


class GenericCreateForm(Form):

    def build(self):
        header = urwid.AttrMap(urwid.Text("Create {}".format(self.modelclass.__name__)), "head")
        formstack = []
        self.formwidgets =[]
        for key in sorted(self.metadata.keys()):
            md = self.metadata[key]
            if md.coltype == "RelationshipProperty":
                wid = RelationshipInput(self.session, self.modelclass, md, md.default)
                wid.colname = md.colname
                formstack.append(wid)
                self.formwidgets.append(wid)
                continue
            typewidget = _TYPE_CREATE_WIDGETS.get(md.coltype, UnknownInput)
            if typewidget is not None:
                wid = typewidget(self.modelclass, md, md.default)
                wid.colname = md.colname
                formstack.append(wid)
                self.formwidgets.append(wid)
            else:
                formstack.append(NotImplementedInput(self.modelclass, md, None))
        formstack.append(self.get_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def _ok(self, b):
        data = {}
        widgets = self.formwidgets
        self.formwidgets = None
        for wid in widgets:
            data[wid.colname] = wid.value
        DEBUG("row data", data)
        dbrow = models.create(self.modelclass)
        update_row(self.session, self.modelclass, dbrow, data)
        try:
            self.session.add(dbrow)
            try: # TODO retry form
                self.session.commit()
            except:
                self.session.rollback()
                raise
        finally:
            self._emit("popform")

    def _cancel(self, b):
        self._emit("popform")



class GenericEditForm(Form):

    def build(self):
        header = urwid.AttrMap(urwid.Text("Edit {}".format(self.modelclass.__name__)), "head")
        formstack = []
        self.formwidgets = []
        for key in sorted(self.metadata.keys()):
            md = self.metadata[key]
            if md.coltype == "RelationshipProperty":
                formstack.append(
                        RelationshipInput(self.session, self.modelclass, md, getattr(self.row, md.colname)))
                continue
            typewidget = _TYPE_CREATE_WIDGETS.get(md.coltype, UnknownInput)
            if typewidget is not None:
                wid = typewidget(self.modelclass, md, getattr(self.row, md.colname))
                wid.colname = md.colname
                formstack.append(wid)
                self.formwidgets.append(wid)
            else:
                formstack.append(NotImplementedInput(self.modelclass, md, getattr(self.row, md.colname)))
        formstack.append(self.get_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def _ok(self, b):
        data = {}
        widgets = self.formwidgets
        self.formwidgets = None
        for wid in widgets:
            data[wid.colname] = wid.value
        update_row(self.session, self.modelclass, self.row, data)
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        self._emit("popform")

    def _cancel(self, b):
        self._emit("popform")



class EquipmentCreateForm(Form):
    pass


class EquipmentEditForm(Form):
    pass



_SPECIAL_CREATE_FORMS = {
#        "Equipment": EquipmentCreateForm,
}

_SPECIAL_EDIT_FORMS = {
#        "Equipment": EquipmentEditForm,
}

_SPECIAL_LIST_FORMS = {
#        "Equipment": EquipmentEditForm,
}

def get_create_form(session, modelclass):
    formclass = _SPECIAL_CREATE_FORMS.get(modelclass.__name__, GenericCreateForm)
    return formclass(session, modelclass)


def get_list_form(session, modelclass):
    formclass = _SPECIAL_LIST_FORMS.get(modelclass.__name__, GenericListForm)
    return formclass(session, modelclass)


def get_edit_form(session, rowobj):
    formclass = _SPECIAL_EDIT_FORMS.get(rowobj.__class__.__name__, GenericEditForm)
    return formclass(session, rowobj.__class__, rowobj)


def update_row(session, modelclass, dbrow, data):
    for metadata in models.get_metadata(modelclass):
        value = data.get(metadata.colname)
        if not value and metadata.nullable:
            value = None
        if metadata.coltype == "RelationshipProperty":
            relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
            if isinstance(value, list):
                if not value:
                    continue
                t = session.query(relmodel).filter(relmodel.id.in_(value)).all()
                if metadata.collection == "MappedCollection":
                    setattr(dbrow, metadata.colname, dict((o.name, o) for o in t))
                else:
                    setattr(dbrow, metadata.colname, t)
            elif value is None:
                if metadata.uselist:
                    if metadata.collection == "MappedCollection":
                        value = {}
                    else:
                        value = []
                setattr(dbrow, metadata.colname, value)
            else:
                related = session.query(relmodel).get(value)
                setattr(dbrow, metadata.colname, related)

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

        elif metadata.coltype == "JsonText":
            if value is None:
                if metadata.nullable:
                    setattr(dbrow, metadata.colname, value)
                else:
                    setattr(dbrow, metadata.colname, "")
            else:
                value = json.loads(value)
                setattr(dbrow, metadata.colname, value)
        else:
            setattr(dbrow, metadata.colname, value)
    return dbrow




#################################
## XXX for trying out experimental stuff

class TestForm(Form):
    def __init__(self):
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        self.edit = urwid.Edit("Edit me: ", multiline=True)
        header = urwid.AttrMap(urwid.Text("Edit this text"), "head")
        buts = self.get_buttons()
        listbox = urwid.ListBox(urwid.SimpleListWalker([self.edit, buts]))
        frm = urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)
        ovr = urwid.Frame(urwid.Text("Inside frame"))
        urwid.Overlay(ovr, frm, "center", 80, "middle", 24)
        return frm

    def run(self):
        loop = urwid.MainLoop(self, PALETTE, unhandled_input=self.unhandled_input, pop_ups=True,
                event_loop=urwid.GLibEventLoop())
        loop.run()

    def unhandled_input(self, k):
        if k == "esc":
            raise urwid.ExitMainLoop()
        DEBUG("unhandled key:", k)


### for debugging, can't just print to the same screen. Open a new terminal for printing.

import os

_debugfile = None

def _close_debug(fo):
    fo.close()

def DEBUG(*obj):
    """Open a terminal emulator and write messages to it for debugging."""
    global _debugfile
    if _debugfile is None:
        import atexit
        masterfd, slavefd = os.openpty()
        pid = os.fork()
        if pid: # parent
            os.close(masterfd)
            _debugfile = os.fdopen(slavefd, "w+", 0)
            atexit.register(_close_debug, _debugfile)
        else: # child
            os.close(slavefd)
            os.execlp("urxvt", "urxvt", "-pty-fd", str(masterfd))
    print(datetime.now(), ":", ", ".join(map(repr, obj)), file=_debugfile)



def _test(argv):
    app = TestForm()
    print(app.run())

if __name__ == "__main__":
    import sys
    _test(sys.argv)
