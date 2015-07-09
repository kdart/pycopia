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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

__doc__ = """
Storage editor. Edit data in the Pycopia database. Start with a list of
editable tables. Select and move to locations to create, update, and delete
entries.

Keys:
    Generally, use arrow keys to navigate and press Enter to select items.

    ESC : Quit the program
    Tab : Move focus to different button or area. Arrow keys also work.
    F1  : This Help
    F2  : Reset the application to initial condition.

Shortcuts for creating test cases:
    F5  : Create a new test case in the database.
    F6  : Create a new test suite in the database.

Shortcuts for creating equipment and environments.
    F9  : Create a new equipment entry.
    F10 : Create a new environment entry.

"""

import sys

import urwid

from pycopia import getopt
from pycopia.db import models
from pycopia.db.tui import widgets
from pycopia.db.tui import eventloop


class DBEditor(object):

    def __init__(self, session, debug=False):
        self.loop =None
        self.session = session
        self.footer = urwid.AttrMap(
                urwid.Text([
                        ("key", "ESC"), " Quit  ",
                        ("key", "Tab"), " Move Selection  ",
                        ("key", "F1"), " Help  ",
                        ("key", "F2"), " Reset ",
                        ("key", "F5"), " Add Test Case ",
                        ("key", "F6"), " Add Test Suite ",
                        ("key", "F9"), " Add Equipment ",
                        ("key", "F10"), " Add Environment ",
                    ]),
                "foot")
        self.reset()
        self.top = urwid.Frame(urwid.AttrMap(self.form, 'body'), footer=self.footer)
        if debug:
            from pycopia import logwindow
            widgets.DEBUG = logwindow.DebugLogWindow()

    def run(self):
        self.loop = urwid.MainLoop(self.top, widgets.PALETTE,
                unhandled_input=self.unhandled_input, pop_ups=True, event_loop=eventloop.PycopiaEventLoop())
        self.loop.run()
        self.loop = None

    def unhandled_input(self, k):
        if k == "esc":
            self._popform(None, None)
        elif k == "f1":
            self.show_help()
        elif k == "f2":
            self.reset()
            self.top.body = self.form
        elif k == "f5":
            self.get_create_form(models.TestCase)
        elif k == "f16":
            self.get_create_form(models.TestSuite)
        elif k == "f9":
            self.get_create_form(models.Equipment)
        elif k == "f10":
            self.get_create_form(models.Environment)
        else:
            widgets.DEBUG("unhandled key:", k)


    def reset(self):
        self._formtrail = []
        self.form = widgets.TopForm(self.session)
        urwid.connect_signal(self.form, 'pushform', self._pushform)

    def _restore_footer(self, loop, user_data):
        self.top.set_footer(self.footer)

    def _pushform(self, form, newform):
        self._formtrail.append(form)
        urwid.connect_signal(newform, 'pushform', self._pushform)
        urwid.connect_signal(newform, 'popform', self._popform)
        urwid.connect_signal(newform, 'message', self._message)
        self.form = newform
        self.top.body = self.form

    def _popform(self, form, pkval):
        if form is not None:
            urwid.disconnect_signal(form, 'pushform', self._pushform)
            urwid.disconnect_signal(form, 'popform', self._popform)
            urwid.disconnect_signal(form, 'message', self._message)
        if self._formtrail:
            self.form = self._formtrail.pop()
            self.form.invalidate()
            self.top.body = self.form
        else:
            raise urwid.ExitMainLoop()

    def _message(self, form, msg):
        self.message(msg)

    def message(self, msg):
        self.top.set_footer(urwid.AttrWrap(urwid.Text(msg), "important"))
        self.loop.set_alarm_in(15.0, self._restore_footer)

    def get_list_form(self, modelclass):
        form = widgets.get_list_form(self.session, modelclass)
        urwid.emit_signal(self.form, 'pushform', self.form, form)

    def get_create_form(self, modelclass):
        form = widgets.get_create_form(self.session, modelclass)
        urwid.emit_signal(self.form, 'pushform', self.form, form)

    def get_edit_form(self, row):
        form = widgets.get_edit_form(self.session, row)
        urwid.emit_signal(self.form, 'pushform', self.form, form)

    def show_help(self):
        hd = HelpDialog()
        urwid.connect_signal(hd, 'close', lambda hd: self._restoreform())
        self.top.body = hd

    def _restoreform(self):
        self.top.body = self.form



class HelpDialog(urwid.WidgetWrap):
    signals = ['close']

    def __init__(self):
        close_button = urwid.Button(("buttn", "OK"))
        urwid.connect_signal(close_button, 'click', lambda button:self._emit("close"))
        lb =urwid.LineBox(urwid.Filler(urwid.Pile([urwid.Text(__doc__), close_button]), valign="top"))
        self.__super.__init__(lb)


def main(argv):
    """dbedit [-d]
    """
    debug = 0
    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "?hdD")
    except getopt.GetoptError:
            print (main.__doc__)
            return
    for opt, val in optlist:
        if opt in ("-?", "-h"):
            print (main.__doc__)
            return
        elif opt == "-d":
            debug += 1
        elif opt == "-D":
            from pycopia import autodebug

    sess = models.get_session()
    try:
        app = DBEditor(sess, debug)
        try:
            app.run()
        except:
            if debug:
                ex, val, tb = sys.exc_info()
                from pycopia import debugger
                if debug > 1:
                    from pycopia import IOurxvt
                    io = IOurxvt.UrxvtIO()
                else:
                    io = None
                debugger.post_mortem(tb, ex, val, io)
                if debug > 1:
                    io.close()
            else:
                raise
    finally:
        sess.close()


if __name__ == "__main__":
    import sys
    from pycopia import debugger
    try:
        main(sys.argv)
    except:
        ex, val, tb = sys.exc_info()
        #from pycopia import IOurxvt
        #io = IOurxvt.UrxvtIO()
        debugger.post_mortem(tb, ex, val)
        #io.close()

