#!/usr/bin/python2.4
# vim:ts=2:sw=2:softtabstop=0:tw=74:smarttab:expandtab
#
# Copyright The Android Open Source Project

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at 
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by Keith Dart to conform to Pycopia style and improve
# documentation.


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

__author__ = 'keith@kdart.com (Keith Dart)'
__original_author__ = 'dart@google.com (Keith Dart)'


from pycopia import aid

# results a test object can produce.
TESTRESULTS = aid.Enums(PASSED=1, FAILED=0, INCOMPLETE=-1, ABORT=-2, NA=-3,
                    EXPECTED_FAIL=-4)
TESTRESULTS.sort()
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = TESTRESULTS

# Default report message.
NO_MESSAGE = "no message"

# Type of objects the TestRunner can run, and reports can be generated
# from.
OBJECTTYPES = aid.Enums("module", "TestSuite", "Test", "TestRunner", "unknown")
[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = OBJECTTYPES

