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
