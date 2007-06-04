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

"""$URL$
$Id$
"""
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Support Persistent data with type enforcement and default values for attributes.

import durus.persistent as persistent

MANDATORY = "Mandatory"
CONTAINER = "CONTAINER"

class PersistentData(persistent.Persistent):
    _ATTRS = {}
    MANDATORY = MANDATORY
    CONTAINER = CONTAINER
    def __init__(self, **kwargs):
        super(PersistentData, self).__init__()
        for aname, (typ, default) in self.__class__._ATTRS.items():
            if aname in kwargs:
                value = kwargs[aname]
                if value is not None:
                    value = typ(value)
                super(PersistentData, self).__setattr__(aname, value)
            else:
                if default is MANDATORY:
                    raise ValueError, "mandatory attribute %r not provided." % (aname,)
                elif default is CONTAINER: # created empty first time
                    super(PersistentData, self).__setattr__(aname, typ())
                elif default is not None: # no default
                    super(PersistentData, self).__setattr__(aname, default)
        self.__dict__["_cache"] = {}

    def __repr__(self):
        s = ["%s(" % (self.__class__.__name__,)]
        for aname, (typ, default) in self.__class__._ATTRS.items():
            s.append("%s=%s(%r), " % (aname, typ.__name__, getattr(self, aname, default)))
        s.append(")")
        return "".join(s)

    def __str__(self):
        return "<%s>" % (self.__class__.__name__,)

    def __getattribute__(self, name):
        try:
            return super(PersistentData, self).__getattribute__(name)
        except AttributeError, err:
            typ, default = self.__class__._ATTRS.get(name, (None, None))
            if typ is not None:
                return default
            raise

    def __setattr__(self, name, value):
        typ, default = self.__class__._ATTRS.get(name, (None, None))
        if typ is not None and value is not None:
            if typ in (int, long, float, str, unicode):
                value = typ(value)
            else:
                assert issubclass(type(value), typ), "PersistentData: wrong type for attribute %r!" % name
        super(PersistentData, self).__setattr__(name, value)

    def _get_cache(self, name, constructor):
        try:
            return self.__dict__["_cache"][name]
        except KeyError:
            obj = constructor()
            self.__dict__["_cache"][name] = obj
            return obj

    def _del_cache(self, name, destructor=None):
        try:
            obj = self.__dict__["_cache"].pop(name)
        except KeyError:
            return
        else:
            if destructor:
                destructor(obj)

    def clear_cache(self):
        self.__dict__["_cache"].clear()

