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
User interface components for running tests.

Depends on the following report being defined in the configuration:
   reports.remote=('pycopia.reports.clientserver.RemoteReport',)
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os

import urwid

from pycopia import proctools
from pycopia import timelib
from pycopia.dictlib import AttrDict
from pycopia.reports import clientserver

from pycopia.QA import core
from pycopia.QA.tui import walkers
from pycopia.QA.tui import widgets
from pycopia.QA.tui import db


### shorthand notation
AM = urwid.AttrMap


class RunnerForm(widgets.Form):

    def __init__(self):
        self.report_rx = None
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        environments = db.get_environment_names()
        reports = [None] + db.get_report_names()

        self._envsel = widgets.ListScrollSelector(environments)
        self._repsel = widgets.ListScrollSelector(reports)
        self._tclist = urwid.SimpleListWalker([])
        butcols = urwid.Columns([
                ("pack", urwid.Text("environment:")),
                AM(self._envsel, "selectable", "butfocus"),
                ("pack", urwid.Text("report:")),
                AM(self._repsel, "selectable", "butfocus"),
            ], dividechars=2)
        header = urwid.Pile([
        AM(urwid.Text("Select environment, report, and set options. Use Tab to switch to environment selector. Selected:"), "subhead"),
                urwid.BoxAdapter(urwid.ListBox(self._tclist), 2),
                butcols,
        ])
        body = self._build_test_selector(False)
        return urwid.Frame(body, header=header, focus_part="body")

    def keypress(self, size, key):
        if self._command_map[key] != 'next selectable':
            return self._w.keypress(size, key)
        self._w.set_focus("header" if self._w.get_focus() == "body" else "body")

    def _runtest(self, b):
        if not self._tclist:
            self._emit("message", "No tests selected")
            return
        urwid.disconnect_signal(b, "click", self._runtest) # prevent running again until test ends
        environmentname = self._envsel.value
        reportname = self._repsel.value
        options = self._get_options()
        testlist = [tw.base_widget.text for tw in self._tclist]
        self.runtest(testlist, environmentname, reportname, options)
        self._w.set_focus("body")

    def runtest(self, testlist, environmentname="default", reportname=None, options=None):
        """Run a test using the external runtest program."""
        if self.report_rx is not None:
            self._emit("message", "Test still running")
            return
        report = ReportForm()
        self.report_rx = clientserver.ReportReceiver(report)
        self._w.body = report
        if reportname:
            altreport = ",{}".format(reportname)
        else:
            altreport = ""
        tc = " ".join(testlist)
        if options:
            optlist = " ".join("--{}={!r}".format(*t) for t in options.items())
        else:
            optlist = ""
        cmd = "runtest --reportname=remote{} --environmentname={} {} {}".format(altreport, environmentname, optlist, tc)
        proctools.spawnpty(cmd, callback=self._test_end)

    def _test_end(self, proc):
        self.report_rx.close()
        self.report_rx = None
        if not proc.exitstatus:
            self._emit("message", str(proc.exitstatus))

    def _get_options(self):
        return {} # TODO

    def _build_test_selector(self, include_testcases):
        cb = AM(urwid.CheckBox("Include test cases", False, on_state_change=self._refresh_cb), "selectable", "butfocus")
        gobut = urwid.Button("Go")
        urwid.connect_signal(gobut, 'click', self._runtest)
        gobut = urwid.AttrWrap(gobut, 'selectable', 'butfocus')
        tb = self._get_testtree(include_testcases)
        return urwid.Pile([(1, urwid.Filler(cb)), tb, urwid.Filler(gobut)])

    def _get_testtree(self, include_testcases):
        testtree = scan_source(include_testcases, self._select_runnable)
        tree = walkers.SimpleTreeWalker(testtree)
        if_grandchild = lambda pos: tree.depth(pos) > 1
        treelist = widgets.CollapsibleIndentedTreeListWalker(tree,
                       is_collapsed=if_grandchild,
                       #indent=6,
                       #childbar_offset=1,
                       selectable_icons=True,
                       icon_focussed_att='butfocus',
                       #icon_frame_left_char=None,
                       #icon_frame_right_char=None,
                       #icon_expanded_char='-',
                       #icon_collapsed_char='+',
                )
        return widgets.TreeBox(treelist)

    def _append_tclist(self, path):
        self._tclist.append(urwid.Text(path))

    def _refresh_cb(self, cb, newstate):
        tb = self._get_testtree(newstate)
        self._w.body.base_widget.contents[1] = (tb, ('weight', 1))

    def _select_runnable(self, runnable):
        self._append_tclist(runnable.name)


class JobRunnerForm(widgets.Form):
    """TODO"""

    def __init__(self):
        self.report_rx = None
        display_widget = self.build()
        self.__super.__init__(display_widget)

    def build(self):
        header = urwid.Pile([
            AM(urwid.Text("Select a test job to run."), "subhead"),
            ])
        body = self._build_test_selector()
        return urwid.Frame(body, header=header, focus_part="body")

    def _build_test_selector(self):
        jobs = [widgets.ListEntry(job.name) for job in db.get_job_list()]
        jobwalker = urwid.SimpleListWalker(jobs)
        return urwid.ListBox(jobwalker)



