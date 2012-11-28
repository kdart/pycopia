#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab:fenc=utf-8
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

import sys
import json
from datetime import datetime

import urwid

from sqlalchemy.exc import IntegrityError

from pycopia import ipv4
from pycopia.aid import NULL, Enum
from pycopia.db import types
from pycopia.db import models

DEBUG = NULL

PALETTE = [
    ('body','default', 'default'),
    ('popup','black','light gray', 'standout'),
    ('top','default', 'default'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('enumbuttn','black','yellow'),
    ('buttn','black','dark cyan'),
    ('formbuttn','black','dark green'),
    ('formbuttnf','white','dark blue','bold'),
    ('buttnimportant','black','dark magenta', ("bold", "standout")),
    ('buttnimportantf','white','dark magenta', ("bold", "standout")),
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
    ('focus','white','default','bold'),
    ('focustext','light gray','dark blue'),
    ('foot', 'light gray', 'black'),
    ('head', 'white', 'black', 'standout'),
    ('formhead', 'dark blue', 'light gray', 'standout'),
    ('subhead', 'yellow', 'black', 'standout'),
    ('important','light magenta','default',('standout','underline')),
    ('key', "black", 'light cyan', 'underline'),
    ('collabel','light gray','black'),
    ('coldivider','light blue','black'),
    ('notnulllabel','light magenta','black'),
    ('selectable','black', 'dark cyan'),
    ('notimplemented', 'dark red', 'black'),
    ('deleted', 'dark red', 'black'),
    ('title', 'white', 'black', 'bold'),
    ('colhead', 'yellow', 'black', 'default'),
]

UP = Enum(1, "UP")
DOWN = Enum(2, "DOWN")


### shorthand notation

AM = urwid.AttrMap


class InputDivider(urwid.WidgetWrap):
    def __init__(self, legend):
        wid = urwid.Columns([
                (25, AM(urwid.Text("{}:".format(legend), align="left"), "coldivider")),
                 urwid.Divider(u"-")], dividechars=1)
        self.__super.__init__(wid)


class BaseInput(urwid.WidgetWrap):
    signals = ["update", "pushform", "message"]

    def _col_creator(self, metadata, widget, legend=None):
        return urwid.Columns([
                (25, AM(urwid.Text(legend or metadata.colname, align="right"),
                            "collabel" if (metadata.nullable or metadata.uselist) else "notnulllabel")),
                 widget], dividechars=1)

    def message(self, msg):
        self._emit("message", msg)

    def _message(self, b, msg): # callback form
        self._emit("message", msg)

    def _not_implemented(self, metadata):
        return urwid.Text([metadata.coltype, ("notimplemented", " Not implemented yet")])

    @property
    def value(self):
        return None

    def validate(self):
        return True


class BooleanInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        self.wid = urwid.CheckBox(metadata.colname, state=value)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return bool(self.wid.get_state())


class IntInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"0" if value is None else str(value)
        self.wid = urwid.IntEdit(default=val)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.value()

    def validate(self):
        try:
            long(self.wid.value())
        except ValueError:
            return False
        return True


class FloatInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"0.0" if value is None else str(value)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text

    def validate(self):
        try:
            float(self.wid.edit_text)
        except ValueError:
            return False
        return True


class IntervalInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value)
        legend = legend or "{} (time interval)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text


class CharInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.nullable = metadata.nullable
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        if not self.wid.edit_text and self.nullable:
            return None
        return self.wid.edit_text

    def validate(self):
        return self.nullable or bool(self.wid.edit_text)


class TextInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else value
        self.nullable = metadata.nullable
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        if not self.wid.edit_text and self.nullable:
            return None
        return self.wid.edit_text

    def validate(self):
        return self.nullable or bool(self.wid.edit_text)


class PythonInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else repr(value)
        self.nullable = metadata.nullable
        legend = legend or "{} (Python)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=True)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        if not self.wid.edit_text and self.nullable:
            return None
        return self.wid.edit_text


class JsonInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else json.dumps(value, ensure_ascii=False)
        self.nullable = metadata.nullable
        legend = legend or "{} (JSON)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=True, allow_tab=True)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        if not self.wid.edit_text and self.nullable:
            return None
        return self.wid.edit_text


class CidrInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value.CIDR)
        legend = legend or "{} (x.x.x.0/m)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text

    def validate(self):
        try:
            ipv4.IPv4(self.wid.edit_text)
        except ValueError:
            return False
        return True


class InetInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value.CIDR)
        legend = legend or "{} (x.x.x.x/m)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text

    def validate(self):
        try:
            ipv4.IPv4(self.wid.edit_text)
        except ValueError:
            return False
        return True


class MACInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value)
        legend = legend or "{} (xx:xx:xx:xx:xx:xx)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text


class DateInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value)
        legend = legend or "{} (date)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text


class TimeInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value)
        legend = legend or "{} (time)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        return self.wid.edit_text


class TimestampInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        val = u"" if value is None else str(value)
        legend = legend or "{} (date time)".format(metadata.colname)
        self.wid = urwid.Edit(edit_text=val, multiline=False, allow_tab=False)
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

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
            glist.append(AM(b, 'enumbuttn','buttnf'))
        # set the right value
        for b in blist:
            if b.value == value:
                b.state = True
        self.wid = urwid.GridFlow(glist, maxl+4, 1, 0, 'left')
        self.blist = blist
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        for b in self.blist:
            if b.state is True:
                return b.value


class EnumTypeInput(BaseInput):
    def __init__(self, model, metadata, value, legend=None):
        blist = []
        glist = []
        maxl = 0
        enumtype = getattr(types, metadata.coltype)
        if value is None:
            value = enumtype.get_default()
        for num, name in enumtype.get_choices():
            maxl = max(maxl, len(name))
            b = urwid.RadioButton(blist, name, False, user_data=num)
            b.value = num
            glist.append(AM(b, 'enumbuttn','buttnf'))
        # set the right value
        for b in blist:
            if b.value == value:
                b.state = True
        self.wid = urwid.GridFlow(glist, maxl+4, 1, 0, 'left')
        self.blist = blist
        self.__super.__init__(self._col_creator(metadata, self.wid, legend))

    @property
    def value(self):
        for b in self.blist:
            if b.state is True:
                return b.value


# TODO factor this out to multiple types of relation input.
class RelationshipInput(BaseInput):
    def __init__(self, session, model, metadata, value, legend=None):
        self.session = session
        self.modelclass = model
        self.metadata = metadata
        if value is None:
            if metadata.uselist:
                self.dbvalue = {}
            else:
                self.dbvalue = None
        else:
            if metadata.uselist:
                self.dbvalue  = dbvalue = dict()
                if metadata.collection == "MappedCollection":
                    for v in value.values():
                        dbvalue[v.id] = v
                else:
                    for v in value:
                        dbvalue[v.id] = v
            else:
                self.dbvalue = value
        label = self._get_top_label()
        wid = self._get_top_button(label)
        self.__super.__init__(self._col_creator(metadata, wid, legend))

    @property
    def value(self):
        if self.metadata.uselist:
            return self.dbvalue.values() # list of foriegn key ids
        else:
            return self.dbvalue

    def validate(self):
        if self.metadata.uselist:
            return True
        else:
            if not self.metadata.nullable and self.dbvalue is None:
                return False
            return True

    def _get_top_label(self):
        if self.metadata.uselist:
            label = "{{{}}} (Edit)".format(", ".join(str(o) for o in self.dbvalue.values()))
        else:
            label = "{} (Edit)".format(self.dbvalue)
        return label

    def _get_top_button(self, label):
        but = urwid.Button(label)
        urwid.connect_signal(but, 'click', self._expand)
        if not self.metadata.nullable and not self.metadata.uselist and not self.dbvalue:
            return AM(but, "buttnimportant", "buttnimportantf")
        else:
            return AM(but, "formbuttn", "formbuttnf")

    def _create_relation_input(self):
        choices = dict(models.get_choices(self.session, self.modelclass, self.metadata.colname, None))
        addnew = urwid.Button("Add New")
        urwid.connect_signal(addnew, 'click', self._add_new_related)
        # Cancel
        canc = urwid.Button("Cancel")
        urwid.connect_signal(canc, 'click', self._cancel)
        butcol = urwid.Columns([AM(addnew, "buttn", "buttnf"), AM(canc, "buttn", "buttnf")])
        wlist = [butcol]
        if self.metadata.nullable:
            entry = ListEntry(urwid.Text("None (remove)"))
            urwid.connect_signal(entry, 'activate', self._single_select)
            wlist.append(entry)
        for pk, cname in choices.items():
            entry = ListEntry(urwid.Text(cname))
            urwid.connect_signal(entry, 'activate', self._single_select, pk)
            wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), 9)

    def _expand(self, b):
        if self.metadata.uselist:
            newform = MultiselectListForm(self)
            urwid.connect_signal(newform, 'popform', self._pop_multiform)
            urwid.connect_signal(newform, 'message', self._message)
            self._emit("pushform", newform)
        else:
            self.old_dbvalue = self.dbvalue
            newwid = self._create_relation_input()
            self._w.widget_list[1] = newwid

    def _pop_multiform(self, form, dbvalue=NULL):
        if dbvalue is not NULL:
            self.dbvalue = dbvalue
        self._w.widget_list[1] = self._get_top_button(self._get_top_label())

    def _cancel(self, b):
        self.dbvalue = self.old_dbvalue
        self.old_dbvalue = None
        self._w.widget_list[1] = self._get_top_button(self._get_top_label())

    def _single_select(self, le, pk=None):
        if pk is not None:
            self.dbvalue = self._get_related_row(pk)
        else:
            self.dbvalue = None
        self.old_dbvalue = None
        self._w.widget_list[1] = self._get_top_button(self._get_top_label())

    def _add_new_related(self, b):
        colname = self.metadata.colname
        relmodel = getattr(self.modelclass, colname).property.mapper.class_
        newform = get_create_form(self.session, relmodel)
        urwid.connect_signal(newform, 'popform', self._popsubform)
        urwid.connect_signal(newform, 'message', self._message)
        self._emit("pushform", newform)

    def _message(self, b, msg):
        self._emit("message", msg)

    def _popsubform(self, form, pkval):
        if pkval is not None:
            self.dbvalue = self._get_related_row(pkval)
        self._w.widget_list[1] = self._get_top_button(self._get_top_label())

    def _get_related_row(self, pk):
        relmodel = getattr(self.modelclass, self.metadata.colname).property.mapper.class_
        return self.session.query(relmodel).get(pk)


