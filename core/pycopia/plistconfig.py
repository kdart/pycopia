#!/usr/bin/python2
# -*- coding: utf-8 -*-
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
Config object backed by a property list file. A property list file is an XML
format text file using Apple's Property List DTD (PropertyList-1.0.dtd).
"""

from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

import os
import re
import plistlib


class AutoAttrDict(dict):
    """A dictionary with attribute-style access and automatic container node creation.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __setitem__(self, key, value):
        return super(AutoAttrDict, self).__setitem__(key, value)

    def __getitem__(self, name):
        try:
            return super(AutoAttrDict, self).__getitem__(name)
        except KeyError:
            d = AutoAttrDict()
            super(AutoAttrDict, self).__setitem__(name, d)
            return d

    def __delitem__(self, name):
        return super(AutoAttrDict, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__

    def copy(self):
        return AutoAttrDict(self)

    # perform shell-like variable expansion
    def expand(self, value):
        if '$' not in value:
            return value
        i = 0
        while 1:
            mo = _var_re.search(value, i)
            if not mo:
                return value
            i, j = mo.span(0)
            oname = vname = mo.group(1)
            if vname.startswith('{') and vname.endswith('}'):
                vname = vname[1:-1]
            tail = value[j:]
            value = value[:i] + str(self.get(vname, "$"+oname))
            i = len(value)
            value += tail

    def tofile(self, path_or_file):
        write_config(self, path_or_file)


_var_re = re.compile(r'\$([a-zA-Z0-9_\?]+|\{[^}]*\})')

def read_config_from_string(pstr):
    d = plistlib.readPlistFromString(pstr)
    return _convert_dict(d)

def read_config(path_or_file):
    """Read a property list config file."""
    d = plistlib.readPlist(path_or_file)
    return _convert_dict(d)

def _convert_dict(d):
    for key, value in d.iteritems():
        if isinstance(value, dict):
            d[key] = _convert_dict(value)
    return AutoAttrDict(d)

def write_config_to_string(conf):
    return plistlib.writePlistToString(conf)

def write_config(conf, path_or_file):
    """Write a property list config file."""
    plistlib.writePlist(conf, path_or_file)


def get_config(filename=None, init=None):
    """Get an existing or new plist config object.

    Optionally initialize from another dictionary.
    """
    if init is not None:
        return _convert_dict(init)
    if filename is None:
        return AutoAttrDict()
    if os.path.exists(filename):
        return read_config(filename)
    else:
        d = AutoAttrDict()
        write_config(d, filename)
        return d



if __name__ == "__main__":
    cf = get_config()
    cf.parts.program.flags.flagname = 2
    cf.parts.program.path = "$BASE/program"
    cf.parts.BASE = "bin"
    assert cf.parts.program.flags.flagname == 2
    assert cf.parts.program.path == "$BASE/program"
    assert cf.parts.expand(cf.parts.program.path) == "bin/program"
    cf.tofile("/tmp/testplist.plist")
    del cf
    cf = read_config("/tmp/testplist.plist")
    assert cf.parts.program.flags.flagname == 2
    assert cf.parts.program.path == "$BASE/program"
    assert cf.parts.expand(cf.parts.program.path) == "bin/program"
    cf.parts.program.flags.flagname = 3
    assert cf.parts.program.flags.flagname == 3
    cf.tofile("/tmp/testplist.plist")
    del cf
    cf = read_config("/tmp/testplist.plist")
    assert cf.parts.program.flags.flagname == 3