def scan_source(include_testcases=False, on_activate=None):
    """Scan the installed source code base, in the "testcases" base package,
    for runnable modules, UseCases, and TestCases.

    Return a list of tuples (DisplayNode, children)
    """
    from pycopia import module
    try:
        import testcases
    except ImportError:
        return []

    # callback for testdir walker
    def filternames(flist, dirname, names):
        for name in names:
            if name.endswith(".py") and not name.startswith("_"):
                flist.append(os.path.join(dirname, name[:-3]))
    testhome = os.path.dirname(testcases.__file__)
    modnames = []
    os.path.walk(testhome, filternames, modnames)
    testhome_index = len(os.path.dirname(testhome)) + 1
    modnames = map(lambda n: n[testhome_index:].replace("/", "."), modnames)
    # have a list of full module names at this point
    rootlist = []
    root = (widgets.PackageNode("testcases"), rootlist)
    rootdict = {"testcases": {"children": rootlist}}
    for modname in sorted(modnames):
        try:
            mod = module.get_module(modname)
        except module.ModuleImportError:
            continue
        d = rootdict
        parts = modname.split(".")
        for part in parts[:-1]:
            try:
                d = d[part]
            except KeyError:
                newlist = []
                d[part] = {"children": newlist}
                d["children"].append((widgets.PackageNode(part), newlist))
                d = d[part]
        modchildren = []
        for attrname in dir(mod):
            obj = getattr(mod, attrname)
            if type(obj) is type:
                if issubclass(obj, core.UseCase):
                    modchildren.append((widgets.UseCaseNode(".".join([modname, obj.__name__]), on_activate=on_activate), None))
                if include_testcases and issubclass(obj, core.Test):
                    modchildren.append((widgets.TestCaseNode(".".join([modname, obj.__name__]), on_activate=on_activate), None))
        if not modchildren:
            modchildren = None
        d["children"].append((widgets.ModuleNode(modname, hasattr(mod, "run"), on_activate=on_activate), modchildren))
    return [root]



# runtime support

class ReportForm(urwid.WidgetWrap):
    __metaclass__ = urwid.MetaSignals

    def __init__(self):
        display_widget = self._build()
        self.__super.__init__(display_widget)

    def _build(self):
        self.replist = urwid.SimpleListWalker([])
        return urwid.ListBox(self.replist)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return self._w.keypress(size, key)

    def _message(self, msgtype, msg, level):
        if msgtype.find("TIME") >= 0:
            msg = timelib.localtimestamp(msg, "%b %d %H:%M:%S")
        return urwid.Columns([(20, urwid.Text(("repmsg", msgtype), "right")), urwid.Text(msg)], dividechars=1)

    def _extra_info(self, msgtype, *msg):
        cols = [(20, urwid.Text(("repinfo", msgtype), "right"))]
        for part in msg:
            cols.append(("pack", urwid.Text(unicode(part).encode("utf-8"), wrap="clip")))
        return urwid.Columns(cols, dividechars=1)

    def initialize(self, config=None):
        del self.replist[:]

    def finalize(self):
        self.replist.append(urwid.Divider(u'━'))

    def logfile(self, filename):
        self.replist.append(self._extra_info("Logfile", filename))

    def add_title(self, title):
        self.replist.append(urwid.Text(("formhead", title)))

    def add_heading(self, text, level=1):
        box = widgets.get_linebox(urwid.Text(("colhead", text)), level)
        self.replist.append(box)

    def add_message(self, msgtype, msg, level=1):
        self.replist.append(self._message(msgtype, msg, level))

    def add_summary(self, entries):
        # gets a list of tuples of ("testentry string", TestResult)
        pass

    def add_text(self, text):
        self.replist.append(urwid.Text(text))

    def add_analysis(self, text):
        self.replist.append(self._extra_info("Analysis", text))

    def add_data(self, data, note=None):
        if note:
            self.replist.append(self._extra_info("Data added", note))

    def add_url(self, text, url):
        self.replist.append(self._extra_info("URL", text, url))

    def passed(self, msg, level=1):
        self.replist.append(urwid.Text([("reppass", "PASS "), unicode(msg).encode("utf-8")]))

    def failed(self, msg, level=1):
        self.replist.append(urwid.Text([("repfail", "FAIL "), unicode(msg).encode("utf-8")]))

    def expectedfail(self, msg, level=1):
        self.replist.append(urwid.Text([("repexpfail", "EXPECTED FAIL "), unicode(msg).encode("utf-8")]))

    def incomplete(self, msg, level=1):
        self.replist.append(urwid.Text([("repincomplete", "INCOMPLETE "), unicode(msg).encode("utf-8")]))

    def abort(self, msg, level=1):
        self.replist.append(urwid.Text([("repabort", "ABORT "), unicode(msg).encode("utf-8")]))

    def info(self, msg, level=1):
        self.replist.append(urwid.Text([("repinfo", "INFO "), unicode(msg).encode("utf-8")]))

    def diagnostic(self, msg, level=1):
        self.replist.append(urwid.Text([("repdiag", "DIAG "), unicode(msg).encode("utf-8")]))

    def newpage(self):
        self.replist.append(urwid.Divider(u"="))

    def newsection(self):
        self.replist.append(urwid.Divider(u"-"))



if __name__ == "__main__":
    from pycopia import autodebug
    from pprint import pprint
    st = scan_source(True)
    pprint (st)
    #print (get_test_list())