class AttributeInput(BaseInput):
    def __init__(self, session, model, metadata, row, legend=None):
        self.session = session
        self.modelclass = model
        self.metadata = metadata
        self.row = row
        wid = self.build()
        self.__super.__init__(self._col_creator(metadata, wid, legend))

    def build(self):
        wlist = []
        addnew = urwid.Button("Add")
        urwid.connect_signal(addnew, 'click', self._add_new_attribute)
        addnew = urwid.AttrWrap(addnew, 'selectable', 'butfocus')
        wlist.append(addnew)
        for attrib in getattr(self.row, self.metadata.colname): # list-like attribute
            entry = ListEntry(urwid.Columns(
                    [(30, urwid.Text(str(attrib.type))),
                     urwid.Text(unicode(attrib.value).encode("utf-8"))]))
            entry.attrname = attrib.type.name
            urwid.connect_signal(entry, 'activate', self._edit_attribute)
            urwid.connect_signal(entry, 'delete', self._delete)
            wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), max(7, len(wlist)+2))

    # edit attrib
    def _edit_attribute(self, entry):
        value = self.row.get_attribute(self.session, entry.attrname)
        frm = AttributeEditForm(entry.attrname, unicode(value).encode("utf-8"))
        urwid.connect_signal(frm, 'ok', self._edit_ok, entry)
        urwid.connect_signal(frm, 'cancel', self._edit_cancel, entry)
        self._saveentryval = entry._w
        entry._w = frm

    def _edit_cancel(self, form, entry):
        urwid.disconnect_signal(form, 'ok', self._edit_ok, entry)
        urwid.disconnect_signal(form, 'cancel', self._edit_cancel, entry)
        saveentry = self._saveentryval
        del self._saveentryval
        entry._w = saveentry

    def _edit_ok(self, form, newtext, entry):
        try:
            self.row.update_attribute(self.session, entry.attrname, newtext)
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
            return
        urwid.disconnect_signal(form, 'ok', self._edit_ok, entry)
        urwid.disconnect_signal(form, 'cancel', self._edit_cancel, entry)
        saveentry = self._saveentryval
        del self._saveentryval
        newval = self.row.get_attribute(self.session, entry.attrname)
        saveentry.base_widget[1].base_widget.set_text(unicode(newval).encode("utf-8"))
        entry._w = saveentry

    # create attrib
    def _add_new_attribute(self, b):
        frm = AttributeAddForm(self.session, self.modelclass)
        urwid.connect_signal(frm, 'ok', self._add_new_attribute_ok)
        urwid.connect_signal(frm, 'cancel', self._add_new_attribute_cancel)
        listbox = self._w.contents[1][0].base_widget
        listbox.body.append(frm) # listwalker
        listbox.set_focus(len(listbox.body)-1)

    def _add_new_attribute_cancel(self, dlg):
        listbox = self._w.contents[1][0].base_widget
        frm = listbox.body.pop()
        listbox.set_focus(0)

    def _add_new_attribute_ok(self, form, data):
        attrname, attrvalue = data
        try:
            self.row.set_attribute(self.session, attrname, attrvalue)
        except IntegrityError:
            self.session.rollback()
            DEBUG(ex.__name__, val)
            self._emit("message", "Cannot add, attribute already exists.")
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
            return
        old, attr = self._w.contents[1] # attr e.g. (wid, ("given", 25, False))
        self._w.contents[1] = (self.build(), attr)

    # delete attrib
    def _delete(self, listentry):
        urwid.disconnect_signal(listentry, 'activate', self._edit_attribute)
        urwid.disconnect_signal(listentry, 'delete', self._delete)
        text, attr = listentry._w.base_widget[0].get_text()
        dlg = DeleteDialog(text)
        urwid.connect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.connect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        self._oldw = listentry._w
        listentry._w = dlg

    def _delete_ok(self, dlg, listentry):
        listbox = self._w.contents[1][0].base_widget
        assert type(listbox) is urwid.ListBox
        listbox.body.remove(listentry)
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        del self._oldw
        # now actually delete the attribute
        self.row.del_attribute(self.session, listentry.attrname)

    def _delete_cancel(self, dlg, listentry):
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        listentry._w = self._oldw
        del self._oldw
        # restore sig handlers
        urwid.connect_signal(listentry, 'activate', self._edit_attribute)
        urwid.connect_signal(listentry, 'delete', self._delete)


class TestEquipmentInput(BaseInput):
    def __init__(self, session, model, metadata, row, legend=None):
        self.session = session
        self.modelclass = model
        self.metadata = metadata
        self.environmentrow = row # an Environment row
        wid = self.build()
        self.__super.__init__(self._col_creator(metadata, wid, legend))

    def build(self):
        addnew = urwid.Button("Add")
        urwid.connect_signal(addnew, 'click', self._add_new_testequipment)
        addnew = urwid.AttrWrap(addnew, 'selectable', 'butfocus')
        wlist = [addnew]
        for te in getattr(self.environmentrow, self.metadata.colname): # list-like attribute
            entry = ListEntry( urwid.Text(self._stringify_te(te)))
            urwid.connect_signal(entry, 'activate', self._edit_testequipment)
            urwid.connect_signal(entry, 'delete', self._delete_testequipment)
            entry.testequipment = te
            if te.UUT:
                wlist.insert(1, entry)
            else:
                wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), max(7, len(wlist)+2))

    def _stringify_te(self, te):
        if te.roles:
            ts = u"{}  roles: {}".format(te, u", ".join(unicode(role) for role in te.roles))
        else:
            ts = unicode(te)
        return ts.encode("utf-8")

    def _add_new_testequipment(self, b):
        frm = TestEquipmentAddForm(self.session)
        urwid.connect_signal(frm, 'ok', self._add_new_testequipment_ok)
        urwid.connect_signal(frm, 'cancel', self._add_new_testequipment_cancel)
        self._emit("pushform", frm)

    def _add_new_testequipment_ok(self, frm, data):
        eq, roles, uut = data
        dbrow = models.create(models.TestEquipment, environment=self.environmentrow, equipment=eq, UUT=uut, roles=roles)
        self.session.add(dbrow)
        try:
            self.session.commit()
        except:
            self.session.rollback()
            ex, val, tb = sys.exc_info()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        entry = ListEntry(urwid.Text(self._stringify_te(dbrow)))
        urwid.connect_signal(entry, 'activate', self._edit_testequipment)
        urwid.connect_signal(entry, 'delete', self._delete_testequipment)
        entry.testequipment = dbrow
        listbox = self._w.contents[1][0].base_widget
        listbox.body.append(entry)
        urwid.disconnect_signal(frm, 'ok', self._add_new_testequipment_ok)
        urwid.disconnect_signal(frm, 'cancel', self._add_new_testequipment_cancel)
        frm._emit("popform")

    def _add_new_testequipment_cancel(self, frm):
        urwid.disconnect_signal(frm, 'ok', self._add_new_testequipment_ok)
        urwid.disconnect_signal(frm, 'cancel', self._add_new_testequipment_cancel)
        frm._emit("popform")

    # editing
    def _edit_testequipment(self, entry):
        frm = TestEquipmentEditForm(self.session, entry.testequipment)
        urwid.connect_signal(frm, 'ok', self._edit_testequipment_ok, entry)
        urwid.connect_signal(frm, 'cancel', self._edit_testequipment_cancel, entry)
        self._emit("pushform", frm)

    def _edit_testequipment_cancel(self, form, entry):
        try:
            self.session.rollback()
        except:
            ex, val, tb = sys.exc_info()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        urwid.disconnect_signal(form, 'ok', self._edit_testequipment_ok, entry)
        urwid.disconnect_signal(form, 'cancel', self._edit_testequipment_cancel, entry)
        form._emit("popform")

    def _edit_testequipment_ok(self, form, entry):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            ex, val, tb = sys.exc_info()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        entry._w.base_widget.set_text(self._stringify_te(entry.testequipment))
        urwid.disconnect_signal(form, 'ok', self._edit_testequipment_ok, entry)
        urwid.disconnect_signal(form, 'cancel', self._edit_testequipment_cancel, entry)
        form._emit("popform")

    # deleting
    def _delete_testequipment(self, listentry):
        urwid.disconnect_signal(listentry, 'activate', self._edit_testequipment)
        urwid.disconnect_signal(listentry, 'delete', self._delete_testequipment)
        text, attr = listentry._w.base_widget.get_text()
        dlg = DeleteDialog(text)
        urwid.connect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.connect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        self._oldw = listentry._w
        listentry._w = dlg

    def _delete_ok(self, dlg, listentry):
        listbox = self._w.contents[1][0].base_widget
        assert type(listbox) is urwid.ListBox
        listbox.body.remove(listentry)
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        del self._oldw
        try:
            self.session.delete(listentry.testequipment)
            self.session.commit()
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        listentry.testequipment = None
        urwid.disconnect_signal(listentry, 'activate', self._edit_testequipment)
        urwid.disconnect_signal(listentry, 'delete', self._delete_testequipment)

    def _delete_cancel(self, dlg, listentry):
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        listentry._w = self._oldw
        del self._oldw
        # restore sig handlers
        urwid.connect_signal(listentry, 'activate', self._edit_testequipment)
        urwid.connect_signal(listentry, 'delete', self._delete_testequipment)


