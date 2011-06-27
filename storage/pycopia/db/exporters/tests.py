#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
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

"""
Write test case template code from database entries.

"""

import os
from logging import warn


from sqlalchemy import and_, or_

from pycopia import textutils
from pycopia.db import models
from pycopia.aid import mapstr



### Test case template file parts follow.

HEAD = mapstr("""#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab

\"\"\"
%(heading)s
%(line)s

%(modinfo)s

\"\"\"

from pycopia.QA import core
""")

MODIMPORT = mapstr("""from %(modname)s import %(classname)s
""")

CLASSDEF = mapstr("""
class %(classname)s(core.Test):
    \"\"\"
    Purpose
    +++++++

    %(purpose)s

    Pass Criteria
    +++++++++++++

    %(passcriteria)s

    Start Condition
    +++++++++++++++

    %(startcondition)s

    End Condition
    +++++++++++++

    %(endcondition)s

    Reference
    +++++++++

    %(reference)s

    Prerequisites
    +++++++++++++

    %(prerequisites)s

    Procedure
    +++++++++

    %(procedure)s

    \"\"\"
    %(prereqline)s

    def execute(self):
        return self.manual()
""")

PREREQLIST = mapstr("""
    PREREQUISITES = [%(prereqlist)s]
""")

GETSUITE_GENERIC = mapstr("""
def get_suite(config):
    suite = core.TestSuite(config, name="%(suitename)s")
""")

GETSUITE_SPECIFIC = mapstr("""
class %(suitename)s(core.TestSuite):
    pass

def get_suite(config):
    suite = %(suitename)s(config)
""")

ADDSUITE = mapstr("""    suite.add_test(%(classname)s)
""")

END = mapstr("""
    return suite

def run(config):
    suite = get_suite(config)
    suite.run()
""")

#### end templates


tbl = [" "]*256
for c in textutils.alphanumeric:
    tbl[ord(c)] = c
_IDENTTABLE = "".join(tbl)
del tbl, c


def identifier(name):
    name = name.translate(_IDENTTABLE)
    return "".join(map(textutils.identifier, name.split()))



class TestSuiteExporter(object):

    def __init__(self, basedir):
        self._basedir = basedir
        self._dbsession = models.get_session()
        self._writer = None

    def close(self):
        if self._dbsession is not None:
            self._dbsession.close()
        if self._writer is not None:
            self._writer.close()
        self._dbsession = None
        self._writer = None

    def __del__(self):
        self.close()

    def start(self, modname, description):
        filename = os.path.join(self._basedir, "suites", modname.replace(".", "/")) + ".py"
        try:
            os.makedirs(os.path.split(filename)[0])
        except OSError: # already exists
            pass
        self._writer = open(filename, "w")
        self._writer.write(str(HEAD(heading=modname, line="-"*len(modname), modinfo=description)))

    def end_suite(self):
        self._writer.write(str(SUITEEND))
        self._writer.close()
        self._writer = None

    def end_testcase(self):
        self._writer.close()
        self._writer = None

    def export_testcase(self, dbtestcase):
        name = identifier(dbtestcase.name)
        if dbtestcase.prerequisite:
            prerequisites = identifier(dbtestcase.prerequisite.name)
            prereqline = str(PREREQLIST(prereqlist=prerequisites))
        else:
            prerequisites = ""
            prereqline = ""
        CLASSDEF(classname=name, 
                purpose=str(dbtestcase.purpose),
                passcriteria=str(dbtestcase.passcriteria),
                startcondition=str(dbtestcase.startcondition),
                endcondition=str(dbtestcase.endcondition),
                reference=str(dbtestcase.reference),
                prerequisites=prerequisites,
                procedure=str(dbtestcase.procedure),
                prereqline=prereqline)
        self._writer.write(str(CLASSDEF))

    def export_suite(self, dbsuite):
        testnames = []
        name = identifier(dbsuite.name)
        self.start(name, dbsuite.purpose)
        for tc in dbsuite.testcases:
            self.export_testcase(tc)
            testnames.append(identifier(tc.name))
        self._writer.write(str(GETSUITE_GENERIC(suitename=name)))
        for tcname in testnames:
            self._writer.write(str(ADDSUITE(classname=tcname)))
        self.end_suite()

    def export_suites(self, filt):
        dbsession = self._dbsession
        basequery = and_(or_(models.TestSuite.suiteimplementation == None, 
                        models.TestSuite.suiteimplementation == "" ), 
                    models.TestSuite.valid == True)
        if filt:
            query = dbsession.query(models.TestSuite).filter(
                    and_(
                        basequery,
                        models.TestSuite.name.like("%" + filt + "%")
                    )
                )
        else:
            query = dbsession.query(models.TestSuite).filter(basequery)

        for dbsuite in query.all():
            self.export_suite(dbsuite)

    def export_all_suites(self):
        return export_suites(None)



if __name__ == "__main__":
    import sys
    from pycopia import autodebug

    print "Attributes:"
    print "HEAD:", HEAD.attributes()
    print "CLASSDEF:", CLASSDEF.attributes()
    print "PREREQLIST:", PREREQLIST.attributes()
    print "GETSUITE_GENERIC:", GETSUITE_GENERIC.attributes()
    print "GETSUITE_SPECIFIC:", GETSUITE_SPECIFIC.attributes()
    print "ADDSUITE:", ADDSUITE.attributes()
    print "SUITEEND:", SUITEEND.attributes()
    print "---"

    exporter = TestSuiteExporter("/var/tmp/python")
    exporter.export_suites(None)

