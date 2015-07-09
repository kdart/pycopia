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
Web interface for QA reports and tools.

This depends on the storage server also running.

"""

import itertools

from pycopia.WWW import framework
from pycopia.WWW.middleware import auth
from pycopia.WWW import HTML5

from pycopia.aid import IF
from pycopia.db import types
from pycopia.db import models
from pycopia.db import webhelpers


from sqlalchemy.exc import DataError, IntegrityError
#from sqlalchemy import and_, or_



TC_METAMAP = dict((c.colname, c) for c in models.get_metadata(models.TestCase))
#TR_METAMAP = dict((c.colname, c) for c in models.get_metadata(models.TestResult))


TINY_MCE_EDIT_INIT="""
    tinyMCE.init({
        mode : "textareas",
        theme : "advanced",
        editor_selector : "TEXT",
        theme_advanced_buttons1 : "bold,italic,underline,separator,strikethrough,justifyleft,justifycenter,justifyright,justifyfull,bullist,numlist,undo,redo,|,formatselect,fontselect,fontsizeselect",
        theme_advanced_buttons2 : "",
        theme_advanced_buttons3 : "",
        theme_advanced_toolbar_location : "top",
        theme_advanced_toolbar_align : "left",
        theme_advanced_statusbar_location : "none"
        });
