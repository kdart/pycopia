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
Persistent mapping with attribute style access.

"""

from copy import copy
from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict

import sys

class PersistentAttrDict(Persistent):

    """
    Instance attributes:
      data : dict
    """
    data_is = dict

    def __init__(self, *args, **kwargs):
        self.__dict__["data"] = dict(*args, **kwargs)

    def __cmp__(self, other):
        if isinstance(other, PersistentAttrDict):
            return cmp(self.__dict__["data"], other.data)
        elif isinstance(other, PersistentDict):
            return cmp(self.__dict__["data"], other.data)
        else:
            return cmp(self.__dict__["data"], other)

    def __len__(self):
        return len(self.__dict__["data"])

    def __getitem__(self, key):
        return self.__dict__["data"][key]

    def __setitem__(self, key, value):
        self._p_note_change()
        self.__dict__["data"][key] = value

    def __delitem__(self, key):
        self._p_note_change()
        del self.__dict__["data"][key]

    # attribute-style access 
    def __getattribute__(self, key):
        try:
            return super(PersistentAttrDict, self).__getattribute__(key)
        except AttributeError:
            try:
                return self.__dict__[key]
            except KeyError:
                try:
                    return self.__dict__["data"].__getattribute__( key)
                except AttributeError:
                    try:
                        return self.__dict__["data"].__getitem__(key)
                    except KeyError, err:
                        raise AttributeError, "no attribute or key '%s' found (%s)." % (key, err)

    def __setattr__(self, key, obj):
        if key.startswith("_p_") or key.startswith("__"): # durus attributes
            super(PersistentAttrDict, self).__setattr__(key, obj)
        elif self.__dict__.has_key(key): # existing local attributes
            self.__dict__[key] = obj
        else: # set the data dict
            self.__dict__["data"].__setitem__(key, obj)
            self._p_note_change()

    def __delattr__(self, key):
        try: # to force handling of properties
            self.__dict__["data"].__delitem__(key)
            self._p_note_change()
        except KeyError:
            super(PersistentAttrDict, self).__delattr__(key)

    def clear(self):
        self._p_note_change()
        self.__dict__["data"].clear()

    def copy(self):
        if self.__class__ is PersistentAttrDict:
            return PersistentAttrDict(self.__dict__["data"])
        # Use the copy module to copy self without data, and then use the
        # update method to fill the data in the new instance.
        changed = self.get_p_changed()
        data = self.__dict__["data"]
        try:
            self.__dict__["data"] = {} # This is why we saved _p_changed.
            c = copy(self)
        finally:
            self.__dict__["data"] = data
            self._p_note_change(changed)
        c.update(self)
        return c

    def keys(self):
        return self.__dict__["data"].keys()

    def items(self):
        return self.__dict__["data"].items()

    def iteritems(self):
        return self.__dict__["data"].iteritems()

    def iterkeys(self):
        return self.__dict__["data"].iterkeys()

    def itervalues(self):
        return self.__dict__["data"].itervalues()

    def values(self):
        return self.__dict__["data"].values()

    def has_key(self, key):
        return self.__dict__["data"].has_key(key)

    def update(self, other):
        self._p_note_change()
        if isinstance(other, PersistentAttrDict) or isinstance(other, PersistentDict):
            self.__dict__["data"].update(other.data)
        elif isinstance(other, dict):
            self.__dict__["data"].update(other)
        else:
            for k, v in other.items():
                self[k] = v

    def get(self, key, failobj=None):
        return self.__dict__["data"].get(key, failobj)

    def set(self, key, value=None):
        self._p_note_change()
        self.__dict__["data"][key] = value

    def delete(self, key):
        self._p_note_change()
        del self.__dict__["data"][key]

    def rename(self, oldkey, newkey):
        self._p_note_change()
        obj = self.__dict__["data"][oldkey]
        self.__dict__["data"][newkey] = obj
        del self.__dict__["data"][oldkey]

    def setdefault(self, key, failobj=None):
        if key not in self.__dict__["data"]:
            self._p_note_change()
            self.__dict__["data"][key] = failobj
            return failobj
        return self.__dict__["data"][key]

    def pop(self, key, *args):
        self._p_note_change()
        return self.__dict__["data"].pop(key, *args)

    def popitem(self):
        self._p_note_change()
        return self.__dict__["data"].popitem()

    def __contains__(self, key):
        return key in self.__dict__["data"]

    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d
    fromkeys = classmethod(fromkeys)

    def __iter__(self):
        return iter(self.__dict__["data"])


