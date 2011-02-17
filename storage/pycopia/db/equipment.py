#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Equipment reports from the database.

"""

from __future__ import print_function

import os

from pycopia.db import models
from pycopia import proctools


HEAD = """
digraph G {
 size="11,17";
 ranksep=3;
 overlap="scale";
 ratio=auto;
"""

NODEDEF = '"{nodename}" [ label="{label}",shape="{shape}",style="{style}",color="{color}" ];\n'
CONNECTDEF = '"{startnode}" -> "{endnode}" [ color="{color}",arrowhead="{arrowhead}" ];\n'

TAIL = """
}
"""

RENDER = 'twopi -o{outfile} -Tsvg {dotfile}'

class MapBuilder(object):

    def __init__(self, session):
        self._sess = session

    def topology_all(self, outfile, dotfile):
        with open(dotfile, "w") as fo:
            self._write_dotfile(fo)
        os.system(RENDER.format(outfile=outfile, dotfile=dotfile))

    def _write_dotfile(self, fileobj):
        fileobj.write(HEAD)
        sess = self._sess
        nets = sess.query(models.Network).all()
        for netw in nets:
            fileobj.write(NODEDEF.format(nodename="net_{0:d}".format(netw.id), label=netw.name, 
                        shape="circle", style="filled", color="blue"))
            for iface in netw.interfaces:
                fileobj.write(NODEDEF.format(
                        nodename="iface_{0:d}".format(iface.id), 
                        label="{0} ({1!s})".format(iface.name, iface.ipaddr),
                        shape="box", style="filled", color="grey"))


        for netw in nets:
            endnode = "net_{0:d}".format(netw.id)
            for iface in netw.interfaces:
                fileobj.write(CONNECTDEF.format(
                        startnode="iface_{0:d}".format(iface.id), 
                        endnode=endnode,
                        color="green", arrowhead="none"))
        fileobj.write(TAIL)

    def _interfaces(self, fileobj):
        pass



def topomap(argv):
    verbose = True
    try:
        dotout = argv[1] # XXX
    except IndexError:
        dotout = "/tmp/eqgraph.dot"
    try:
        outfilename = argv[2] # XXX
    except IndexError:
        outfilename = "/var/tmp/eqgraph.svg"
    sess = models.get_session()
    builder = MapBuilder(sess)
    try:
        builder.topology_all(outfilename, dotout)
    finally:
        sess.close()
    if verbose:
        print(outfilename, "written.")


if __name__ == "__main__":
    import sys
    topomap(sys.argv)
    os.system("eog /var/tmp/eqgraph.svg")