"""


def testcase_edit_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    doc.scripts = [ "MochiKit.js", "proxy.js", "db.js", "tiny_mce/tiny_mce.js"]
    doc.add_javascript2head(text=TINY_MCE_EDIT_INIT)
    for name, val in kwargs.items():
        setattr(doc, name, val)
    build_framing(request, doc, "Edit Test Case")
    return doc


def testcase_view_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    doc.scripts = [ "MochiKit.js", "proxy.js", "db.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    build_framing(request, doc, "Test Case")
    return doc

#def testcase_delete_constructor(request, **kwargs):
#    doc = HTML5.new_document()
#    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
#    for name, val in kwargs.items():
#        setattr(doc, name, val)
#    build_framing(request, doc, "Delete Test Case")
#    return doc


def testcase_run_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    for name, val in kwargs.items():
        setattr(doc, name, val)
    build_framing(request, doc, "Run Test Case")
    return doc


def testcase_list_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    doc.scripts = [ "MochiKit.js", "proxy.js", "db.js"]
    for name, val in kwargs.items():
        setattr(doc, name, val)
    build_framing(request, doc, "Test Cases")
    return doc


def testcase_create_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    for name, val in kwargs.items():
        setattr(doc, name, val)
    doc.scripts = [ "MochiKit.js", "proxy.js", "db.js", "tiny_mce/tiny_mce.js"]
    doc.add_javascript2head(text=TINY_MCE_EDIT_INIT)
    build_framing(request, doc, "New Test Case")
    return doc


def build_framing(request, doc, title):
    nav = doc.add_section("navigation")
    NM = doc.nodemaker
    nav.append(NM("P", None,
         NM("A", {"href":"/"}, "Home"), NM("_", None),
         IF(request.path.count("/") > 2, NM("A", {"href":".."}, "Up")), NM("_", None),
    ))
    nav.append(NM("P", {"class_": "title"}, title))
    nav.append(NM("P", None,
            NM("A", {"href": "/auth/logout"}, "logout")))
    doc.add_section("messages", id="messages")



def render_testcase(doc, dbrow):
    doc.add_header(2, dbrow.name)
    NM = doc.nodemaker
    sect = doc.add_section("testcasebody", id="rowid_%s" % dbrow.id)
    if dbrow.functionalarea:
        sect.add_header(3, "Area Tested")
        dl = sect.add_definition_list()
        dl.add_definition("Testing area:", " ".join(map(str, dbrow.functionalarea)))

    sect.add_header(3, "Implementation")
    if dbrow.automated:
        if dbrow.testimplementation:
            sect.new_para("Implemented in: '%s'%s." % (dbrow.testimplementation,
                    IF(dbrow.interactive, " (user interactive test)", "")))
        else:
            sect.new_para("Test is automated but has no implementation!", class_="error")
    else:
        if dbrow.testimplementation:
            sect.new_para("Manual test implemented in: '%s'." % (dbrow.testimplementation,))
        else:
            sect.new_para("This is a manual test that may be run by the this web interface.")

    for colname in ('purpose', 'passcriteria', 'startcondition', 'endcondition', 'procedure'):
        sect.add_header(3, colname.capitalize())
        sect.append(NM("ASIS", None, getattr(dbrow, colname))) # these entries stored as XHTML markup already.

#        form = doc.add_form(action=request.resolver.get_url(testcase_edit, tcid=dbrow.id))
#        BR = form.get_new_element("Br")
#        outerfs = form.add_fieldset(modelclass.__name__)
#        for colname in ('name', 'purpose', 'passcriteria', 'startcondition', 'endcondition',
#                        'procedure', 'reference', 'testimplementation',
#                        'functionalarea', 'prerequisite', 'automated', 'interactive'):
#            metadata = TC_METAMAP[colname]
#            webhelpers.create_input(outerfs, modelclass, metadata, dbrow)
#            outerfs.append(BR)
#        for colname in ('priority', 'cycle', 'status'):
#            metadata = TC_METAMAP[colname]
#            webhelpers.create_input(outerfs, modelclass, metadata, dbrow)
#            outerfs.append(BR)


class TestcaseViewer(framework.RequestHandler):

    def get(self, request, tcid):
        dbrow = get_testcase(tcid)
        title = "Testcase %r" % (dbrow.name,)
        resp = framework.ResponseDocument(request, testcase_view_constructor, title=title)
        doc = resp.doc
        NM = doc.nodemaker
        doc.new_para(
                NM("Fragments", None,
                    NM("A", {"href": request.resolver.get_url(testcase_run, tcid=dbrow.id)}, resp.get_icon("go")),
                    NM("A", {"href": request.resolver.get_url(testcase_edit, tcid=dbrow.id)}, resp.get_icon("edit")),
                    NM("A", {"href": "javascript:doDeleteRow(%r, %r);" % ("TestCase", dbrow.id)},
                        resp.get_icon("delete")),
                )
        )
        render_testcase(doc, dbrow)
        return resp.finalize()



class TestcaseEditor(framework.RequestHandler):

    def get(self, request, tcid):
        dbrow = get_testcase(tcid)
        resp = self.get_page(request, dbrow)
        return resp.finalize()

    def post(self, request, tcid):
        dbrow = get_testcase(tcid)
        try:
            webhelpers.update_row(request.POST, models.TestCase, dbrow)
        except types.ValidationError, err:
            webhelpers.dbsession.rollback()
            resp = self.get_page(request, dbrow, err)
            return resp.finalize()
        try:
            webhelpers.dbsession.commit()
        except (DataError, IntegrityError), err:
            webhelpers.dbsession.rollback()
            resp = self.get_page(request, dbrow, err)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.resolver.get_url(testcase_list))

    def get_page(self, request, dbrow, error=None):
        title = "Edit test case %r." % (dbrow.name,)
        modelclass = models.TestCase
        resp = framework.ResponseDocument(request, testcase_edit_constructor, title=title)
        resp.new_para(title)
        if error is not None:
            resp.new_para(error, class_="error")
        form = resp.add_form(action=request.resolver.get_url(testcase_edit, tcid=dbrow.id))
        BR = form.get_new_element("Br")
        outerfs = form.add_fieldset(modelclass.__name__)
        for colname in ('name', 'purpose', 'passcriteria', 'startcondition', 'endcondition',
                        'procedure', 'reference', 'testimplementation',
                        'functionalarea', 'prerequisites', 'automated', 'interactive'):
            metadata = TC_METAMAP[colname]
            webhelpers.create_input(outerfs, modelclass, metadata, dbrow)
            outerfs.append(BR)
        for colname in ('priority', 'cycle', 'status'):
            metadata = TC_METAMAP[colname]
            webhelpers.create_input(outerfs, modelclass, metadata, dbrow)
            outerfs.append(BR)
        form.add_hidden("lastchange", str(models.tables.time_now()))
        form.add_input(type="submit", name="submit", value="submit")
        return resp




class TestcaseRunner(framework.RequestHandler):

    def get(self, request, tcid):
        dbrow = get_testcase(tcid)
        title = "Run test case %r" % (dbrow.name,)
        resp = framework.ResponseDocument(request, testcase_run_constructor, title=title)
        render_testcase(resp.doc, dbrow)
        if not dbrow.automated:
            form = resp.doc.add_form(action=request.resolver.get_url(testcase_run, tcid=dbrow.id))
            BR = form.get_new_element("Br")
            outerfs = form.add_fieldset("Run the test.")
            outerfs.add_textinput("build", "Build")
            outerfs.new_para("Build should have form: '<project>.<major>.<minor>.<subminor>.<build>'")
            webhelpers.create_pick_list(outerfs, models.Environment, filtermap=None)
            outerfs.append(BR)
            outerfs.yes_no("Were you able to complete the test?", name="completed")
            outerfs.append(BR)
            outerfs.yes_no("If so, did it pass?", name="passfail")
            outerfs.append(BR)
            outerfs.add_textinput("note", "Notes")
            form.add_hidden("starttime", str(models.tables.time_now()))
            form.add_input(type="submit", name="submit", value="OK")
        else:
            resp.doc.new_para("""
            This is an automated test. Running automated tests from the
            web interface is not yet supported.
            """,
            class_="error")
        return resp.finalize()

    def post(self, request, tcid):
        dbrow = get_testcase(tcid)
        data = request.POST
        if data.get("completed") == "0": # yes
            if data.get("passfail") == "0": # yes
                result = webhelpers.PASSED
            else:
                result = webhelpers.FAILED
        else:
            result = webhelpers.INCOMPLETE

        username = request.session["username"]
        tester = models.User.get_by_username(webhelpers.dbsession, username)
        build=webhelpers.resolve_build(data.get("build"))

        rr = models.create(models.TestResult,
                objecttype=webhelpers.RUNNER,
                testcase=None,
                environment=webhelpers.resolve_environment(data.get("environment")),
                build=build,
                tester=tester,
                testversion=None,
                parent=None,
                starttime=data.get("starttime"),
                endtime=str(models.tables.time_now()),
                arguments=None,
                result=result,
                diagnostic=None,
                note=None,
                valid=True,
            )
        webhelpers.dbsession.add(rr)
        tr = models.create(models.TestResult,
                objecttype=webhelpers.TEST,
                testcase=dbrow,
                environment=None,
                build=build,
                tester=tester,
                testversion=None,
                parent=rr,
                starttime=data.get("starttime"),
                endtime=str(models.tables.time_now()),
                arguments=None,
                result=result,
                diagnostic=IF(result != webhelpers.PASSED, data.get("note")),
                note=IF(result == webhelpers.PASSED, data.get("note")),
                valid=True,
            )
        webhelpers.dbsession.add(tr)
        try:
            webhelpers.dbsession.commit()
        except (DataError, IntegrityError), err:
            webhelpers.dbsession.rollback()
            title = "Test runner error"
            resp = framework.ResponseDocument(request, testcase_run_constructor, title=title)
            resp.doc.new_para(err, class_="error")
            resp.doc.new_para("There was an error recording this test. Please try again.")
            return resp.finalize()
        return framework.HttpResponseRedirect(request.resolver.get_url(testcase_list))


class TestcaseCreator(framework.RequestHandler):

    def get_page(self, request, error=None):
        title = "Create new test case"
        modelclass = models.TestCase
        resp = framework.ResponseDocument(request, testcase_create_constructor, title=title)
        resp.new_para(title)
        if error is not None:
            resp.new_para(error, class_="error")
        form = resp.add_form(action=request.resolver.get_url(testcase_create))
        outerfs = form.add_fieldset(modelclass.__name__)
        BR = form.get_new_element("Br")
        for colname in ('name', 'purpose', 'passcriteria', 'startcondition', 'endcondition',
                        'procedure', 'reference', 'testimplementation',
                        'functionalarea', 'prerequisites', 'automated', 'interactive'):
            metadata = TC_METAMAP[colname]
            webhelpers.new_input(outerfs, modelclass, metadata)
            outerfs.append(BR)
        for colname in ('priority', 'cycle', 'status'):
            metadata = TC_METAMAP[colname]
            webhelpers.new_input(outerfs, modelclass, metadata)
            outerfs.append(BR)
        form.add_input(type="submit", name="submit", value="submit")
        return resp

    def get(self, request):
        resp = self.get_page(request)
        return resp.finalize()

    def post(self, request):
        dbrow = models.TestCase()
        try:
            webhelpers.update_row(request.POST, models.TestCase, dbrow)
        except types.ValidationError, err:
            webhelpers.dbsession.rollback()
            request.log_error("TC create ValidationError: %s\n" % (err,))
            resp = self.get_page(request, err)
            return resp.finalize()

        webhelpers.dbsession.add(dbrow)

        try:
            webhelpers.dbsession.commit()
        except (DataError, IntegrityError), err:
            webhelpers.dbsession.rollback()
            request.log_error("TC create data error: %s\n" % (err,))
            resp = self.get_page(request, err)
            return resp.finalize()
        else:
            return framework.HttpResponseRedirect(request.resolver.get_url(testcase_list))



class TestcaseLister(framework.RequestHandler):

    def get(self, request):
        resp = framework.ResponseDocument(request, testcase_list_constructor, title="Test cases")
        tableclass = models.TestCase
        NM = resp.nodemaker
        resp.new_para(NM("A", {"href": request.resolver.get_url(testcase_create)},
                resp.get_icon("add")))
        cycler = itertools.cycle(["row1", "row2"])
        tbl = resp.doc.add_table(width="100%")
        tbl.caption("Test Cases")
        colnames = ("name", "testimplementation")
        tbl.new_headings("", *colnames)
        for dbrow in webhelpers.query(tableclass, {}):
            row = tbl.new_row(id="rowid_%s" % dbrow.id, class_=cycler.next())
            col = row.new_column(
                NM("Fragments", {},
                    NM("A", {"href": "run/%s" % (dbrow.id,)},
                        resp.get_small_icon("go")),
                    NM("A", {"href": "edit/%s" % (dbrow.id,)},
                        resp.get_small_icon("edit")),
                    NM("A", {"href": "javascript:doDeleteRow(%r, %r);" % (tableclass.__name__, dbrow.id)},
                        resp.get_small_icon("delete")),
                )
            )
            firstname = colnames[0]
            row.new_column(
                NM("A", {"href": request.resolver.get_url(testcase_view, tcid=dbrow.id)},
                        getattr(dbrow, firstname))
            )
            for colname in colnames[1:]:
                row.new_column(getattr(dbrow, colname))
        return resp.finalize()



def get_testcase(rowid):
    try:
        dbrow = webhelpers.dbsession.query(models.TestCase).get(int(rowid))
        if dbrow is None:
            raise framework.HttpErrorNotFound("No such testcase id.")
    except ValueError:
            raise framework.HttpErrorNotFound("Bad id value.")
    return dbrow



def main_constructor(request, **kwargs):
    doc = HTML5.new_document()
    doc.stylesheet = request.resolver.get_url("css", name="qawebui.css")
    for name, val in kwargs.items():
        setattr(doc, name, val)
    build_framing(request, doc, "Test Management")
    return doc


class MainHandler(framework.RequestHandler):

    def get(self, request):
        resp = framework.ResponseDocument(request, main_constructor)
        NM = resp.doc.nodemaker
        resp.new_para("Test Management.")
        resp.doc.append(
          NM("UL", None,
            NM("LI", None,
                    NM("A", {"href": request.resolver.get_url(testcase_list)}, "Test cases."),
            ),
#            NM("LI", None,
#                    NM("A", {"href": request.resolver.get_url(testresults_list)}, "Latest test results."),
#            ),
          )
        )
        return resp.finalize()


# handlers mapped from the config.

testcase_list = webhelpers.setup_dbsession(auth.need_login(TestcaseLister()))
testcase_view = webhelpers.setup_dbsession(auth.need_login(TestcaseViewer()))
testcase_edit = webhelpers.setup_dbsession(auth.need_login(TestcaseEditor()))
testcase_create = webhelpers.setup_dbsession(auth.need_login(TestcaseCreator()))
testcase_run = webhelpers.setup_dbsession(auth.need_login(TestcaseRunner()))

main = auth.need_login(MainHandler())



if __name__ == "__main__":
    pass