class EquipmentInterfaceInput(BaseInput):
    def __init__(self, session, model, metadata, row, legend=None):
        self.session = session
        self.modelclass = model
        self.metadata = metadata
        self.equipmentrow = row # an Equipment row
        wid = self.build()
        self.__super.__init__(self._col_creator(metadata, wid, legend))

    def build(self):
        addnew = urwid.Button("Add")
        urwid.connect_signal(addnew, 'click', self._add_new_interface)
        addnew = urwid.AttrWrap(addnew, 'selectable', 'butfocus')
        attach = urwid.Button("Attach existing")
        urwid.connect_signal(attach, 'click', self._attach_interface)
        attach = urwid.AttrWrap(attach, 'selectable', 'butfocus')
        wlist = [urwid.Columns([addnew, attach], dividechars=1)]
        for intf in self.equipmentrow.interfaces.values():
            wlist.append(self._get_intf_entry(intf))
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), max(7, len(wlist)+2))

    def _get_intf_entry(self, intf):
        entry = ListEntry(urwid.Text(unicode(intf).encode("utf-8")))
        urwid.connect_signal(entry, 'activate', self._edit_interface)
        urwid.connect_signal(entry, 'delete', self._delete_interface)
        entry.interface = intf
        return entry

    def _delete_interface(self, listentry):
        urwid.disconnect_signal(listentry, 'activate', self._edit_interface)
        urwid.disconnect_signal(listentry, 'delete', self._delete_interface)
        text, attr = listentry._w.base_widget.get_text()
        dlg = DeleteDialog(text)
        urwid.connect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.connect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        self._oldw = listentry._w
        listentry._w = dlg

    def _delete_ok(self, dlg, listentry):
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        del self._oldw
        self.session.delete(listentry.interface)
        try:
            self.session.commit()
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        else:
            listbox = self._w.contents[1][0].base_widget
            assert type(listbox) is urwid.ListBox
            listbox.body.remove(listentry)
            listentry.interface = None
            urwid.disconnect_signal(listentry, 'activate', self._edit_interface)
            urwid.disconnect_signal(listentry, 'delete', self._delete_interface)

    def _delete_cancel(self, dlg, listentry):
        urwid.disconnect_signal(dlg, 'ok', self._delete_ok, listentry)
        urwid.disconnect_signal(dlg, 'cancel', self._delete_cancel, listentry)
        listentry._w = self._oldw
        del self._oldw
        # restore sig handlers
        urwid.connect_signal(listentry, 'activate', self._edit_interface)
        urwid.connect_signal(listentry, 'delete', self._delete_interface)

    def _add_new_interface(self, b):
        frm = get_create_form(self.session, models.Interface)
        urwid.connect_signal(frm, 'message', self._message)
        urwid.connect_signal(frm, 'popform', self._add_complete)
        self._emit("pushform", frm)

    def _add_complete(self, form, pkval=None):
        urwid.disconnect_signal(form, 'popform', self._add_complete)
        if pkval is not None:
            intf = self.session.query(models.Interface).get(pkval)
            if intf.name in self.equipmentrow.interfaces:
                self._emit("message", "Interface with that name already exists. Not adding.")
            else:
                self.equipmentrow.interfaces.set(intf)
                try:
                    self.session.commit()
                except:
                    ex, val, tb = sys.exc_info()
                    self.session.rollback()
                    DEBUG(ex.__name__, val)
                    self._emit("message", "{}: {}".format(ex.__name__, val))
                else:
                    listbox = self._w.contents[1][0].base_widget
                    assert type(listbox) is urwid.ListBox
                    entry = self._get_intf_entry(intf)
                    listbox.body.append(entry)
        form._emit("popform")

    def _edit_interface(self, listentry):
        frm = get_edit_form(self.session, listentry.interface)
        urwid.connect_signal(frm, 'message', self._message)
        urwid.connect_signal(frm, 'popform', self._edit_complete, listentry)
        self._emit("pushform", frm)

    def _edit_complete(self, form, pkval, listentry):
        urwid.disconnect_signal(form, 'popform', self._edit_complete, listentry)
        urwid.disconnect_signal(form, 'message', self._message)
        listentry._w.base_widget.set_text(unicode(listentry.interface).encode("utf-8"))
        #self._invalidate()
        form._emit("popform")

    def _attach_interface(self, b):
        frm = InterfaceAttachForm(self.session, self.equipmentrow)
        urwid.connect_signal(frm, 'popform', self._add_complete)
        self._emit("pushform", frm)


### Misc. dialogs

