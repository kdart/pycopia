#!/usr/bin/python2.6
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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


"""Module that defines test loaders.

The objects here are responsible for taking a desired test, or set of
tests, looking in the database for implementations and dependencies, and
constructing a runnable test objects.
"""


__author__ = 'keith@kdart.com (Keith Dart)'


import sys
import os

from pycopia import logging
from pycopia.textutils import identifier
from pycopia import module
from pycopia.QA import core


class Error(Exception):
    """Base class for test loader errors."""

class NoImplementationError(Error):
    """Raised when a test object has no automated implementation defined."""

class InvalidObjectError(Error):
    """Raised when an attempt is made to instantiate a test object from the
    database, but the object in the database is marked invalid.
    """

class InvalidTestError(Error):
    """Raised when a test is requested that cannot be run for some
    reason.
    """

def get_test_class(dbcase):
    """Return the implementation class of a TestCase, or None if not found.
    """
    if dbcase.automated and dbcase.valid:
        impl = dbcase.testimplementation
        if impl:
            obj = module.get_object(impl)
            if type(obj) is type and issubclass(obj, core.Test):
                return obj
            else:
                raise InvalidTestError("%r is not a Test class object." % (obj,))
        else:
            return None
    else:
        return None


def get_suite(dbsuite, config):
    """Get a Suite object.

    Return the implementation class of a TestSuite, or a generic Suite
    instance if not defined.
    """
    name = dbsuite.name
    if " " in name:
        name = identifier(name)
    impl = dbsuite.suiteimplementation
    if impl:
        try:
            obj = module.get_object(impl)
        except module.ObjectImportError:
            logging.warning("Did not find suite implementation %r." % (impl,))
        else:
            if type(obj) is type and issubclass(obj, core.TestSuite):
                return obj(config, name=name)
            else:
                raise InvalidObjectError("%r is not a TestSuite class object." % (obj,))
    return core.TestSuite(config, name=name)


def get_TestSuite_from_module(mod, config):
    """Get an existing suite from a module."""
    for methname in ("get_suite", "GetSuite"):
        try:
            meth = getattr(mod, methname)
            return meth(config)
        except AttributeError:
            continue
    raise module.ObjectImportError("Module %r does not have a get_suite() function." % (module,))

