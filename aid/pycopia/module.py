#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=0:tw=74:smarttab:expandtab
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

# Modified by Keith Dart to conform to Pycopia style.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""Common utility methods and objects for Droid.
"""

__author__ = 'keith@dartworks.biz (Keith Dart)'
__original__author__ = 'dart@google.com (Keith Dart)'

import sys
import imp


class ModuleImportError(ImportError):
    """Raised when a test module could not be located."""


class ObjectImportError(ImportError):
    """Raised when a test object could not be located."""


def Import(modname):
    """Improved __import__ function that returns fully initialized subpackages."""
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    __import__(modname)
    return sys.modules[modname]


def get_module(name):
    """
    Use the Python import function to get a Python package module by name.
    Raises ModuleImportError if the module could not be found.

    Arguments:
        name: A string. The name of the module to import and run.

    Returns:
        A python module.
    """
    try:
        return sys.modules[name]
    except KeyError:
        pass
    try:
        __import__(name)
    except ImportError as err:
        raise ModuleImportError("Error loading: %s (%s)." % (name, err))
    else:
        return sys.modules[name]


def get_object(name):
    """Get an object from a Python module, or a module itself.

    Arguments:
        name:
            Python path name of object. Usually a module or a class in a module.

    Returns:
        An object identified by the given path name. may raise AttributeError
        or ModuleImportError if name not found.
    """
    try:
        return sys.modules[name]
    except KeyError:
        pass
    i = name.rfind(".")
    if i >= 0:
        try:
            __import__(name)
        except ImportError:
            pass
        else:
            return sys.modules[name]
        mod = get_module(name[:i]) # module name component
        try:
            return getattr(mod, name[i+1:]) # path tail is an object inside module
        except AttributeError:
            raise ObjectImportError("%r not found in %r." % (name[i+1:], mod.__name__))
    else:
        return get_module(name) # basic module name


def get_class(path):
    """Get a class object.

    Return a class object from a string specifiying the full package and
    name path.
    """
    modulename, classname = path.rsplit(".", 1)
    mod = Import(modulename)
    return getattr(mod, classname)


def get_objects(namelist):
    """Return a list of objects.

    Arguments:
        namelist:
            A list of object names, as strings.

    Returns:
        A tuple of two lists. First list contains object instances
        corresponding to the given names. May be shorter than the provided
        list due to objects not being found.  Second list is list of
        errors for names that could not be produced.
    """
    rv = []
    errors = []
    for name in namelist:
        try:
            obj = get_object(name)
        except (ModuleImportError, ObjectImportError) as err:
            errors.append(err)
        else:
            rv.append(obj)
    return rv, errors


def _iter_subpath(packagename):
    s = 0
    while True:
        i = packagename.find(".", s + 1)
        if i < 0:
            yield packagename
            break
        yield packagename[:i]
        s = i + 1

def _load_package(packagename, basename, searchpath):
    fo, _file, desc = imp.find_module(packagename, searchpath)
    if basename:
        fullname = "{}.{}".format(basename, packagename)
    else:
        fullname = packagename
    return imp.load_module(fullname, fo, _file, desc)


def find_package(packagename, searchpath=None):
    """Find a package by fully qualified name."""
    try:
        return sys.modules[packagename]
    except KeyError:
        pass
    for pkgname in _iter_subpath(packagename):
        if "." in pkgname:
            basepkg, subpkg = pkgname.rsplit(".", 1)
            pkg = sys.modules[basepkg]
            _load_package(subpkg, basepkg, pkg.__path__)
        else:
            try:
                sys.modules[pkgname]
            except KeyError:
                _load_package(pkgname, None, searchpath)
    return sys.modules[packagename]


def find_module(modname, path=None):
    """Find a module, also handling subpackages.
    Similar to imp.find_module(), except works with subpackages.
    This does not load the module, so no side effects from the module. It
    does load the package, so any contents of __init__.py are run and may
    have side effects.

    Returns:
        fo     -- Open file object.
        fname  -- file name of the file found
        desc   -- a 3-tuple of extension, mode, and file type.
    """
    if "." in modname:
        pkgname, modname = modname.rsplit(".", 1)
        pkg = find_package(pkgname)
        return find_module(modname, pkg.__path__)
    try:
        info = imp.find_module(modname, path)
    except ImportError:
        return None
    return info

