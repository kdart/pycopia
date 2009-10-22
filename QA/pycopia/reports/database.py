#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


"""Report object that populates the test results database.

Include this report if you want a test to report its
results into the database.

The table schema is hierarchical, and some records will hold different set
of data from another. The entire set is obtained by custom query in the
model object.

"""


import sys
import os

from datetime import datetime
from pycopia import passwd
from pycopia import reports

from sqlalchemy.orm.exc import NoResultFound

from pycopia.db import models


_COLUMNS = {
    "testcase": None,           # test case record
    "environment": None,        # from config
    "build": None,              # BUILD
    "tester": None,             # user running the test
    "testversion": None,        # Version of test implementation
    "parent": None,             # container object
    "objecttype_c": None,       # Object type enumeration
    "starttime": None,          # STARTTIME (Test, Suite),    RUNNERSTART (module)
    "endtime": None,            # ENDTIME (Test, Suite), RUNNEREND (module)
    "arguments": None,          # TESTARGUMENTS (Test), RUNNERARGUMENTS (module)
    "result": None,             # PASSED, FAILED, EXPECTED_FAIL, INCOMPLETE, ABORT
    "diagnostic": None,         # The diagnostic message before failure.
    "testresultdata": None,     # optional serialized data (reference)
    "resultslocation": None,    # url
    "testimplementation": None, # implementation 
    "reportfilename": None,
    "note": None,               # COMMENT
    "valid": True,              
}

