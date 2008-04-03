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
Helpers and tools for dictionary objects. Various useful dictionary
variants live here.

"""

class AttrDictWrapper(object):
    """Wraps any mapping object with the ability to get to its contents using
    attribute access syntax (dot). Note that you cannot have any contained keys
    that match an attribute name."""
    def __init__(self, mapping=None):
        self.__dict__["_mapping"] = mapping or {}

    # attribute-style access 
    def __getattribute__(self, key):
        try:
            return super(AttrDictWrapper, self).__getattribute__(key)
        except AttributeError:
            try:
                return self.__dict__["_mapping"].__getattribute__( key)
            except AttributeError:
                try:
                    obj = self.__dict__["_mapping"].__getitem__(key)
                    if hasattr(obj, "keys"):
                        return self.__class__(obj) # wrap the returned mapping object also
                    else:
                        return obj
                except KeyError, err:
                    raise AttributeError, "no attribute or key '%s' found (%s)." % (key, err)

    def __setattr__(self, key, obj):
        if self.__class__.__dict__.has_key(key): # property access
            object.__setattr__(self, key, obj)
        else:
            return self.__dict__["_mapping"].__setitem__(key, obj)

    def __delattr__(self, key):
        try: # to force handling of properties
            self.__dict__["_mapping"].__delitem__(key)
        except KeyError:
            object.__delattr__(self, key)

    def __getitem__(self, key):
        obj = self._mapping[key]
        if hasattr(obj, "keys"):
            return self.__class__(obj) # wrap the returned mapping object also
        else:
            return obj

    def __delitem__(self, key):
        del self._mapping[key]

    def __setitem__(self, key, obj):
        self._mapping[key] = obj


class AttrDict(dict):
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary.  """
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
        return super(AttrDict, self).__setitem__(key, value)

    def __getitem__(self, name):
        return super(AttrDict, self).__getitem__(name)

    def __delitem__(self, name):
        return super(AttrDict, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__

    def copy(self):
        return AttrDict(self)


class AttrDictDefault(dict):
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary. Returns a default entry if key is not found. """
    def __init__(self, init={}, default=None):
        dict.__init__(self, init)
        self.__dict__["_default"] = default

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s, %r)" % (self.__class__.__name__, dict.__repr__(self), 
            self.__dict__["_default"])

    def __setitem__(self, key, value):
        return super(AttrDictDefault, self).__setitem__(key, value)

    def __getitem__(self, name):
        try:
            return super(AttrDictDefault, self).__getitem__(name)
        except KeyError:
            return self.__dict__["_default"]

    def __delitem__(self, name):
        return super(AttrDictDefault, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__

    def copy(self):
        return self.__class__(self, self.__dict__["_default"])

    def get(self, default=None):
        df = default or self.__dict__["_default"]
        return super(AttrDictDefault, self).get(name, df)


class ObjectCache(dict):
    """A dict that caches objects. Adds a method, get_object, that
    works like get() but takes a constructor callable that is called if
    the object is not found here.  
    """
    def get_object(self, index, constructor, **kwargs):
        try:
            obj = self[index]
        except KeyError:
            obj = constructor(**kwargs)
            self[index] = obj
        return obj


# The following MergeDict and others copied from django:

# Copyright (c) 2005, the Lawrence Journal-World
# All rights reserved.

# Forked since these could be useful for non-web apps as well.

class MultiValueDictKeyError(KeyError):
    pass

class MergeDict(object):
    """
    A simple class for creating new "virtual" dictionaries that actualy look
    up values in more than one dictionary, passed in the constructor.
    """
    def __init__(self, *dicts):
        self.dicts = dicts

    def __getitem__(self, key):
        for dict in self.dicts:
            try:
                return dict[key]
            except KeyError:
                pass
        raise KeyError

    def __contains__(self, key):
        return self.has_key(key)

    def get(self, key, default):
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key):
        for dict in self.dicts:
            try:
                return dict.getlist(key)
            except KeyError:
                pass
        raise KeyError

    def items(self):
        item_list = []
        for dict in self.dicts:
            item_list.extend(dict.items())
        return item_list

    def has_key(self, key):
        for dict in self.dicts:
            if dict.has_key(key):
                return True
        return False


class SortedDict(dict):
    "A dictionary that keeps its keys in the order in which they're inserted."
    def __init__(self, data=None):
        if data is None: data = {}
        dict.__init__(self, data)
        self.keyOrder = data.keys()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key not in self.keyOrder:
            self.keyOrder.append(key)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.keyOrder.remove(key)

    def __iter__(self):
        for k in self.keyOrder:
            yield k

    def items(self):
        return zip(self.keyOrder, self.values())

    def keys(self):
        return self.keyOrder[:]

    def values(self):
        return [dict.__getitem__(self, k) for k in self.keyOrder]

    def update(self, dict):
        for k, v in dict.items():
            self.__setitem__(k, v)

    def setdefault(self, key, default):
        if key not in self.keyOrder:
            self.keyOrder.append(key)
        return dict.setdefault(self, key, default)

    def value_for_index(self, index):
        "Returns the value of the item at the given zero-based index."
        return self[self.keyOrder[index]]


class MultiValueDict(dict):
    """
    A subclass of dictionary customized to handle multiple values for the same key.

    >>> d = MultiValueDict({'name': ['Adrian', 'Simon'], 'position': ['Developer']})
    >>> d['name']
    'Simon'
    >>> d.getlist('name')
    ['Adrian', 'Simon']
    >>> d.get('lastname', 'nonexistent')
    'nonexistent'
    >>> d.setlist('lastname', ['Holovaty', 'Willison'])

    This class exists to solve the irritating problem raised by cgi.parse_qs,
    which returns a list for every key, even though most Web forms submit
    single name-value pairs.
    """
    def __init__(self, key_to_list_mapping=()):
        dict.__init__(self, key_to_list_mapping)

    def __repr__(self):
        return "<MultiValueDict: %s>" % dict.__repr__(self)

    def __getitem__(self, key):
        """
        Returns the last data value for this key, or [] if it's an empty list;
        raises KeyError if not found.
        """
        try:
            list_ = dict.__getitem__(self, key)
        except KeyError:
            raise MultiValueDictKeyError, "Key %r not found in %r" % (key, self)
        try:
            return list_[-1]
        except IndexError:
            return []

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, [value])

    def __copy__(self):
        return self.__class__(dict.items(self))

    def __deepcopy__(self, memo=None):
        import copy
        if memo is None: memo = {}
        result = self.__class__()
        memo[id(self)] = result
        for key, value in dict.items(self):
            dict.__setitem__(result, copy.deepcopy(key, memo), copy.deepcopy(value, memo))
        return result

    def get(self, key, default=None):
        "Returns the default value if the requested data doesn't exist"
        try:
            val = self[key]
        except KeyError:
            return default
        if val == []:
            return default
        return val

    def getlist(self, key):
        "Returns an empty list if the requested data doesn't exist"
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return []

    def setlist(self, key, list_):
        dict.__setitem__(self, key, list_)

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def setlistdefault(self, key, default_list=()):
        if key not in self:
            self.setlist(key, default_list)
        return self.getlist(key)

    def appendlist(self, key, value):
        "Appends an item to the internal list associated with key"
        self.setlistdefault(key, [])
        dict.__setitem__(self, key, self.getlist(key) + [value])

    def items(self):
        """
        Returns a list of (key, value) pairs, where value is the last item in
        the list associated with the key.
        """
        return [(key, self[key]) for key in self.keys()]

    def lists(self):
        "Returns a list of (key, list) pairs."
        return dict.items(self)

    def values(self):
        "Returns a list of the last value on every key list."
        return [self[key] for key in self.keys()]

    def copy(self):
        "Returns a copy of this object."
        return self.__deepcopy__()

    def update(self, *args, **kwargs):
        "update() extends rather than replaces existing key lists. Also accepts keyword args."
        if len(args) > 1:
            raise TypeError, "update expected at most 1 arguments, got %d", len(args)
        if args:
            other_dict = args[0]
            if isinstance(other_dict, MultiValueDict):
                for key, value_list in other_dict.lists():
                    self.setlistdefault(key, []).extend(value_list)
            else:
                try:
                    for key, value in other_dict.items():
                        self.setlistdefault(key, []).append(value)
                except TypeError:
                    raise ValueError, "MultiValueDict.update() takes either a MultiValueDict or dictionary"
        for key, value in kwargs.iteritems():
            self.setlistdefault(key, []).append(value)

