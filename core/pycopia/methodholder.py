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

from basicconfig import ConfigHolder

class MethodHolder(ConfigHolder):
    """MethodHolder(method)
Allows for the delayed invocation of methods, and easy introspection of
formal parameters for user interfaces.
    """
    def __init__(self, method=None, **kwargs):
        super(MethodHolder, self).__init__()
        if method is None:
            return
        elif type(method) is str:
            self.__dict__["_methodname"] = method
            self.lock()
            self.update(kwargs)
        elif type(method) is _UnboundMethodType:
            self.__dict__["_methodname"] = method.im_func.func_name
            # formal names
            varnames = list(method.im_func.func_code.co_varnames)[:method.im_func.func_code.co_argcount]
            varnames.reverse()
            df = method.im_func.func_defaults or []
            defaults = list(df) ; defaults.reverse()
            for name, deflt in map(None, varnames, defaults):
                self[name] = deflt
            del self[varnames[-1]] # remove the self reference
            self.lock()
            self.update(kwargs)
        else:
            raise ValueError, "MethodHolder: invalid initializer type"

    def __str__(self):
        m = self.__dict__["_methodname"]
        params = ", ".join(["%s=%r" % (n, v) for n, v in self.items()])
        return "%s: %s" % (m, params)

    def __repr__(self):
        return "%s(%r, %s)" % (self.__class__.__name__, self.__dict__["_methodname"],
        ", ".join(["%s=%r" % (n, v) for n, v in self.items()]) )

    def _methodname(self):
        return self.__dict__["_methodname"]

    methodname = property(_methodname, None, None, "Method name")

    def __call__(self, instance):
        meth = getattr(instance, self.__dict__["_methodname"])
        return apply(meth, (), self)

    def copy(self):
        new = MethodHolder()
        for key, val in self.items():
            new[key] = val
        new.__dict__["_methodname"] = self.__dict__["_methodname"]
        new.lock()
        return new

    def update(self, other):
        for k in other.keys():
            self[k] = other[k]

_UnboundMethodType = type(MethodHolder.copy)


def _test(argv):
    class TestMe(object):
        def mymethod(self, arg1=1, arg2=2, arg3=3):
            print arg1, arg2, arg3

    mh = MethodHolder(TestMe.mymethod)
    print mh

if __name__ == "__main__":
    import sys
    _test(sys.argv)

