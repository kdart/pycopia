#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2011  Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
Functions to aid Python development.
"""

import sys
import os

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
            remcmd = "{} {} '{}' ".format(PYTHON, "-i" if interactive else "", url.path[1:]) # chop leading slash
            if url.user:
                cmd = 'ssh -t {}@{} {}'.format(url.user, url.host, remcmd)
            else:
                cmd = 'ssh -t {} {}'.format(url.host, remcmd)
        else:
            return "Can't handle scheme: " + url.scheme
    else:
        cmd = "{} {} '{}' ".format(PYTHON, "-i" if interactive else "", filename)
    if "DISPLAY" in os.environ:
        return run_config(os.environ.get("XTERM"), cmd)
    else:
        return os.system(cmd)

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

def find_source_file(modname):
    try:
        return getsourcefile(modname)
    except TypeError:
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

