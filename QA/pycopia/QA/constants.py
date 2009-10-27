#!/usr/bin/python
# vim:ts=2:sw=2:softtabstop=0:tw=74:smarttab:expandtab


"""QA Universal constants and enumerations.

Possible test outcomes:

- PASSED: execute() test passed (criteria was met), and the suite may continue.

- FAILED: execute() failed (criteria was not met), but the suite can
  continue. You may also raise a TestFailError exception.

- INCOMPLETE: execute() could not complete, and the pass/fail criteria
  could not be determined. but the suite may continue. You may also raise
  a TestIncompleteError exception.

- ABORT: execute() could not complete, and the suite cannot continue.
  Raising TestSuiteAbort exception has the same effect.

- NA: A result that is not applicable (e.g. it is a holder of tests).

- EXPECTED_FAIL: Means the test is failing due to a bug, and is already
  known to fail. 

"""


from pycopia import aid

# Default report message.
NO_MESSAGE = "no message"


### These enums should match exactly the enums in pycopia.db.types module.  ###
# results a test object can produce.
TESTRESULTS = aid.Enums(PASSED=1, FAILED=0, INCOMPLETE=-1, ABORT=-2, NA=-3,
                    EXPECTED_FAIL=-4)
TESTRESULTS.sort()
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = TESTRESULTS

# Type of objects the TestRunner can run, and reports can be generated
# from.
OBJECTTYPES = aid.Enums("module", "TestSuite", "Test", "TestRunner", "unknown")
[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = OBJECTTYPES

