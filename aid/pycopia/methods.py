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

# Modified by Keith Dart to conform to Pycopia style.


"""Method introspection.
"""

__author__ = 'keith@kdart.com (Keith Dart)'
__original_author__ = 'dart@google.com (Keith Dart)'

import types

from pycopia.aid import NULL


# flags
CO_OPTIMIZED =              0x0001
CO_NEWLOCALS =              0x0002
CO_VARARGS =                0x0004
CO_VARKEYWORDS =            0x0008
CO_NESTED =                 0x0010
CO_GENERATOR =              0x0020
CO_FUTURE_DIVISION =        0x2000
CO_FUTURE_ABSOLUTE_IMPORT = 0x4000 # do absolute imports by default
CO_FUTURE_WITH_STATEMENT =  0x8000


class MethodSignature(object):
    """Introspect a method or function and store the formal arguments.

    Attributes::

        :name:      the name of the original function or method.
        :arguments: a list of 2-tuples, (argument name, default value). If
                    there is no default value defined the value will be NULL object.

    """
    def __init__(self, method):
        self._varargsname = None
        self._varkeywordsname = None
        self._inspect(method)

    def _inspect(self, method):
        if type(method) is types.MethodType:
            func = method.im_func
            varstart = 1 # to chop the instance (self)
        elif type(method) is types.FunctionType:
            func = method
            varstart = 0
        else:
            raise ValueError("Invalid object type.")
        code = func.func_code
        # formal names
        argc = code.co_argcount
        if code.co_flags & CO_VARARGS:
            self._varargsname = code.co_varnames[argc]
            argc += 1
        if code.co_flags & CO_VARKEYWORDS:
            self._varkeywordsname = code.co_varnames[argc]
        self.name = func.func_name
        varnames = list(code.co_varnames)[varstart:code.co_argcount]
        if func.func_defaults:
            defaults = func.func_defaults
            self._args = varnames[:-len(defaults)]
            self._kwargs = zip(varnames[len(varnames)-len(defaults):], defaults)
        else:
            self._args = varnames
            self._kwargs = []

    def __str__(self):
        return "%s(%s)" % (self.name,
                ", ".join(map(str, self._args)+map(lambda t: "%s=%r" % t, self._kwargs))
                )

    def has_arguments(self):
        return bool(self._args) or bool(self._kwargs)

    # object evaluates to True if signature has arguments.
    __nonzero__ = has_arguments

    def get_arguments(self):
        return [(arg, NULL) for arg in self._args]+self._kwargs

    # TODO(dart) still needs work to handle varargs grouping.
    def get_keyword_arguments(self, args=(), kwargs=None):
        """Return a dict with arguments filled in."""
        assert len(args) >= len(self._args), "Not enough positional arguments."
        kw = dict(zip(self._args, args) + self._kwargs)
        if kwargs:
            for key, default in self._kwargs:
                kw[key] = kwargs.get(key, default)
        if len(args) > len(self._args):
            for (name, default), arg in zip(self._kwargs, args[len(self._args):]):
                kw[name] = arg
        return kw

    arguments = property(get_arguments)
    kwarguments = property(lambda s: s._kwargs[:])

    args = property(lambda s: tuple(s._args))
    kwargs = property(lambda s: dict(s._kwargs))

