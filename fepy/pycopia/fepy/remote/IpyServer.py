# ironpython
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

