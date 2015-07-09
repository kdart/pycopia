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
Pycopia name server control module.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


from pycopia.remote import pyro


def print_listing(listing):
    for name, uri in sorted(listing.items()):
        print("{} -->\n    {}".format(name, uri))


def nsexport(nameserver, fname):
    with open(fname, "wb") as fo:
        for name, uri in nameserver.list().items():
            fo.write("{}\t{}\n".format(name, uri))


def nsimport(nameserver, fname):
    with open(fname, "rb") as fo:
        for line in fo:
            name, uri = line.split("\t", 1)
            try:
                nameserver.register(name.strip(), uri.strip(), safe=True)
            except pyro.NamingError:
                print("Warning: {} already registered.".format(name))
            else:
                print("Registered: {}".format(name))


_DOC = """nsc [-h?]

Control or query the name server.

Subcommands:
    list - show current objects.
    ping - No error if server is reachable.
    remove <name> - remove the named agent entry.
    export <filename> - export agent entries to a file.
    import <filename> - import agent entries from a file.
"""

def nsc(argv):
    import getopt
    try:
        optlist, args = getopt.getopt(argv[1:], "h?")
    except getopt.GetoptError:
        print(_DOC)
        return 2

    for opt, optarg in optlist:
        if opt in ("-h", "-?"):
            print(_DOC)
            return

    try:
        subcmd = args[0]
    except IndexError:
        print(_DOC)
        return 2

    args = args[1:]
    nameserver = pyro.locate_nameserver()
    if subcmd.startswith("li"):
        if args:
            print_listing(nameserver.list(prefix=args[0]))
        else:
            print_listing(nameserver.list())
    elif subcmd.startswith("pi"):
        nameserver.ping()
        print("Name server is alive.")
    elif subcmd.startswith("rem"):
        if args:
            nameserver.remove(name=args[0])
        else:
            print(_DOC)
            return 2
    elif subcmd.startswith("imp"):
        fname = args[0] if len(args) > 0 else "nsentries.txt"
        nsimport(nameserver, fname)
    elif subcmd.startswith("exp"):
        fname = args[0] if len(args) > 0 else "nsentries.txt"
        nsexport(nameserver, fname)
        print("exported to {}.".format(fname))
    else:
        print(_DOC)
        return 2


if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    nsc(sys.argv)