class DeleteDialog(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel"]

    def __init__(self, text):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        dlg = urwid.Columns([urwid.Text(text),
                AM(urwid.Text("Delete?"), "important"),
                (10, ok),
                (10, cancel)], dividechars=1, focus_column=2)
        self.__super.__init__(dlg)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return self._w.keypress(size, key)

    def _ok(self, b):
        self._emit("ok")

    def _cancel(self, b):
        self._emit("cancel")


class AttributeEditForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel"]

    def __init__(self, name, text):
        wid = self.build(name, text)
        self.__super.__init__(wid)

    def build(self, name, text):
        ls = urwid.Text(name)
        te = urwid.Edit(edit_text=text, multiline=True, allow_tab=True)
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        return urwid.Columns([ls, ("weight", 2, te), (10, ok), (10, cancel)], dividechars=1, focus_column=1)

    def _ok(self, b):
        widget_list = self._w.widget_list
        data = widget_list[1].get_text()[0]
        self._emit("ok", data)

    def _cancel(self, b):
        self._emit("cancel")


class AttributeAddForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel"]

    def __init__(self, session, model):
        self.session = session
        self.modelclass = model
        self._attribute_types = dict([(row.name, row) for row in session.query(model.get_attribute_class())])
        wid = self.build()
        self.__super.__init__(wid)

    def get_form_buttons(self):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        return ok, cancel

    def build(self):
        choices = sorted(self._attribute_types.keys())
        ls = ListScrollSelector(choices)
        urwid.connect_signal(ls, 'change', self._update_desc)
        ls = AM(ls, "selectable", "butfocus")
        te = urwid.Edit(edit_text=u"", multiline=True, allow_tab=True)
        ok, cancel = self.get_form_buttons()
        cols = urwid.Columns([ls, ("weight", 2, te), (10, ok), (10, cancel)], dividechars=1, focus_column=0)
        self.descw = urwid.Text(self._attribute_types[choices[0]].description)
        return urwid.Pile([cols, self.descw])

    def _update_desc(self, selector):
        atype = self._attribute_types[selector.value]
        self.descw.set_text("{} ({})".format(atype.description, atype.value_type))

    def _ok(self, b):
        widget_list = self._w.widget_list[0].widget_list
        data = (widget_list[0].base_widget.value, widget_list[1].get_text()[0] )
        self._emit("ok", data)

    def _cancel(self, b):
        self._emit("cancel")


class TestEquipmentAddForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel", "popform", "message"]

    def __init__(self, session):
        self.session = session
        self._roles = list(session.query(models.SoftwareCategory).order_by("name"))
        self._eq = None
        self._uut = False
        self._selected = []
        wid = self.build()
        self.__super.__init__(wid)

    def get_form_buttons(self):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        return ok, cancel

    def build(self):
        self._showeq = urwid.Text(u"")
        eqi = self._create_equipment_input()
        maxlen = 0
        uutcb = urwid.CheckBox(u"DUT/UUT", state=False)
        urwid.connect_signal(uutcb, 'change', self._uut_select)
        blist = [AM(uutcb, "important")]
        for role in self._roles:
            label = str(role)
            maxlen = max(len(label), maxlen)
            but = urwid.CheckBox(str(role), state=False)
            urwid.connect_signal(but, 'change', self._multi_select, role)
            blist.append(but)
        roleboxes = urwid.Padding(urwid.GridFlow(blist, maxlen+4, 1, 0, "left"))
        # buttons
        ok, cancel = self.get_form_buttons()
        buts = urwid.Columns([(10, ok), (10, cancel)], dividechars=1, focus_column=0)
        return urwid.ListBox(urwid.SimpleListWalker([eqi, AM(self._showeq, "flagged"), roleboxes, buts]))

    def _create_equipment_input(self):
        choices = self.session.query(models.Equipment).order_by("name")
        wlist = []
        for row in choices:
            entry = ListEntry(urwid.Text(row.name))
            urwid.connect_signal(entry, 'activate', self._eq_select, row)
            wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))
        return urwid.BoxAdapter(urwid.LineBox(listbox), 9)

    def _eq_select(self, entry, row):
        self._showeq.set_text(row.name)
        self._eq = row
        self._w.focus_position = 2

    def _uut_select(self, b, newstate):
        self._uut = newstate

    def _multi_select(self, b, newstate, role):
        if newstate is True:
            self._selected.append(role)
        else:
            self._selected.remove(role)

    def _ok(self, b):
        data = (self._eq, self._selected, self._uut)
        self._eq = None
        self._selected = None
        self._emit("ok", data)

    def _cancel(self, b):
        self._emit("cancel")


class TestEquipmentEditForm(urwid.WidgetWrap):
    # For usability we only edit the roles. Otherwise, delete and re-add.
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel", "popform", "message"]

    def __init__(self, session, testequipment):
        self.session = session
        self._roles = list(session.query(models.SoftwareCategory).order_by("name"))
        self._testequipment = testequipment
        wid = self.build()
        self.__super.__init__(wid)

    def get_form_buttons(self):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        return ok, cancel

    def build(self):
        showeq = urwid.Text(self._testequipment.equipment.name)
        maxlen = 0
        uutcb = urwid.CheckBox(u"DUT/UUT", state=self._testequipment.UUT)
        urwid.connect_signal(uutcb, 'change', self._uut_select)
        blist = [AM(uutcb, "important")]
        for role in self._roles:
            label = str(role)
            maxlen = max(len(label), maxlen)
            state = role in self._testequipment.roles
            but = urwid.CheckBox(str(role), state=state)
            urwid.connect_signal(but, 'change', self._multi_select, role)
            blist.append(but)
        roleboxes = urwid.Padding(urwid.GridFlow(blist, maxlen+4, 1, 0, "left"))
    #    # buttons
        ok, cancel = self.get_form_buttons()
        buts = urwid.Columns([(10, ok), (10, cancel)], dividechars=1, focus_column=0)
        div = urwid.Divider()
        return urwid.ListBox(urwid.SimpleListWalker([AM(showeq, "flagged"), div, roleboxes, div, buts]))

    def _uut_select(self, b, newstate):
        self._testequipment.UUT = newstate

    def _multi_select(self, b, newstate, role):
        if newstate is True:
            self._testequipment.roles.append(role)
        else:
            self._testequipment.roles.remove(role)

    def _ok(self, b):
        self._emit("ok")

    def _cancel(self, b):
        self._emit("cancel")


class InterfaceAttachForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["popform", "message"]

    def __init__(self, session, equipment):
        self.session = session
        self._equipment = equipment
        wid = self.build()
        self.__super.__init__(wid)

    def build(self):
        wlist = []
        entry = ListEntry(urwid.Text("None (cancel)"))
        urwid.connect_signal(entry, 'activate', self._cancel)
        wlist.append(entry)
        for intf in models.Interface.select_unattached(self.session):
            wlist.append(self._get_intf_entry(intf))
        return urwid.ListBox(urwid.SimpleListWalker(wlist))

    def _get_intf_entry(self, intf):
        entry = ListEntry(urwid.Text(unicode(intf).encode("utf-8")))
        urwid.connect_signal(entry, 'activate', self._sel_interface)
        entry.interface = intf
        return entry

    def _cancel(self, entry):
        self._emit("popform", None)

    def _sel_interface(self, entry):
        intf = entry.interface
        del entry.interface
        self._emit("popform", intf.id)


# extra widgets

class FilterInput(urwid.WidgetWrap):
    signals = ["change"]
    _sizing = frozenset(['flow'])
#    UPARR=u"↑"
#    DOWNARR=u"↓"

    DIRECTION = {
        UP: urwid.SelectableIcon(u"↑", 0),
        DOWN: urwid.SelectableIcon(u"↓", 0),
    }
    #reserve_columns = 1

    def __init__(self):
        self._edit = SimpleEdit()
        self._direction = UP
        wid = urwid.Columns([self._edit, ("fixed", 1, FilterInput.DIRECTION[self._direction])])
        self.__super.__init__(wid)

    def keypress(self, size, key):
        key = self._w.keypress(size, key)
        if key is not None:
            cmd =  self._command_map[key]
            if cmd == "activate":
                self._emit("change")
                return None
            else:
                return key
    @property
    def value(self):
        return self._edit._edit_text, self._direction



class SimpleEdit(urwid.Edit):
    signals = ["change"]

    DIRECTION = {
        UP: urwid.SelectableIcon(u"↑", 0),
        DOWN: urwid.SelectableIcon(u"↓", 0),
    }
    def __init__(self):
        self.__super.__init__(u"", u"", multiline=False)

    def keypress(self, size, key):
        key = self.__super.keypress(size, key)
        if key is not None:
            cmd =  self._command_map[key]
            if cmd == "activate":
                self._emit("change")
                return None
            else:
                return key

    def set_edit_text(self, text):
        self._edit_text = text
        if self.edit_pos > len(text):
            self.edit_pos = len(text)
        self._invalidate()

    @property
    def value(self):
        return self._edit_text



