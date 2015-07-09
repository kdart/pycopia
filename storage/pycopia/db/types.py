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
Extra database types.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


__all__ = ["INTEGER", "BIGINT", "SMALLINT", "VARCHAR", "CHAR", "TEXT",
    "NUMERIC", "FLOAT", "REAL", "INET", "CIDR", "UUID", "BIT", "MACADDR",
    "DOUBLE_PRECISION", "TIMESTAMP", "TIME", "DATE", "BYTEA", "BOOLEAN",
    "INTERVAL", "ARRAY", "ENUM",
    "ValidationError", "Cidr", "Inet", "PickleText", "JsonText", "TestCaseStatus",
    "TestCaseType", "PriorityType", "TestResultType", "TestObjectType",
    "ValueType", "LikelihoodType", "SeverityType", "validate_value_type"]

import sys
import json

# works with both python 2.7 and 3.x
try:
    import cPickle as pickle
    dumps = pickle.dumps
    loads = pickle.loads
except ImportError:
    import pickle
    dumps = lambda o: pickle.dumps(o, protocol=0, fix_imports=True).decode("ascii")
    loads = lambda o: pickle.loads(o, fix_imports=True)


from pycopia.aid import Enums
from pycopia.ipv4 import IPv4


from sqlalchemy.dialects.postgresql import (INTEGER, BIGINT, SMALLINT,
        VARCHAR, CHAR, TEXT, NUMERIC, FLOAT, REAL, INET,
        CIDR, UUID, BIT, MACADDR, DOUBLE_PRECISION, TIMESTAMP, TIME,
        DATE, BYTEA, BOOLEAN, INTERVAL, ARRAY, ENUM)

from sqlalchemy import types
from sqlalchemy.ext.mutable import Mutable


class ValidationError(AssertionError):
    pass


# custom column types.

class Cidr(Mutable, types.TypeDecorator):
    """Cidr reprsents networks without host part."""

    impl = CIDR

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return IPv4(value).network.CIDR

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return IPv4(value)

    def copy_value(self, value):
        if value is None:
            return None
        return IPv4(value)

class Inet(Mutable, types.TypeDecorator):
    """An IPv4 address type. Columns with this type take and receive IPv4
    objects from the database.
    """

    impl = INET

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return IPv4(value).CIDR

    def copy_value(self, value):
        if value is None:
            return None
        return IPv4(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if "/" in value:
            return IPv4(value)
        else:
            return IPv4(value, "255.255.255.255")


class PickleText(types.TypeDecorator):
    """For columns that store Python objects in a TEXT column.

    Be aware there is an issue when using this type for a column that
    allows NULL values. The ORM maps NULL values to Python None value. But
    if you store a None value as a pickled value you can then not tell the
    difference between them when you extract the value. Therefore, make
    the column NOT NULL whenever possible.
    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return loads(value.encode("ascii"))


class JsonText(types.TypeDecorator):
    """For columns that store a JSON encoded data structure in a TEXT field.
    """
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def process_result_value(self, value, dialect):
        return json.loads(value)

# special enumeration types

class TestCaseStatus(types.TypeDecorator):
    """TestCase status indicates test case lifecycle state."""

    impl = INTEGER
    enumerations = Enums("new", "reviewed", "deprecated")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


class TestCaseType(types.TypeDecorator):
    """TestCase test type. Where in the cycle this test is applied."""

    impl = INTEGER
    enumerations = Enums("unit", "system", "integration", "regression", "performance")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[1]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))



class PriorityType(types.TypeDecorator):
    """TestCase priority type."""

    impl = INTEGER
    enumerations = Enums("P_UNKNOWN", "P1", "P2", "P3", "P4", "P5")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


TESTRESULTS = Enums(PASSED=1, FAILED=0, INCOMPLETE=-1, ABORT=-2, NA=-3, EXPECTED_FAIL=-4)
TESTRESULTS.sort()

class TestResultType(types.TypeDecorator):
    """Possible status of test case or test runner objects."""

    impl = INTEGER
    enumerations = TESTRESULTS

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[1]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


OBJECTTYPES = Enums("UseCase", "TestSuite", "Test", "TestRunner", "unknown")
OBJ_USECASE, OBJ_TESTSUITE, OBJ_TEST, OBJ_TESTRUNNER, OBJ_UNKNOWN = OBJECTTYPES

class TestObjectType(types.TypeDecorator):
    """Possible test runner objects that produce results."""

    impl = INTEGER
    enumerations = OBJECTTYPES

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[4]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))



class ValueType(types.TypeDecorator):
    """base types of attribute value types. Usually a value_type column
    name.
    """

    impl = INTEGER
    enumerations = Enums("object", "string", "unicode",
                    "integer", "float", "boolean")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


def validate_value_type(value_type, value):
    try:
        return _VALIDATOR_MAP[value_type](value)
    except (ValueError, TypeError) as err:
        raise ValidationError(err)

### attribute base type validation and conversion
def _validate_float(value):
    return float(value)

def _validate_int(value):
    return int(value)

def _validate_boolean(value):
    if isinstance(value, basestring):
        value = value.lower()
        if value in ("on", "1", "true", "t", "y", "yes"):
            return True
        elif value in ("off", "0", "false", "f", "n", "no"):
            return False
        else:
            raise ValidationError("Invalid boolean string: {!r}".format(value))
    else:
        return bool(value)

def _validate_object(value):
    if isinstance(value, basestring):
        try:
            return eval(value, {}, {})
        except:
            ex, val, tb = sys.exc_info()
            del tb
            raise ValidationError("Could not evaluate object: {}: {}".format(ex,__name__, val))
    else:
        return value

def _validate_string(value):
    return str(value)

def _validate_unicode(value):
    return unicode(value)

_VALIDATOR_MAP = {
    0: _validate_object,
    1: _validate_string,
    2: _validate_unicode,
    3: _validate_int,
    4: _validate_float,
    5: _validate_boolean,
}


class LikelihoodType(types.TypeDecorator):
    """Approximate likelihood (probability quartile) that an event may occur."""

    impl = INTEGER
    enumerations = Enums("Unknown", "VeryLikely", "Likely", "Possible", "Unlikely", "VeryUnlikely")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


class SeverityType(types.TypeDecorator):
    """Severity, or impact that an item may have on something if it did not exist."""

    impl = INTEGER
    enumerations = Enums("Unknown", "MajorLoss", "MinorLoss", "MinorLossHasReplacement",
            "CauseDifficulty", "Annoyance", "Trivial")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


