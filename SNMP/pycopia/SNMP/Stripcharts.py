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
Objects for running strip charts for IF-MIB variables.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
from math import log

import gtk


try:
    import rtgraph
except ImportError:
    print("""The 'rtgraph' module is not installed. Obtain this from
    http://navi.cx/svn/misc/trunk/rtgraph/web/index.html
    or run 'emerge dev-python/rtgraph' in Gentoo Linux.""", file=sys.stderr)
    raise

from pycopia.SNMP import SNMP, SNMPNoResponse
from pycopia.mibs import IF_MIB

class SNMPChannel(rtgraph.Channel):
    def __init__(self, session, klass, port, color):
        intf = klass(indexoid=[port])
        intf.set_session(session)
        self.rater = intf.get_ratecounter(3)
        super(SNMPChannel, self).__init__(name=klass.__name__, color=color)

    def getValue(self):
        try:
            self.rater.update(self._t)
        except SNMPNoResponse:
            return None
        try:
            return log(self.rater.EWRA)
        except (TypeError, ValueError):
            return 0.0

    def hasChanged(self, graph):
        self._t = graph.lastUpdateTime


def unicast_packets(argv, community="public"):
    """Display a set of strip charts, one for each set of parameters in argv.
    The set is a "host interface" pair. For example: device1 2 device2 4 """

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title("Unicast Packets")

    vbox = gtk.VBox()
    vbox.show()
    win.add(vbox)

    sessions = {}

    while argv:
        host = argv.pop(0)
        ifindex = int(argv.pop(0))

        if host in sessions:
            sess = sessions[host]
        else:
            sess = SNMP.get_session(host, community)
            sessions[host] = sess

        graph = rtgraph.HScrollLineGraph(
            scrollRate = 2,
            pollInterval = 1000,
            size       = (384,128),
            gridSize   = 32,
            channels   = [SNMPChannel(sess, IF_MIB.ifInUcastPkts, ifindex, color=(1,0,0)),
                          SNMPChannel(sess, IF_MIB.ifOutUcastPkts, ifindex, color=(0,1,0))],
            bgColor    = (0, 0, 0.3),
            gridColor  = (0, 0, 0.5),
            range      = (0, 19),
            )
        graph.show()

        frame = gtk.Frame()
        frame.set_label("device %s ifindex %s" % (host, ifindex))
        frame.add(graph)
        frame.show()

        vbox.pack_end(frame)

    del sessions
    win.show()
    win.connect("destroy", gtk.main_quit)
    gtk.main()