class ListScrollSelector(urwid.Widget):
    _selectable = True
    _sizing = frozenset(['flow'])
    signals = ["click", "change"]
    UPARR=u"↑"
    DOWNARR=u"↓"

    def __init__(self, choicelist):
        self.__super.__init__()
        self._list = choicelist
        self._prefix = ""
        self._max = len(choicelist)
        assert self._max > 0, "Need list with at least one element"
        self._index = 0
        self.set_text(self._list[self._index])
        maxwidth = reduce(lambda c,m: max(c,m), map(lambda o: len(str(o)), choicelist), 0)
        self._fmt = u"{} {{:{}.{}s}} {}".format(self.UPARR, maxwidth, maxwidth, self.DOWNARR)

    def keypress(self, size, key):
        cmd =  self._command_map[key]
        if cmd == 'cursor up':
            self._prefix = ""
            self._index = (self._index - 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == 'cursor down':
            self._prefix = ""
            self._index = (self._index + 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == "activate":
            self._emit("click")
        elif key == "backspace":
            self._prefix = self._prefix[:-1]
        elif len(key) == 1 and key.isalnum():
            self._prefix += key
            i = self.prefix_index(self._list, self._prefix, self._index + 1)
            if i is not None:
                self._index = i
                self.set_text(self._list[i])
        else:
            return key

    @staticmethod
    def prefix_index(thelist, prefix, index=0):
        while index < len(thelist):
            if thelist[index].startswith(prefix):
                return index
            index += 1
        return None

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        (maxcol,) = size
        text = self._fmt.format(self._text).encode("utf-8")
        c = urwid.TextCanvas([text], maxcol=maxcol)
        c.cursor = self.get_cursor_coords(size)
        return c

    def set_text(self, text):
        self._text = text
        self._invalidate()
        self._emit("change")

    def get_cursor_coords(self, size):
        return None

    @property
    def value(self):
        return self._list[self._index]



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
    "INTERVAL": IntervalInput,
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
    signals = ["activate", "delete"]

    def __init__ (self, w):
        w = AM(w, 'body', 'focus')
        self.__super.__init__(w)

    def selectable(self):
        return True

    def keypress(self, size, key):
        try:
            if self._w.keypress(size, key) is None:
                return
        except AttributeError:
            pass
        if self._command_map[key] != 'activate':
            if key == "delete":
                self._emit('delete')
                return None
            else:
                return key
        self._emit('activate')


###### Forms

class MultiselectListForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["popform", "message"]

    def __init__(self, relationinput):
        self.session = relationinput.session
        self.metadata = relationinput.metadata
        self.modelclass = relationinput.modelclass
        self.currentvalue = relationinput.dbvalue.copy()
        self.old_dbvalue = relationinput.dbvalue.copy()
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        # buttons
        done = urwid.Button("Done")
        urwid.connect_signal(done, 'click', self._done_multiselect)
        done = urwid.AttrWrap(done, 'selectable', 'butfocus')
        add = urwid.Button("Add New")
        urwid.connect_signal(add, 'click', self._add_new)
        add = urwid.AttrWrap(add, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = urwid.AttrWrap(cancel, 'selectable', 'butfocus')
        # footer and header
        footer = urwid.GridFlow([done, add, cancel], 15, 3, 1, 'center')
        header = urwid.Padding(urwid.Text(
            ("popup", "Select multiple items. Tab to button box to select buttons. Arrow keys move selection.")))
        listbox = self._build_list()
        return urwid.Frame(listbox, header=header, footer=footer, focus_part="body")

    def _build_list(self):
        choices = get_related_choices(self.session, self.modelclass, self.metadata, None)
        choices.update(self.currentvalue)
        wlist = []
        current = self.currentvalue
        for pk, cobj in choices.items():
            if pk in current:
                but = urwid.CheckBox(str(cobj), state=True)
            else:
                but = urwid.CheckBox(str(cobj), state=False)
            urwid.connect_signal(but, 'change', self._multi_select, (pk, cobj))
            wlist.append(but)
        return urwid.ListBox(urwid.SimpleListWalker(wlist))

    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            return self._w.keypress(size, key)
            #return key
        if isinstance(self._w, urwid.Frame):
            self._w.set_focus("footer" if self._w.get_focus() == "body" else "body")

    def _message(self, b, msg):
        self._emit("message", msg)

    def _add_new(self, b):
        colname = self.metadata.colname
        relmodel = getattr(self.modelclass, colname).property.mapper.class_
        newform = get_create_form(self.session, relmodel)
        urwid.connect_signal(newform, 'popform', self._popsubform)
        urwid.connect_signal(newform, 'message', self._message)
        ovl = urwid.Overlay(urwid.LineBox(newform), self._w,
                "center", ("relative", 90), "middle", ("relative", 90), min_width=40, min_height=20)
        self._w = ovl

    def _popsubform(self, form, pkval):
        if pkval is not None:
            colname = self.metadata.colname
            relmodel = getattr(self.modelclass, colname).property.mapper.class_
            row = self.session.query(relmodel).get(pkval)
            self.currentvalue[pkval] = row
        ovl = self._w
        self._w = ovl.bottom_w
        self._w.set_body(self._build_list())

    def _cancel(self, b):
        self.old_dbvalue = None
        self.currentvalue = None
        self._emit("popform", NULL)

    def _done_multiselect(self, b):
        self.old_dbvalue = None
        dbvalue = self.currentvalue
        self._emit("popform", dbvalue)

    def _multi_select(self, b, newstate, val):
        pk, obj = val
        if newstate is True:
            self.currentvalue[pk] = obj
        else:
            try:
                del self.currentvalue[pk]
            except KeyError:
                pass


class MultiselectForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["popform", "message"]

    def __init__(self, relationinput):
        self.session = relationinput.session
        self.metadata = relationinput.metadata
        self.modelclass = relationinput.modelclass
        self.currentvalue = relationinput.dbvalue.copy()
        self.old_dbvalue = relationinput.dbvalue.copy()
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        # buttons
        done = urwid.Button("Done")
        urwid.connect_signal(done, 'click', self._done_multiselect)
        done = urwid.AttrWrap(done, 'selectable', 'butfocus')
        add = urwid.Button("Add New")
        urwid.connect_signal(add, 'click', self._add_new)
        add = urwid.AttrWrap(add, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = urwid.AttrWrap(cancel, 'selectable', 'butfocus')
        # footer and header
        header = urwid.GridFlow([done, add, cancel], 15, 3, 1, 'center')
        footer = urwid.Padding(urwid.Text(
            ("popup", "Tab to button box to select buttons. Arrow keys transfer selection.")))
        body = self._build_body()
        return urwid.Frame(body, header=header, footer=footer, focus_part="body")

    def _build_body(self):
        listbox = self._build_list()

    def _build_list(self):
        choices = get_related_choices(self.session, self.modelclass, self.metadata, None)

        #listbox.body.remove(listentry)

        #choices.update(self.currentvalue)
        wlist = []
#        current = self.currentvalue
#        for pk, cobj in choices.items():
#            if pk in current:
#                but = urwid.CheckBox(str(cobj), state=True)
#            else:
#                but = urwid.CheckBox(str(cobj), state=False)
#            urwid.connect_signal(but, 'change', self._multi_select, (pk, cobj))
#            wlist.append(but)
#        return urwid.ListBox(urwid.SimpleListWalker(wlist))


    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            return self._w.keypress(size, key)
        if isinstance(self._w, urwid.Frame):
            self._w.set_focus("header" if self._w.get_focus() == "body" else "body")

    def _message(self, b, msg):
        self._emit("message", msg)



#### top level forms
class Form(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["pushform", "popform", "message"]

    def __init__(self, session=None, modelclass=None, row=None):
        self.session = session
        self.modelclass = modelclass
        if modelclass is not None:
            self.metadata = models.get_metadata_map(modelclass)
        else:
            self.metadata = None
        self.row = row
        self.formwidgets =[] # list of only input widgets
        display_widget = self.build()
        self.__super.__init__(display_widget)
        self.newpk = None

    # from construction helpers
    def get_form_buttons(self, defaultdata=None, create=False):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok, defaultdata)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        l = [ok, cancel]
        if create:
            ok_edit = urwid.Button("OK and Edit")
            urwid.connect_signal(ok_edit, 'click', self._ok_and_edit, defaultdata)
            ok_edit = AM(ok_edit, 'selectable', 'butfocus')
            l = [ok, ok_edit, cancel]
        else:
            l = [ok, cancel]
        butgrid = urwid.GridFlow(l, 15, 3, 1, 'center')
        return urwid.Pile([urwid.Divider(), butgrid ], focus_item=1)

    def get_default_data(self, deflist):
        data = {}
        for name in deflist:
            data[name] = self.metadata[name].default
        return data

    def build_data_input(self, colmd, data=NULL, legend=None):
        typewidget = _TYPE_CREATE_WIDGETS[colmd.coltype]
        wid = typewidget(self.modelclass, colmd, data if data is not NULL else colmd.default, legend)
        wid.colname = colmd.colname
        self.formwidgets.append(wid)
        return wid

    def build_relation_input(self, colmd, data=NULL, legend=None):
        wid = RelationshipInput(self.session, self.modelclass, colmd, data if data is not NULL else colmd.default, legend)
        urwid.connect_signal(wid, "pushform", self._subform)
        wid.colname = colmd.colname
        self.formwidgets.append(wid)
        return wid

    def build_input(self, colmd, data=NULL, legend=None):
        if colmd.coltype == "RelationshipProperty":
            return self.build_relation_input(colmd, data, legend)
        else:
            return self.build_data_input(colmd, data, legend)

    def build_divider(self, legend):
        return InputDivider(legend)

    def build_attribute_input(self, colmd, data):
        wid = AttributeInput(self.session, self.modelclass, colmd, self.row)
        urwid.connect_signal(wid, "pushform", self._subform)
        urwid.connect_signal(wid, 'message', self._message)
        wid.colname = colmd.colname
        return wid

    def message(self, msg):
        self._emit("message", msg)

    def invalidate(self):
        return NotImplemented

    def _subform(self, oldform, newform):
        urwid.connect_signal(newform, 'popform', self._popform)
        urwid.connect_signal(newform, 'message', self._message)
        ovl = urwid.Overlay(urwid.LineBox(newform), self._w,
                "center", ("relative", 80), "middle", ("relative", 80), min_width=40, min_height=20)
        self._w = ovl

    def _message(self, form, msg):
        self._emit("message", msg)

    def _popform(self, form, *extra):
        urwid.disconnect_signal(form, 'popform', self._popform)
        urwid.disconnect_signal(form, 'message', self._message)
        ovl = self._w
        self._w = ovl.bottom_w

    def _cancel(self, b):
        self._emit("popform")

    def build(self):
        raise NotImplementedError("Override in subclass: return a top-level Frame widget")

    # form dispostion callbacks
    def _ok(self, b, data=None):
        raise NotImplementedError("Need to implement _ok in subclass")

    def _ok_and_edit(self, b, data=None):
        raise NotImplementedError("Need to implement _ok in subclass")



class TopForm(Form):

    _PRIMARY_TABLES = [
        "EquipmentModel",
        "Equipment",
        "Environment",
        "TestCase",
        "TestSuite",
        "TestJob",
    ]

    _SUPPORT_TABLES = [
        "Address",
        "AttributeType",
        "CapabilityGroup",
        "CapabilityType",
        "Component",
        "Contact",
        "CorporateAttributeType",
        "Corporation",
        "EnvironmentAttributeType",
        "EquipmentCategory",
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
    ]

    def build(self):
        menulist = []
        # big title
        bt = urwid.BigText("Storage Editor", urwid.HalfBlock5x4Font())
        bt = urwid.Padding(bt, "center", None)
        # primary tables for editing
        self.primlist = [TableItemWidget(s) for s in self._PRIMARY_TABLES]
        for b in self.primlist:
            urwid.connect_signal(b, 'activate', self._select)
        pmenu = urwid.GridFlow(self.primlist, 20, 2, 1, "left")
        # heading blurbs
        subhead = urwid.AttrMap(urwid.Text("Select an object type to view or edit."), "subhead")
        supportsubhead = urwid.AttrMap(urwid.Text("Select a supporting object to view or edit."), "subhead")
        # secondary/support tables
        self.seclist = [TableItemWidget(s) for s in self._SUPPORT_TABLES]
        for b in self.seclist:
            urwid.connect_signal(b, 'activate', self._select)
        smenu = urwid.GridFlow(self.seclist, 25, 1, 0, "left")
        divider = urwid.Divider(u"-", top=1, bottom=1)
        menulist = [bt, divider, subhead, pmenu, divider, supportsubhead, smenu]
        listbox = urwid.ListBox(urwid.SimpleListWalker(menulist))
        return urwid.Frame(listbox)

    def _select(self, selb):
#        for b in self.primlist:
#            urwid.disconnect_signal(b, 'activate', self._select)
        form = get_list_form(self.session, getattr(models, selb.modelname))
        self._emit("pushform", form)


class GenericListForm(Form):
    # TODO DB paging and filtering
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

    def invalidate(self):
        listbox = urwid.ListBox(self.get_items())
        self._w.body = urwid.AttrMap(listbox, 'body')
        # TODO disconnect old, existing signals
            #urwid.disconnect_signal(le, 'activate', self._edit, pk)
            #urwid.disconnect_signal(le, 'delete', self._delete, pk)

    def get_items(self):
        q = self.session.query(self.modelclass).order_by(self._orderby)
        if self._filter:
            filt = []
            for name, value in self._filter.items():
                filt.append(getattr(self.modelclass, name).like("%{}%".format(value)))
            q = q.filter(*filt)
        items = []
        for row in q:
            disprow = []
            pk = getattr(row, str(self._pkname))
            disprow.append( ('fixed', 6, urwid.Text(str(pk))) )
            for colname in self._colnames:
                md = self.metadata[colname]
                fmt, width = self._FORMATS.get(md.coltype, ("{!s:10.10}", 10))
                disprow.append( ('fixed', width, urwid.Text(fmt.format(getattr(row, colname)))) )
            le = ListEntry(urwid.Columns(disprow, dividechars=1))
            urwid.connect_signal(le, 'activate', self._edit, pk)
            urwid.connect_signal(le, 'delete', self._delete, pk)
            items.append(le)
        return urwid.SimpleListWalker(items)

    def build(self):
        self._pkname = models.get_primary_key_name(self.modelclass)
        self._orderby = self._pkname
        self._filter = {}
        self._colnames = models.get_rowdisplay(self.modelclass)
        # col headings
        colforms = [('fixed', 6, urwid.Text(("colhead", "filt:")))]
        colnames = [('fixed', 6, urwid.Text(("colhead", self._pkname))) ]
        clsname = self.modelclass.__name__
        for colname in self._colnames:
            md = self.metadata[colname]
            fmt, width = self._FORMATS.get(md.coltype, ("{!s:10.10}", 10))
            colnames.append( ('fixed', width, urwid.Text(("colhead", md.colname))) )
            if md.coltype in ("TEXT", "VARCHAR"):
                fb = SimpleEdit() # TODO use FilterInput to select sort order, once it works
                fb.colname = md.colname
                urwid.connect_signal(fb, "change", self._set_filter)
                colforms.append(('fixed', width, AM(fb, "selectable", "butfocus")))
            else:
                colforms.append(('fixed', width, urwid.Divider()))

        cb = urwid.Button("Create new {}".format(clsname.lower()))
        urwid.connect_signal(cb, 'click', self._create_cb)
        header = urwid.Pile( [
                urwid.Columns([AM(urwid.Text(clsname), "subhead"), AM(cb, "selectable", "butfocus") ], focus_column=1), 
                urwid.Columns(colforms, dividechars=1),
                urwid.Columns(colnames, dividechars=1),
                ])
        listbox = urwid.ListBox(self.get_items())
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header, focus_part="body")

    def _set_filter(self, fb):
        colname, value = fb.colname, fb.value
        if value:
            self._filter[colname] = value
        else:
            try:
                del self._filter[colname]
            except KeyError:
                pass
        self.invalidate()

    def _create_cb(self, b):
        cform = get_create_form(self.session, self.modelclass)
        urwid.connect_signal(cform, 'pushform', lambda oform, newform: self._emit("pushform", newform))
        self._emit("pushform", cform)

    def _edit(self, b, pk):
        row = self.session.query(self.modelclass).get(pk)
        eform = get_edit_form(self.session, row)
        self._emit("pushform", eform)

    def _delete(self, listentry, pk):
        row = self.session.query(self.modelclass).get(pk)
        dlg = YesNoDialog("Are you sure you want to delete {}?".format(row))
        urwid.connect_signal(dlg, 'ok', self._delete_ok, (listentry, row))
        urwid.connect_signal(dlg, 'cancel', self._delete_cancel)
        ovl = urwid.Overlay(dlg, self._w,
                "center", ("relative", 30), "middle", ("relative", 30), min_width=20, min_height=6)
        self._w = ovl

    def _delete_ok(self, dlg, data):
        listentry, row = data
        msg = "Deleted {!r}".format(str(row))
        try:
            self.session.delete(row)
            self.session.commit()
        except IntegrityError as ierr:
            self.session.rollback()
            self._emit("message", str(ierr))
        else:
            urwid.disconnect_signal(listentry, 'activate', self._edit, row.id)
            urwid.disconnect_signal(listentry, 'delete', self._delete, row.id)
            listentry._w =  urwid.Text(("deleted", msg))
        ovl = self._w
        self._w = ovl.bottom_w

    def _delete_cancel(self, dlg):
        ovl = self._w
        self._w = ovl.bottom_w

    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            return self._w.keypress(size, key)
            #return key
        self._w.set_focus("header" if self._w.get_focus() == "body" else "body")


class GenericCreateForm(Form):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create {}".format(self.modelclass.__name__)), "formhead"),
                urwid.AttrMap(urwid.Text("Use arrow keys to navigate, "
                        "Press Enter to select form buttons. Type directly into other fields."
                        "Select and press Enter in the OK button when done. Or Cancel, if you change your mind."), "formhead"),
                urwid.Divider(),
                ])
        formstack = [] # list of all form widgets to display
        doinput, _ = sort_inputs(self.modelclass)
        for key in doinput:
            md = self.metadata[key]
            if md.coltype == "RelationshipProperty":
                # only show columns that don't need our primary key (which wont exist yet)
                if not md.uselist:
                    wid = RelationshipInput(self.session, self.modelclass, md, md.default)
                    urwid.connect_signal(wid, "pushform", self._subform)
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
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def _ok(self, b, data=None):
        pkval = self._commit(data)
        if pkval is not None:
            self.formwidgets = None
            self._emit("popform", pkval)

    def _ok_and_edit(self, b, data=None):
        pkval = self._commit(data)
        if pkval is not None:
            self.formwidgets = None
            self._emit("popform", pkval)
            row = self.session.query(self.modelclass).get(pkval)
            eform = get_edit_form(self.session, row)
            self._emit("pushform", eform)

    def _commit(self, data):
        data = data or {}
        errlist = []
        widgets = self.formwidgets
        for inputwid in widgets:
            if inputwid.validate():
                data[inputwid.colname] = inputwid.value
            else:
                errlist.append(inputwid.colname)
        if errlist:
            self._emit("message", "Errors in data: {}".format(", ".join(errlist)))
            return None
        dbrow = models.create(self.modelclass)
        update_row(self.session, self.modelclass, dbrow, data)
        pkval = None
        self.session.add(dbrow)
        try:
            self.session.commit()
            pkval = models.get_primary_key_value(dbrow)
        except:
            self.session.rollback()
            ex, val, tb = sys.exc_info()
            del tb
            DEBUG(ex.__name__, val)
            self._emit("message", "{}: {}".format(ex.__name__, val))
        return pkval # will be None on failure, user may try again or cancel

    def _cancel(self, b):
        self._emit("popform", None)


class GenericEditForm(Form):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit {}".format(self.modelclass.__name__)), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        self.formwidgets = []
        doinput, m2m = sort_inputs(self.modelclass)
        for key in doinput + m2m:
            md = self.metadata[key]
            if md.coltype == "RelationshipProperty":
                wid = RelationshipInput(self.session, self.modelclass, md, getattr(self.row, md.colname))
                urwid.connect_signal(wid, "pushform", self._subform)
                wid.colname = md.colname
                formstack.append(wid)
                self.formwidgets.append(wid)
                continue
            typewidget = _TYPE_CREATE_WIDGETS.get(md.coltype, UnknownInput)
            if typewidget is not None:
                wid = typewidget(self.modelclass, md, getattr(self.row, md.colname))
                wid.colname = md.colname
                formstack.append(wid)
                self.formwidgets.append(wid)
            else:
                formstack.append(NotImplementedInput(self.modelclass, md, getattr(self.row, md.colname)))
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def _ok(self, b, data=None):
        data = data or {}
        widgets = self.formwidgets
        self.formwidgets = None
        for wid in widgets:
            data[wid.colname] = wid.value
        pkval = None
        update_row(self.session, self.modelclass, self.row, data)
        try:
            self.session.commit()
            pkval = models.get_primary_key_value(self.row)
        except:
            self.session.rollback()
            raise
        self._emit("popform", pkval)

    def _cancel(self, b):
        self._emit("popform", None)



class EquipmentCreateForm(GenericCreateForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create Equipment"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("model", "name", "serno")),
                ("Localization", ("language",)),
                ("Asset management", ("owner", "location", "sublocation", "vendor")),
                ("Automation", ("account",)),
                ("structural relationship", ('parent',)),
                ("Addtional Info", ("comments",)),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd)
                formstack.append(wid)
        data = self.get_default_data(["active", "addeddate"])
        formstack.append(self.get_form_buttons(data, create=True))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class EquipmentEditForm(GenericEditForm):
    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit Equipment"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("model", "name", "serno")),
                ("Localization", ("language",)),
                ("Asset management", ("active", "owner", "location", "sublocation", "vendor", "software")),
                ("Automation", ("account",)),
                ("structural relationship", ('parent', 'subcomponents')),
                ("Addtional Info", ("comments",)),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd, getattr(self.row, colmd.colname))
                formstack.append(wid)
        for colname in ('attributes',):# TODO ('capabilities', 'attributes'):
            colmd = self.metadata[colname]
            wid = self.build_attribute_input(colmd, getattr(self.row, colmd.colname))
            formstack.append(wid)
        formstack.insert(3, self.build_interface_input())
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def build_interface_input(self):
        colmd = self.metadata["interfaces"]
        wid = EquipmentInterfaceInput(self.session, self.modelclass, colmd, self.row)
        urwid.connect_signal(wid, "pushform", self._subform)
        urwid.connect_signal(wid, 'message', self._message)
        return wid


