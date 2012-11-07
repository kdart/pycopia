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
from datetime import datetime

import urwid

from sqlalchemy.exc import IntegrityError

from pycopia import ipv4
from pycopia.aid import NULL
from pycopia.db import types
from pycopia.db import models

DEBUG = NULL

PALETTE = [
    ('banner', 'black', 'light gray', 'standout,underline'),
    ('bg', 'black', 'dark blue'),
    #('body','black','light gray', 'standout'),
    ('body','default', 'default'),
    ('popup','black','light gray', 'standout'),
    ('top','default', 'default'),
    ('border','black','dark blue'),
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
    ('shadow','white','black'),
    ('notimplemented', 'dark red', 'black'),
    ('deleted', 'dark red', 'black'),
    ('title', 'white', 'black', 'bold'),
    ('colhead', 'yellow', 'black', 'default'),
]


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
        val = u"" if value is None else value
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
        val = u"" if value is None else value
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
        self._emit("pushform", newform)

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
            self.row.set_attribute(self.session, entry.attrname, newtext)
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
            self._emit("message", "{}: {}".format(ex.__name__, val))
            return
        urwid.disconnect_signal(form, 'ok', self._edit_ok, entry)
        urwid.disconnect_signal(form, 'cancel', self._edit_cancel, entry)
        saveentry = self._saveentryval
        del self._saveentryval
        saveentry.base_widget[1].base_widget.set_text(newtext)
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
        except:
            ex, val, tb = sys.exc_info()
            self.session.rollback()
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
        choices = [c[0] for c in self.modelclass.get_attribute_list(self.session)] # list of (name, basetype) pairs
        ls = AM(ListScrollSelector(choices), "selectable", "butfocus")
        te = urwid.Edit(edit_text=u"", multiline=True, allow_tab=True)
        ok, cancel = self.get_form_buttons()
        return urwid.Columns([ls, ("weight", 2, te), (10, ok), (10, cancel)], dividechars=1, focus_column=0)

    def _ok(self, b):
        widget_list = self._w.widget_list
        data = (widget_list[0].base_widget.value, widget_list[1].get_text()[0] )
        self._emit("ok", data)

    def _cancel(self, b):
        self._emit("cancel")


class ListScrollSelector(urwid.Widget):
    _selectable = True
    _sizing = frozenset(['flow'])
    signals = ["click"]
    UPARR=u"↑"
    DOWNARR=u"↓"

    def __init__(self, choicelist):
        self.__super.__init__()
        self._list = choicelist
        self._max = len(choicelist)
        assert self._max > 0, "Need list with at least one element"
        self._index = 0
        self._text = self._list[self._index]
        maxwidth = reduce(lambda c,m: max(c,m), map(lambda o: len(str(o)), choicelist), 0)
        self._fmt = u"{} {{:{}.{}s}} {}".format(self.UPARR, maxwidth, maxwidth, self.DOWNARR)
        self._layout = urwid.text_layout.default_layout

    def keypress(self, size, key):
        cmd =  self._command_map[key]
        if cmd == 'cursor up':
            self._index = (self._index + 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == 'cursor down':
            self._index = (self._index - 1) % self._max
            self.set_text(self._list[self._index])
        elif cmd == "activate":
            self._emit("click")
        else:
            return key

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
            ("popup", "Select multiple idtems. Tab to button box to select buttons. Arrow keys move selection.")))
        listbox = self._build_list()
        return urwid.Frame(listbox, header=header, footer=footer, focus_part="body")

    def _build_list(self):
        choices = get_related_choices(self.session, self.modelclass, self.metadata.colname, None)
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

    def _add_new(self, b):
        colname = self.metadata.colname
        relmodel = getattr(self.modelclass, colname).property.mapper.class_
        newform = get_create_form(self.session, relmodel)
        urwid.connect_signal(newform, 'popform', self._popsubform)
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

    def build(self):
        raise NotImplementedError("Override in subclass: return a top-level Frame widget")

    # from construction helpers
    def get_form_buttons(self, defaultdata=None):
        ok = urwid.Button("OK")
        urwid.connect_signal(ok, 'click', self._ok, defaultdata)
        ok = AM(ok, 'selectable', 'butfocus')
        cancel = urwid.Button("Cancel")
        urwid.connect_signal(cancel, 'click', self._cancel)
        cancel = AM(cancel, 'selectable', 'butfocus')
        butgrid = urwid.GridFlow([ok, cancel], 10, 3, 1, 'center')
        return urwid.Pile([urwid.Divider(), butgrid ], focus_item=1)

    def get_default_data(self, deflist):
        data = {}
        for name in deflist:
            data[name] = self.metadata[name].default,
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
        #urwid.connect_signal(wid, "pushform", self._subform)
        urwid.connect_signal(wid, 'message', self._message)
        wid.colname = colmd.colname
        return wid

    def message(self, msg):
        self._emit("message", msg)

    def _subform(self, oldform, newform):
        urwid.connect_signal(newform, 'popform', self._popform)
        urwid.connect_signal(newform, 'message', self._message)
        ovl = urwid.Overlay(urwid.LineBox(newform), self._w,
                "center", ("relative", 80), "middle", ("relative", 80), min_width=40, min_height=20)
        self._w = ovl

    def _message(self, form, msg):
        self._emit("message", msg)

    def _popform(self, form, *extra):
        ovl = self._w
        self._w = ovl.bottom_w

    # form dispostion callbacks
    def _ok(self, b, data=None):
        raise NotImplementedError("Need to implement _ok in subclass")

    def _cancel(self, b):
        self._emit("popform")



