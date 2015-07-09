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

"""
Functions to aid Python development.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


import sys
import os
import imp

# These days we deal a lot with URLs, so import a URL parser/generator as well.
from pycopia.urlparse import UniversalResourceLocator as URL

PYTHON = os.environ.get("PYTHONBIN", sys.executable) # set PYTHONBIN for alternate interpreter


def run_config(cfstring, param):
    if not cfstring:
        print ("No command string defined to run {0}.".format(param), file=sys.stderr)
        return
    try:
        cmd = cfstring % param
    except TypeError: # no %s in cfstring, so just stick the param on the end
        cmd = "%s %s" % (cfstring, param)
    print("CMD:", repr(cmd))
    return os.system(cmd)


def pyterm(filename="", interactive=1):
    # Allow running remotely via ssh.
    if "://" in filename:
        url = URL(filename)
        if url.scheme in ("scp", "sftp"): # vim remote file
            # Assumes remote dev environment is the same as local one.
            path = url.path[1:]
            if not path.startswith("/"): # from HOME
                if url.user:
                    user = url.user
                else:
                    user = os.environ["USER"]
                path = "/home/{}/{}".format(user, path)
            remcmd = python_command(path, interactive)
            if url.user:
                cmd = 'ssh -t {}@{} {}'.format(url.user, url.host, remcmd)
            else:
                cmd = 'ssh -t {} {}'.format(url.host, remcmd)
        else:
            return "Can't handle scheme: " + url.scheme
    else:
        cmd = python_command(filename, interactive)
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)


def python_command(name, interactive=1):
    modname = module_from_path(name)
    if modname:
        return "{} {} -m '{}' ".format(PYTHON, "-i" if interactive else "", modname)
    else:
        return "{} {} '{}' ".format(PYTHON, "-i" if interactive else "", name)


def xterm(cmd="/bin/sh"):
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)


def edit(modname):
    """
Opens the $XEDITOR with the given module source file (if found).
    """
    filename = find_source_file(modname)
    if filename:
        ed = get_editor()
        return run_config(ed, filename)
    else:
        print ("Could not find source to {0}.".format(modname), file=sys.stderr)


def edit_import_line(importline):
    """Find the module referenced by the import source line and open in editor."""
    filename = find_source_file_from_import_line(importline)
    if filename:
        ed = get_editor()
        return run_config(ed, filename)
    else:
        print ("Could not find source for {0}.".format(importline.strip()), file=sys.stderr)


def view(modname):
    """
Opens the $[X]VIEWER with the given module source file (if found).
    """
    filename = find_source_file(modname)
    if filename:
        ed = get_viewer()
        return run_config(ed, filename)
    else:
        print ("Could not find source to %s." % modname, file=sys.stderr)

def get_editor():
    if "DISPLAY" in os.environ:
        ed = os.environ.get("XEDITOR", None)
    else:
        ed = os.environ.get("EDITOR", None)
    if ed is None:
        ed = get_input("Use which editor?", "/bin/vi")
    return ed

def get_viewer():
    if "DISPLAY" in os.environ:
        ed = os.environ.get("XVIEWER", None)
    else:
        ed = os.environ.get("VIEWER", None)
    if ed is None:
        ed = get_input("Use which viewer?", "/usr/bin/view")
    return ed

def exec_editor(*names):
    """Runs your configured editor on a supplied list of files. Uses exec,
there is no return!"""
    ed = get_editor()
    if ed.find("/") >= 0:
        os.execv(ed, (ed,)+names)
    else:
        os.execvp(ed, (ed,)+names)

def open_url(url):
    """Opens the given URL in an external viewer. """
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("BROWSER"), url)
    else:
        return run_config(os.environ.get("CBROWSER"), url)

def find_source_file(modname, path=None):
    if "." in modname:
        pkgname, modname = modname.rsplit(".", 1)
        pkg = find_package(pkgname)
        return find_source_file(modname, pkg.__path__)
    try:
        fo, fpath, (suffix, mode, mtype) = imp.find_module(modname, path)
    except ImportError:
        ex, val, tb = sys.exc_info()
        print("{} => {}: {}!".format(modname, ex.__name__, val), file=sys.stderr)
        return None
    if mtype == imp.PKG_DIRECTORY:
        fo, ipath, desc = imp.find_module("__init__", [fpath])
        fo.close()
        return ipath
    elif mtype == imp.PY_SOURCE:
        return fpath
    else:
        return None


def find_source_file_from_import_line(line):
    if line.startswith("import "):
        return find_source_file(line[7:].strip())
    elif line.startswith("from "):
        fromparts = line.split()
        return find_from_package(fromparts[1], fromparts[3])
    else:
        return None

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


def find_from_package(pkgname, modname):
    pkg = find_package(pkgname)
    try:
        fo, fpath, (suffix, mode, mtype) = imp.find_module(modname, pkg.__path__)
    except ImportError:
        ex, val, tb = sys.exc_info()
        print("{} => {}: {}!".format(modname, ex.__name__, val), file=sys.stderr)
        return None
    fo.close()
    if mtype == imp.PY_SOURCE:
        return fpath
    else:
        return None


def module_from_path(fname):
    """Find and return the module name given a full path name.
    Return None if file name not in the package path.
    """
    dirname, basename = os.path.split(fname)
    for p in sys.path:
        if fname.startswith(p):
            pkgname = ".".join(dirname[len(p)+1:].split("/"))
            if pkgname:
                return pkgname + "." + os.path.splitext(basename)[0]
            else:
                return os.path.splitext(basename)[0]
    return None


def open_chm(search):
    """Opens the given search term with a CHM viewer. """
    if "DISPLAY" in os.environ:
        book = os.path.expandvars(os.environ.get("CHMBOOK",
                '$HOME/.local/share/devhelp/books/python321rc1.chm'))
        return run_config(os.environ.get("CHMVIEWER", 'kchmviewer --search %s "%s"'), (search, book))
    else:
        print ("open_chm: No CHM viewer for text mode.", file=sys.stderr)

def open_file(filename):
    return open_url("file://"+filename)


def get_object_name(object):
    objtype = type(object)
    if objtype is str:
        return object
    elif objtype is types.ModuleType or objtype is types.BuiltinFunctionType:
        return object.__name__
    else:
        print ("get_object_name: can't determine object name", file=sys.stderr)
        return None


def show_chm_doc(object, chooser=None):
    name = get_object_name(object)
    if name is None:
        return
    open_chm(name)

showdoc = show_chm_doc

# XXX
if __name__ == "__main__":
    from pycopia import autodebug
    for testname in (
            "import re\n",
            "import pycopia.aid\n",
            "import pycopia.WWW\n",
            "import pycopia.WWW.XHTML\n",
            "from pycopia import aid\n",
            "from pycopia.OS import IOCTL\n",
            "from pycopia.WWW import XHTML\n",
            "import puremvc\n",
            "import puremvc.patterns\n",
            "import puremvc.patterns.proxy\n",
            "import Pyro4\n",
#            "import sqlalchemy\n",
#            "from sqlalchemy import sql\n",
#            "import sqlalchemy.sql\n",
            ):
        print(testname.strip(), "=>", find_source_file_from_import_line(testname))

