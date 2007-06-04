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
A generic CLI module. Make a link to this file in the $PYNMS_HOME/bin directory
that has a name that matches a key in the mapping below. The value of the
mapping should address a class object that will be wrapped with a GenericCLI.
Then you can interact with it.

This program is it's own configuration file.

"""


import sys, os
import CLI
from errno import EEXIST

# edit this as required. Define a command name mapping to a class object, by
# name. After editing, invoke this program as 'genericcli.py' to force linking.
NAMETOOBJECT = {
    "ipv4": "ipv4.IPv4",
    "pyshell": "CLI.Shell",
}

# XXX may need some work
def _get_object(name):
    i = name.rfind(".")
    if i >= 0:
        repmod = __import__(name[:i])
        klass = getattr(repmod, name[i+1:])
        return klass
    else:
        raise ValueError, "%s is not a valid class name" % (name,)

# if called as the "canonical" name then make the links
def make_links():
    bindir = os.path.join(os.environ["PYNMS_HOME"], "bin")
    os.chdir(bindir)
    for fname in NAMETOOBJECT.keys():
        try:
            os.link("genericcli.py", fname)
        except OSError, why:
            if why[0] == EEXIST:
                pass
            else:
                raise
        else:
            print "linked genericcli.py as %s. You man now invoke that command." % (fname,)

def main(argv):
    path, basename = os.path.split(argv[0])
    cname = NAMETOOBJECT.get(basename, None)
    if cname is None:
        print "Did not find key %s, making links." % (basename,)
        make_links()
    else:
        try:
            klass = _get_object(cname)
        except ValueError, err:
            print err
            print "Using generic CLI."
            CLI.run_generic_cli()
        else:
            print "Wrapping class %s." % (klass.__name__,)
            CLI.run_cli_wrapper(argv, klass)

main(sys.argv)