class EnvironmentCreateForm(GenericCreateForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create Environment"), "formhead"),
                urwid.AttrMap(urwid.Text(
                        "Arrow keys navigate,"
                        "Owner is optional, it serves as a lock on the environment. "
                        "Usually you should leave it as None."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for colname in ("name", "owner"):
            colmd = self.metadata[colname]
            wid = self.build_input(colmd)
            formstack.append(wid)
        formstack.append(self.get_form_buttons(create=True))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class EnvironmentEditForm(GenericEditForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit {}".format(self.modelclass.__name__)), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, "
                        "Enter to select form button. Tab to switch to header."
                        "Type into other fields."), "formhead"),
                AM(urwid.Button("Copy from...", on_press=self._create_copy_input), "selectable", "butfocus"),
                urwid.Divider(),
                ])
        formstack = []
        for colname in ("name", "owner"):
            colmd = self.metadata[colname]
            wid = self.build_input(colmd, getattr(self.row, colmd.colname))
            formstack.append(wid)
        colmd = self.metadata["attributes"]
        wid = self.build_attribute_input(colmd, getattr(self.row, colmd.colname))
        formstack.append(wid)
        # test equipment
        colmd = self.metadata["testequipment"]
        tewid = self.build_testequipment_input(colmd, getattr(self.row, "testequipment"))
        formstack.append(tewid)
        # common buttons
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)

    def build_testequipment_input(self, colmd, data):
        wid = TestEquipmentInput(self.session, self.modelclass, colmd, self.row)
        urwid.connect_signal(wid, "pushform", self._subform)
        urwid.connect_signal(wid, 'message', self._message)
        wid.colname = colmd.colname
        return wid

    def _create_copy_input(self, b):
        Env = models.Environment
        choices = self.session.query(Env.id, Env.name).filter(Env.id != self.row.id).order_by(Env.name)
        canc = urwid.Button("Cancel")
        urwid.connect_signal(canc, 'click', self._copy_cancel)
        butcol = urwid.Columns([AM(canc, "buttn", "buttnf")])
        wlist = [butcol]
        for pk, cname in choices:
            entry = ListEntry(urwid.Text(cname))
            urwid.connect_signal(entry, 'activate', self._copy_select)
            entry.pkey = pk
            wlist.append(entry)
        listbox = urwid.ListBox(urwid.SimpleListWalker(wlist))
        box = urwid.BoxAdapter(urwid.LineBox(listbox), 9)
        self._w.header.base_widget.widget_list[-1] = box

    def _copy_cancel(self, b):
        self._w.header.base_widget.focus_position = 2
        self._w.header.base_widget.widget_list[-1] = urwid.Divider()
        self._w.set_focus("body")

    def _copy_select(self, entry):
        self._w.header.base_widget.focus_position = 2
        self._w.header.base_widget.widget_list[-1] = urwid.Divider()
        self._w.set_focus("body")
        self._copy_environment(entry.pkey)
        self._w= self.build()

    def _copy_environment(self, envid):
        env = self.session.query(models.Environment).get(envid)
        DEBUG(env.testequipment)
        for te in env.testequipment:
            newte = models.create(models.TestEquipment,
                    roles=te.roles[:], equipment=te.equipment, UUT=te.UUT, environment=self.row)
            self.session.add(newte)

        for attr in env.attributes:
            newattr = models.create(models.EnvironmentAttribute,
                    environment=self.row, type=attr.type, value=attr.value)
            self.session.add(newattr)
        self.session.commit()

    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            return self._w.keypress(size, key)
        if isinstance(self._w, urwid.Frame):
            self._w.set_focus("header" if self._w.get_focus() == "body" else "body")



