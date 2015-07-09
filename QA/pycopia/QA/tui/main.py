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

__doc__ = """Test runner and reporter.

Keys:
    Generally, use arrow keys to navigate and press Enter to select items.

    ESC : Quit the program
    Tab : Move focus to different button or area. Arrow keys also work.
    F1  : This Help
    F2  : Reset the application to initial condition.

"""

import sys
import os

import urwid

from pycopia.QA.tui import widgets
from pycopia.QA.tui import runner
from pycopia.db.tui import eventloop


class TopForm(widgets.Form):

    def __init__(self):
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        bt = urwid.BigText("Test Case Manager", urwid.HalfBlock5x4Font())
        bt = urwid.Padding(bt, "center", None)
        # Primary functions
        menulist = [
                widgets.MenuItemWidget("Run Test Code", self.do_run),
                widgets.MenuItemWidget("Run Test Job", self.do_job),
        ]
        pmenu = urwid.GridFlow(menulist, 20, 2, 1, "left")
        # heading blurb
        subhead = urwid.AttrMap(urwid.Text("Choose your desired activity."), "subhead")
        divider = urwid.Divider(u"-", top=1, bottom=1)
        formlist = [bt, divider, subhead, pmenu]
        listbox = urwid.ListBox(urwid.SimpleListWalker(formlist))
        return urwid.Frame(listbox)

    def do_run(self, item):
        frm = runner.RunnerForm()
        self._emit("pushform", frm)

    def do_job(self, item):
        frm = runner.JobRunnerForm()
        self._emit("pushform", frm)


class TestRunnerShell(object):

    def __init__(self):
        self.footer = urwid.AttrMap(
                urwid.Text([
                        ("key", "ESC"), " Quit  ",
                        ("key", "F1"), " Help  ",
                        ("key", "F2"), " Reset ",
                    ]),
                "foot")
        self.reset()

    def unhandled_input(self, k):
        if k == "esc":
            self._popform(None)
        elif k == "f1":
            self.show_help()
        elif k == "f2":
            self.reset()
        elif k == "f3":
            pass
        else:
            widgets.DEBUG("unhandled key:", k)

    def run(self):
        self.loop = urwid.MainLoop(self.top, widgets.PALETTE, unhandled_input=self.unhandled_input,
                event_loop=eventloop.PycopiaEventLoop())
        self.loop.run()
        self.loop = None

    def reset(self):
        self._formtrail = []
        self.loop = None
        self.form = TopForm()
        urwid.connect_signal(self.form, 'pushform', self._pushform)
        self.top = urwid.Frame(self.form, footer=self.footer)

    def _pushform(self, form, newform):
        self._formtrail.append(form)
        urwid.connect_signal(newform, 'pushform', self._pushform)
        urwid.connect_signal(newform, 'popform', self._popform)
        urwid.connect_signal(newform, 'message', self._message)
        self.form = newform
        self.top.body = self.form

    def _popform(self, form):
        if form is not None:
            urwid.disconnect_signal(form, 'pushform', self._pushform)
            urwid.disconnect_signal(form, 'popform', self._popform)
            urwid.disconnect_signal(form, 'message', self._message)
        if self._formtrail:
            self.form = self._formtrail.pop()
            #self.form.invalidate()
            self.top.body = self.form
        else:
            raise urwid.ExitMainLoop()

    def _message(self, form, msg):
        self.message(msg)

    def message(self, msg):
        self.top.set_footer(urwid.AttrWrap(urwid.Text(msg), "important"))
        self.loop.set_alarm_in(15.0, self._restore_footer)

    def _restore_footer(self, loop, user_data):
        self.top.set_footer(self.footer)

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
    """qashell [-dD]
    Run the QA shell.
    """
    from pycopia import getopt
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

    if debug:
        from pycopia import logwindow
        widgets.DEBUG = logwindow.DebugLogWindow(do_stderr=True)

    app = TestRunnerShell()
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
            widgets.DEBUG.close()
            if debug > 1:
                io.close()
        else:
            raise




if __name__ == "__main__":
    main(["qashell", "-dd"])

