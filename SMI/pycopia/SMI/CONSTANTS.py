#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
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
Make available the SMI library constants for client applications.

"""

import sys

import _libsmi

# map libsmi constant values to RFC 2578 (and other) defined names for the
# enumeration's name. If not listed here then use the flag name itself.
_NAMES = {
    "SMI_BASETYPE_BITS":               "Bits",
    "SMI_BASETYPE_ENUM":              "Enumeration",
    "SMI_BASETYPE_FLOAT128":           "Float128",
    "SMI_BASETYPE_FLOAT32":            "Float32",
    "SMI_BASETYPE_FLOAT64":            "Float64",
    "SMI_BASETYPE_INTEGER32":          "Integer32",
    "SMI_BASETYPE_INTEGER64":          "Integer64",
    "SMI_BASETYPE_OBJECTIDENTIFIER":   "ObjectIdentifier",
    "SMI_BASETYPE_OCTETSTRING":        "OctetString",
    "SMI_BASETYPE_UNSIGNED32":         "Unsigned32",
    "SMI_BASETYPE_UNSIGNED64":         "Counter64",
    "SMI_ACCESS_NOT_ACCESSIBLE": "not-accessible",
    "SMI_ACCESS_NOTIFY": "accessible-for-notify",
    "SMI_ACCESS_READ_ONLY": "read-only",
    "SMI_ACCESS_READ_WRITE": "read-write",
    "SMI_STATUS_CURRENT": "current",
    "SMI_STATUS_DEPRECATED": "deprecated",
    "SMI_STATUS_OBSOLETE": "obsolete",

}

# pull C #defines from _libsmi C module, assign to Enum types. Override the
# default name with one from the _NAMES mapping, if it exists.
for name, value in vars(_libsmi).items():
    if name.startswith("SMI_") and type(value) is int:
        setattr(sys.modules[__name__], name, Enum(value, _NAMES.get(name, name)))
del name, value, _libsmi, sys, _NAMES