class TopForm(Form):

    _PRIMARY_TABLES = [
        "EquipmentModel",
        "Equipment",
        "Environment",
#        "TestEquipment",
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
        divider = urwid.Divider(u"-")
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
                [urwid.Columns([AM(urwid.Text(clsname), "subhead"), AM(cb, "selectable", "butfocus") ],
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
            le = ListEntry(urwid.Columns(disprow, dividechars=1))
            urwid.connect_signal(le, 'activate', self._edit, pk)
            urwid.connect_signal(le, 'delete', self._delete, pk)
            items.append(le)
        listbox = urwid.ListBox(urwid.SimpleListWalker(items))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header, focus_part="body")

    def _create(self, b):
        cform = get_create_form(self.session, self.modelclass)
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
                urwid.AttrMap(urwid.Text("Arrow keys navigate, Enter to select form button. Type into other fields."), "formhead"),
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
            return
        self.formwidgets = None
        dbrow = models.create(self.modelclass)
        update_row(self.session, self.modelclass, dbrow, data)
        pkval = None
        try:
            self.session.add(dbrow)
            try: # TODO retry form
                self.session.commit()
                pkval = models.get_primary_key_value(dbrow)
            except:
                self.session.rollback()
                raise
        finally:
            self._emit("popform", pkval)

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
        formstack.append(self.get_form_buttons(data))
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
                (None, ("model", "name", "serno", "interfaces")),
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
        formstack.append(self.get_form_buttons())
        listbox = urwid.ListBox(urwid.SimpleListWalker(formstack))
        return urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)


class TestCaseCreateForm(Form):
    pass


class TestCaseEditForm(Form):
    pass


_SPECIAL_CREATE_FORMS = {
        "Equipment": EquipmentCreateForm,
#        "TestCase": TestCaseCreateForm,
}

_SPECIAL_EDIT_FORMS = {
        "Equipment": EquipmentEditForm,
#        "TestCase": TestCaseEditForm,
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


def get_related_choices(session, modelclass, colname, order_by=None):
    mapper = models.class_mapper(modelclass)
    mycol = getattr(modelclass, colname)
    try:
        relmodel = mycol.property.mapper.class_
    except AttributeError:
        return {}

    mymeta = models.get_column_metadata(modelclass, colname)
    if mymeta.uselist:
        if mymeta.m2m:
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
    return dict((models.get_primary_key_value(relrow), relrow) for relrow in q)


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
## XXX for trying out experimental stuff

class TestForm(Form):
    def __init__(self):
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        self.edit = urwid.Edit("Edit me: ", multiline=True)
        header = urwid.AttrMap(urwid.Text("Edit this text"), "head")
        buts = self.get_form_buttons()

        ls = ListScrollSelector(["one", "two", "three", "four", "five", "six"])
        urwid.connect_signal(ls, 'click', self._scroll_select)

        cols = urwid.Columns([urwid.Edit("input: ", multiline=False), #ls,
                (25, AM(urwid.Text("legend", align="right"), "collabel")),
                 AM(urwid.Edit("input", multiline=False), "body")])

        listbox = urwid.ListBox(urwid.SimpleListWalker([self.edit, cols, buts]))

        frm = urwid.Frame(urwid.AttrMap(listbox, 'body'), header=header)
        #ovr = urwid.Frame(urwid.Filler(urwid.Text("Inside frame")))
        #ovl = urwid.Overlay(urwid.LineBox(ovr), frm, "center", 80, "middle", 24)
        return frm

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


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    from pycopia import logwindow
    DEBUG = logwindow.DebugLogWindow()
    modelclass = models.Equipment
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
    _test(sys.argv)
