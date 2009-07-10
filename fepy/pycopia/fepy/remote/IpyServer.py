# ironpython
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab:ft=python
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
Basic remote interface for IronPython servers. This module must be run in
IronPython that has a Pyro installation. Abstracts the Pyro requirements.
Users of this module only have to subclass IronPythonBase class, add the
custom methods, and call the run_server function with it. The service name
is the class name and will appear in the name server.

"""

import sys
import clr

import Pyro.core
import Pyro.naming
from Pyro.errors import NamingError



_EXIT = False

class IronPythonBase(Pyro.core.ObjBase):

    def version(self):
        return sys.version

    def alive(self):
        return True

    def suicide(self):
        "Kill myself. The server manager may ressurect me. How nice."
        global _EXIT
        _EXIT = True

    def eval(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<IronPython>', 'eval')
            rv = eval(code, globals(), vars(self))
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return rv

    def pyexec(self, snippet):
        try:
            code = compile(str(snippet) + '\n', '<IronPython>', 'exec')
            exec code in globals(), vars(self)
        except:
            t, v, tb = sys.exc_info()
            return '*** %s (%s)' % (t, v)
        else:
            return

    def startfile(self, prog):
        os.startfile(prog)

    def AddReference(self, name):
        clr.AddReference(name)
        mod = Import(name)
        sys.modules[__name__].__dict__[name] = mod


def Import(modname):
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    mod = __import__(modname)
    pathparts = modname.split(".")
    for part in pathparts[1:]:
        mod = getattr(mod, part)
    sys.modules[modname] = mod
    return mod


def get_class(path):
    """Get a class object.

    Return a class object from a string specifiying the full package and
    name path.
    """
    [modulename, classname] = path.rsplit(".", 1)
    mod = Import(modulename)
    return getattr(mod, classname)


def run_server(klass):
    myname = klass.__name__
    Pyro.core.initServer()
    ns=Pyro.naming.NameServerLocator().getNS()
    daemon=Pyro.core.Daemon()
    daemon.useNameServer(ns)
    try:
        ns.unregister(myname)
    except NamingError:
        pass
    uri=daemon.connect(klass(), myname)
    daemon.requestLoop(lambda: not _EXIT)
    daemon.shutdown()



def main(argv):
    if len(argv) > 1:
        klass = get_class(argv[1])
        run_server(klass)
    else:
        run_server(IronPythonBase)


if __name__ == "__main__":
    main(sys.argv)

