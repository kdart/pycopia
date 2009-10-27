#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Extra database types.

"""

__all__ = [
    "PGArray", "PGBigInteger", "PGBinary", 
    "PGBit", "PGBoolean", "PGChar", "PGCidr", "PGDate", "PGDateTime", "PGFloat", "PGInet",
    "PGInteger", "PGInterval", "PGMacAddr", "PGNumeric", "PGSmallInteger",
    "PGString", "PGText", "PGTime", "PGUuid",
    "PickleText", "TestCaseStatus", "TestCaseType", "TestPriorityType", "ValueType",
    "TestResultType", "TestObjectType", 
    "validate_value_type",
]

import cPickle as pickle

from pycopia.aid import Enums

from sqlalchemy.databases.postgres import (PGArray, PGBigInteger, PGBinary, 
            PGBit, PGBoolean, PGChar, PGCidr, PGDate, PGDateTime, PGFloat, PGInet,
            PGInteger, PGInterval, PGMacAddr, PGNumeric, PGSmallInteger,
            PGString, PGText, PGTime, PGUuid)

from sqlalchemy import types


class ValidationError(AssertionError):
    pass


# custom column types.

class PickleText(types.TypeDecorator):
    """For columns that store Python objects in a TEXT column.

    Be aware there is an issue when using this type for a column that
    allows NULL values. The ORM maps NULL values to Python None value. But
    if you store a None value as a pickled value you can then not tell the
    difference between them when you extract the value. Therefore, make
    the column NOT NULL whenever possible.
    """

    impl = PGText

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return pickle.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return pickle.loads(value)


# special enumeration types

class TestCaseStatus(types.TypeDecorator):
    """TestCase status indicates test case lifecycle state."""

    impl = PGInteger
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

    impl = PGInteger
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



class TestPriorityType(types.TypeDecorator):
    """TestCase priority type."""

    impl = PGInteger
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

    impl = PGInteger
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


OBJECTTYPES = Enums("module", "TestSuite", "Test", "TestRunner", "unknown")

class TestObjectType(types.TypeDecorator):
    """Possible test runner objects that produce results."""

    impl = PGInteger
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

    impl = PGInteger
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
    except (ValueError, TypeError), err:
        raise ValidationError(err)

### attribute base type validation and conversion
def _validate_float(value):
    return float(value)

def _validate_int(value):
    return int(value)

def _validate_boolean(value):
    if type(value) is str:
        value = value.lower()
        if value in ("on", "1", "true", "t", "y", "yes"):
            return True
        elif value in ("off", "0", "false", "f", "n", "no"):
            return False
        else:
            raise ValidationError("Invalid boolean string")
    else:
        return bool(value)

def _validate_object(value):
    if type(value) is str:
        try:
            return eval(value, {}, {})
        except:
            return value
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