class CorporationCreateForm(GenericCreateForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create Corporation"), "formhead"),
                urwid.AttrMap(urwid.Text(
                        "Arrow keys navigate,"
                        "Owner is optional, it serves as a lock on the environment. "
                        "Usually you should leave it as None."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for colname in ("name", "address", "country", "contact", "notes"):
            colmd = self.metadata[colname]
            wid = self.build_input(colmd)
            formstack.append(wid)
        formstack.append(self.get_form_buttons(create=True))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class InterfaceCreateForm(GenericCreateForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create Interface"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("name", "alias", "ifindex", "description")),
                ("Network Address", ("ipaddr",)),
                ("Media Access Address", ("macaddr", "vlan")),
                ("Extra Info", ("interface_type", "mtu", "speed")),
                ("Administrative", ("status",)),
                ("Associations", ("network", "parent")),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd)
                formstack.append(wid)
        formstack.append(self.get_form_buttons(create=True))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class InterfaceEditForm(GenericEditForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit Interface"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("name", "alias", "ifindex", "description")),
                ("Network Address", ("ipaddr",)),
                ("Media Access Address", ("macaddr", "vlan")),
                ("Extra Info", ("interface_type", "mtu", "speed")),
                ("Administrative", ("status",)),
                ("Associations", ("network", "equipment", "parent", "subinterfaces")),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd, getattr(self.row, colmd.colname))
                formstack.append(wid)
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)



class CorporationEditForm(GenericEditForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit {}".format(self.modelclass.__name__)), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for colname in ("name", "address", "country", "contact", "notes"):
            colmd = self.metadata[colname]
            wid = self.build_input(colmd, getattr(self.row, colmd.colname))
            formstack.append(wid)
        colmd = self.metadata["attributes"]
        wid = self.build_attribute_input(colmd, getattr(self.row, colmd.colname))
        formstack.append(wid)
        # common buttons
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class TestCaseCreateForm(GenericCreateForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Create TestCase"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select "
                "form button. Type into other fields."), "formhead"),

                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("name", "purpose", "passcriteria")),
                ("Details", ("startcondition", "endcondition", "procedure")),
                ("Management", ("automated", "interactive", "testimplementation", "time_estimate")),
                ("Requirement", ("reference", "cycle", "priority")),
                ("Comments", ("comments",)),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd)
                formstack.append(wid)
        data = self.get_default_data(["lastchange", "valid", "status"])
        formstack.append(self.get_form_buttons(data, create=True))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class TestCaseEditForm(GenericEditForm):

    def build(self):
        header = urwid.Pile([
                urwid.AttrMap(urwid.Text("Edit Test Case"), "formhead"),
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
                urwid.Divider(),
                ])
        formstack = []
        for groupname, group in [
                (None, ("name", "purpose", "passcriteria")),
                ("Details", ("startcondition", "endcondition", "procedure", "prerequisites")),
                ("Management", ("valid", "automated", "interactive", "functionalarea", "testimplementation", "time_estimate", "bugid")),
                ("Requirement", ("reference", "cycle", "priority")),
                ("Status", ("status",)),
                ("Comments", ("comments",)),
                ]:
            if groupname:
                formstack.append(self.build_divider(groupname))
            for colname in group:
                colmd = self.metadata[colname]
                wid = self.build_input(colmd, getattr(self.row, colmd.colname))
                formstack.append(wid)
        data = self.get_default_data(["lastchange"])
        formstack.append(self.get_form_buttons(data))
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


