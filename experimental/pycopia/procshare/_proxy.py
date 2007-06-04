# _proxy.py

# Submodule of the posh package, defining a factory function
# for creating proxy types based on shared types

from  types import UnboundMethodType
import _procshare_core as _core

class ProxyMethod(object):
    def __init__(self, inst, cls, mname):
        self.proxy_inst = inst
        self.proxy_cls = cls
        self.mname = mname
        self.cname = cls.__name__

    def __str__(self):
        if self.proxy_inst is None:
            return "<method '%s' of '%s' objects>" % \
                   (self.mname, self.cname)
        return "<method '%s' of '%s' object at %s>" % \
               (self.mname, self.cname, _core.address_of(self.proxy_inst))

    __repr__ = __str__

    def __call__(self, *args, **kwargs):
        if self.proxy_inst is None:
            # Call to unbound proxy method
            if (len(args) < 1) or not isinstance(args[0], self.proxy_cls):
                fmt = "unbound method %s.%s must be called" + \
                      "with %s instance as first argument"
                raise TypeError, fmt % (self.cname, self.mname, self.cname)
            return args[0]._call_method(self.mname, args[1:], kwargs);
        else:
            # Call to bound proxy method
            return self.proxy_inst._call_method(self.mname, args, kwargs);


class ProxyMethodDescriptor(object):
    def __init__(self, mname):
        self.mname = mname

    def __get__(self, inst, cls):
        return ProxyMethod(inst, cls, self.mname)

    def __set__(self, inst, value):
        raise TypeError, "read-only attribute"


method_desc_types = (type(list.__add__), type(list.append), UnboundMethodType)


def MakeProxyType(reftype):
    d = {"__slots__": []}
    for attrname in dir(reftype):
        if not hasattr(_core.Proxy, attrname):
            attr = getattr(reftype, attrname)
            if type(attr) in method_desc_types:
                d[attrname] = ProxyMethodDescriptor(attrname);
    name = reftype.__name__+"Proxy"
    return type(name, (_core.Proxy,), d)