# The enumerations in models need to be converted to pure ints for the
# database to get updated properly.
[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = map(int, models.OBJECTTYPES)
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = map(int, models.TESTRESULTS)


class ResultHolder(object):
    def __init__(self):
        self.parent = None
        self._children = []
        self._data = _COLUMNS.copy()

    def __str__(self):
        d = self._data
        return "%s (%s) - %s start: %s end: %s" % (
            models.OBJECTTYPES[d["objecttype_c"]], d["testimplementation"], 
            d["result"], d["starttime"], d["endtime"])

    def get_result(self):
        new = ResultHolder()
        new.parent = self
        return new

    def append(self, obj):
        self._children.append(obj)

    def remove(self, obj):
        self._children.remove(obj)

    def destroy(self):
        if self.parent:
            self.parent.remove(self)
        for child in self._children:
            child.destroy()

    def set(self, cname, val):
        self._data[cname] = val

    def get(self, cname):
        return self._data[cname]

    def commit(self, dbsession, parentrecord=None):
        self._data["parent"] = parentrecord
        self.resolve_testcase(dbsession)
        tr = models.create(models.TestResult, **self._data)
        dbsession.add(tr)
        for child in self._children:
            child.commit(dbsession, tr)

    def emit(self, fo, level=0):
        fo.write("    "*level)
        fo.write(str(self))
        fo.write("\n")
        for child in self._children:
            child.emit(fo, level+1)

    def resolve_testcase(self, dbsession):
        ti = self._data.get("testimplementation")
        if ti:
            try:
                tc = dbsession.query(
                        models.TestCase).filter(models.TestCase.testimplementation==ti).one()
            except NoResultFound:
                pass
            else:
                self._data["testcase"] = tc


def get_user(conf):
    sess = conf.session
    pwent = passwd.getpwuid(os.getuid())
    try:
#        user = models.User.objects.get(username=pwent.name)
        user = sess.query(models.User).filter(models.User.username==pwent.name).one()
    except NoResultFound:
        user = models.create_user(sess, pwent)
    return user


# When constructing a report from report messages:
# transition table:
#from: to: RUNNER MODULE         SUITE         TEST
# RUNNER     NA         push             push            push
# MODULE     pop        add                push            push
# SUITE        pop        pop                add             push
# TEST         pop        pop                pop             add

class DatabaseReport(reports.NullReport):

    def initialize(self, cf):
        # here is where information from the global configuration that is
        # needed in the database record is kept until the records are written
        # in the finalize method.
        self._debug = cf.flags.DEBUG
        self._environment = cf.environment.environment
        self._testid = None
        self._rootresult = ResultHolder()
        self._rootresult.set("environment", self._environment)
        self._rootresult.set("result", NA)
        self._rootresult.set("objecttype_c", RUNNER)
        self._currentresult = self._rootresult
        self._MIMETYPE = "text/plain" # all reports have a mime type
        user = cf.get("user")
        if user is None:
            user = get_user(cf)
        self._user = user
        self._rootresult.set("tester", self._user)
        self._dbsession = cf.session

    MIMETYPE = property(lambda self: self._MIMETYPE)

    def finalize(self):
        self._currentresult = None
        root = self._rootresult
        self._rootresult = None
        if self._debug:
            sys.stdout.write("\nReport structure:\n")
            root.emit(sys.stdout)
        else:
            root.commit(self._dbsession)
            self._dbsession.commit()
        root.destroy()

    def new_result(self, otype):
        new = self._currentresult.get_result()
        new.set("environment", self._environment)
        new.set("testversion", self._testid)
        new.set("tester", self._user)
        new.set("objecttype_c", int(models.OBJECTTYPES[otype]))
        return new

    def add_result(self, otype):     # really a pop-push operation.
        self.pop_result()
        self.push_result(otype)

    def push_result(self, otype):
        if self._debug:
            sys.stdout.write("     *** push_result: %s\n" % (models.OBJECTTYPES[otype],))
        new = self.new_result(otype)
        self._currentresult.append(new)
        self._currentresult = new

    def pop_result(self):
        if self._debug:
            sys.stdout.write("     *** pop_result\n")
        self._currentresult = self._currentresult.parent

    def logfile(self, filename):
        pass # XXX store log file name?

    def add_title(self, text): 
        # only the test runner sends this.
        pass

    def add_heading(self, text, level): 
        # level = 1 for suites, 2 for tests, 3 for other
        # signals new test and test suite record.
        currenttype = self._currentresult.get("objecttype_c")
        if currenttype == RUNNER: 
            self.push_result(level)     # runner -> (suite | test)
        elif currenttype == MODULE:
            self.push_result(level)     # module -> (suite | test)
        elif currenttype == SUITE:
            if level == 1:                        # suite -> suite
                self.add_result(level)
            elif level == 2:                    # suite -> test
                self.push_result(level) 
        elif currenttype == TEST:
            if level == 1:                        # test -> suite
                self.pop_result()
            elif level == 2:                    # test -> test
                self.add_result(level) 
            elif level == 3:                    # suite summary result starting
                self.pop_result() 
        # Add the implementation name if a suite or a test.
        if level in (1,2):
            self._currentresult.set("testimplementation", text)

    def add_message(self, msgtype, msg, level=0): 
        if msgtype == "RUNNERARGUMENTS":
            self._rootresult.set("arguments", msg)
        elif msgtype == "RUNNERSTARTTIME":
            self._rootresult.set("starttime", datetime.fromtimestamp(msg))
        elif msgtype == "RUNNERENDTIME":
            self._rootresult.set("endtime", datetime.fromtimestamp(msg))
        elif msgtype == "COMMENT":
            self._rootresult.set("note", msg)
        elif msgtype == "TESTARGUMENTS":
            self._currentresult.set("arguments", msg)
        elif msgtype == "STARTTIME":
            self._currentresult.set("starttime", datetime.fromtimestamp(msg))
        elif msgtype == "ENDTIME":
            self._currentresult.set("endtime", datetime.fromtimestamp(msg))
        elif msgtype == "MODULEVERSION":
            self._testid = msg
        elif msgtype == "MODULESTARTTIME":
            currenttype = self._currentresult.get("objecttype_c")
            if currenttype == RUNNER:
                self.push_result(0)    # runner -> module
                self._currentresult.set("starttime", datetime.fromtimestamp(msg))
            elif currenttype == MODULE:
                self.add_result(0)            # module -> module
                self._currentresult.set("starttime", datetime.fromtimestamp(msg))
            elif currenttype == SUITE:
                self.pop_result()             # suite -> module
            elif currenttype == TEST:
                self.pop_result()             # test -> module
        elif msgtype == "MODULEENDTIME":
            currenttype = self._currentresult.get("objecttype_c")
            if currenttype == SUITE:
                self.pop_result()             # suite -> runner
            elif currenttype == TEST:
                self.pop_result()             # test -> runner
            self._currentresult.set("endtime", datetime.fromtimestamp(msg))
            self._currentresult.set("result", NA)

    def passed(self, msg, level=1):
        self._currentresult.set("result", PASSED)

    def failed(self, msg, level=1):
        # If test did not write a diagnostic message then use fail message as
        # diagnostic.
        if not self._currentresult.get("diagnostic"):
            self._currentresult.set("diagnostic", msg)
        self._currentresult.set("result", FAILED)

    def expectedfail(self, msg, level=1):
        if not self._currentresult.get("diagnostic"):
            self._currentresult.set("diagnostic", msg)
        self._currentresult.set("result", EXPECTED_FAIL)

    def incomplete(self, msg, level=1):
        if not self._currentresult.get("diagnostic"):
            self._currentresult.set("diagnostic", msg)
        self._currentresult.set("result", INCOMPLETE)

    def abort(self, msg, level=1):
        self._currentresult.set("result", ABORT)

    def diagnostic(self, msg, level=1):
        self._currentresult.set("diagnostic", msg)

    def add_summary(self, entries): 
        pass

    def add_text(self, text): 
        pass

    def add_data(self, data, note=None): 
        testdata = models.create(models.TestResultData, data=data, note=note)
        if not self._debug:
            self._dbsession.add(testdata)
        self._currentresult.set("testresultdata", testdata)

    def add_url(self, text, url): 
        self._rootresult.set("resultslocation", url)