_SPECIAL_CREATE_FORMS = {
        "Equipment": EquipmentCreateForm,
        "Interface": InterfaceCreateForm,
        "Environment": EnvironmentCreateForm,
        "Corporation": CorporationCreateForm,
        "TestCase": TestCaseCreateForm,
}

_SPECIAL_EDIT_FORMS = {
        "Equipment": EquipmentEditForm,
        "Interface": InterfaceEditForm,
        "Environment": EnvironmentEditForm,
        "Corporation": CorporationEditForm,
        "TestCase": TestCaseEditForm,
}

_SPECIAL_LIST_FORMS = {
#        "Equipment": EquipmentListForm,
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

### dialogs

class YesNoDialog(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals
    signals = ["ok", "cancel", "popform", "message"]

    def __init__(self, text):
        display_widget = self.build(text)
        self.__super.__init__(display_widget)

    def build(self, text):
        body = urwid.Filler(AM(urwid.Text(text), "popup"))
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok)
        ok = urwid.AttrWrap(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = urwid.AttrWrap(cancel, 'selectable', 'butfocus')
        buttons = urwid.GridFlow([ok, cancel], 10, 3, 1, 'center')
        footer = urwid.Pile( [urwid.Divider(), buttons ], focus_item=1)
        return urwid.LineBox(urwid.Frame(body, footer=footer, focus_part="footer"))

    def _ok(self, b):
        self._emit("ok")

    def _cancel(self, b):
        self._emit("cancel")


### utility functions

def sort_inputs(modelclass):
    first = []
    one2many = []
    many2many = []
    for md in models.get_metadata(modelclass):
        if md.nullable:
            if md.coltype == "RelationshipProperty":
                if md.uselist:
                    many2many.append(md.colname)
                else:
                    one2many.append(md.colname)
            else:
                first.append(md.colname)
        else:
            if md.coltype == "RelationshipProperty":
                one2many.insert(0, md.colname)
            else:
                first.insert(0, md.colname)
    return first + one2many, many2many


def get_related_choices(session, modelclass, metadata, order_by=None):
    mapper = models.class_mapper(modelclass)
    mycol = getattr(modelclass, metadata.colname)
    try:
        relmodel = mycol.property.mapper.class_
    except AttributeError:
        return {}

    if metadata.uselist:
        if metadata.m2m:
            q = session.query(relmodel)
        else:
            # only those that are currently unassigned
            rs = mycol.property.remote_side[0]
            q = session.query(relmodel).filter(rs == None)
    else:
        q = session.query(relmodel)
    # add optional order_by, default to ordering by first ROW_DISPLAY column.
    try:
        order_by = order_by or relmodel.ROW_DISPLAY[0]
    except (AttributeError, IndexError):
        pass
    if order_by:
        q = q.order_by(getattr(relmodel, order_by))
    return dict((getattr(relrow, "id"), relrow) for relrow in q)


def update_row(session, modelclass, dbrow, data):
    for metadata in models.get_metadata(modelclass):
        value = data.get(metadata.colname, NULL) # must use NULL for sentinal since None is a valid value.
        if value is NULL:
            continue
        if not value and metadata.nullable:
            value = None
        if metadata.coltype == "RelationshipProperty":
            relmodel = getattr(modelclass, metadata.colname).property.mapper.class_
            if isinstance(value, list):
                if not value:
                    continue
                #t = session.query(relmodel).filter(relmodel.id.in_(value)).all()
                t = value
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
                if type(value) in (int, long):
                    value = session.query(relmodel).get(value)
                setattr(dbrow, metadata.colname, value)

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
## Below is for trying out experimental stuff

class TestForm(Form):
    def __init__(self):
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        sess = models.get_session()
#        self.edit = urwid.Edit("Edit me: ", multiline=True)
#        header = urwid.AttrMap(urwid.Text("Edit this text"), "head")
#        buts = self.get_form_buttons()
#
#        fi = SimpleEdit()
#        ls = ListScrollSelector(["one", "two", "three", "four", "five", "six"])
#        urwid.connect_signal(ls, 'click', self._scroll_select)
#
#        cols = urwid.Columns([fi, urwid.Edit("input: ", multiline=False), ls,
#                (25, AM(urwid.Text("legend", align="right"), "collabel")),
#                 AM(urwid.Edit("input", multiline=False), "body")])
#
#        tefrm = urwid.BoxAdapter(TestEquipmentAddForm(sess), 20)
#        listbox = urwid.ListBox(urwid.SimpleListWalker([self.edit, tefrm, cols, buts]))
#
#        frm = urwid.Frame(listbox, header=header)
        #ovr = urwid.Frame(urwid.Filler(urwid.Text("Inside frame")))
        #ovl = urwid.Overlay(urwid.LineBox(ovr), frm, "center", 80, "middle", 24)
        T = urwid.Text
        M = models.Equipment
        md = models.get_column_metadata(M, "interfaces")

        eq = sess.query(M).get(80)
        choices = get_related_choices(sess, M, md, None)
        #DEBUG(choices)

        current = eq.interfaces
        currentvalues = {}
        for v in current.values():
            currentvalues[v.id] = v

        leftlist = []
        rightlist = []
        for pk, row in choices.items():
            entry = ListEntry(urwid.Text(unicode(row).encode("utf-8")))
            #urwid.connect_signal(entry, 'activate', self._single_select, pk)
            leftlist.append(entry)

        for pk, row in currentvalues.items():
            entry = ListEntry(urwid.Text(unicode(row).encode("utf-8")))
            #urwid.connect_signal(entry, 'activate', self._single_select, pk)
            rightlist.append(entry)


        left = urwid.ListBox(urwid.SimpleListWalker(leftlist))
        right = urwid.ListBox(urwid.SimpleListWalker(rightlist))
        center = urwid.Filler(urwid.Text("<-"))
        return urwid.Columns([left, center, right])
        #return frm

    def _scroll_select(self, ls):
        DEBUG(ls.value)

    def run(self):
        loop = urwid.MainLoop(self, PALETTE, unhandled_input=self.unhandled_input, pop_ups=True,
                event_loop=urwid.GLibEventLoop())
        loop.run()

    def unhandled_input(self, k):
        if k == "esc":
            raise urwid.ExitMainLoop()
        DEBUG("unhandled key:", k)


def _test(argv):
    app = TestForm()
    print(app.run())

def _report_metadata(modelclass):
    basic = []
    many2many = []
    one2many = []
    for md in models.get_metadata(modelclass):
        if md.coltype == "RelationshipProperty":
            if md.uselist:
                many2many.append(md.colname)
            else:
                one2many.append(md.colname)
        else:
            basic.append(md.colname)
    print(" basic data:", basic)
    print(" One 2 many:", one2many)
    print("Many 2 many:", many2many)


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    from pycopia import logwindow
    DEBUG = logwindow.DebugLogWindow()
    #_report_metadata(models.Interface)
    #_test(sys.argv)

