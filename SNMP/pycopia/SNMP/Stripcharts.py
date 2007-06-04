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
Objects for running strip charts for IF-MIB variables.


"""

import sys
import gtk

try:
    import rtgraph
except ImportError:
    print >>sys.stderr, """The 'rtgraph' module is not installed. Obtain this from 
    http://navi.cx/svn/misc/trunk/rtgraph/web/index.html
    or run 'emerge dev-python/rtgraph' in Gentoo Linux."""
    raise

from pycopia.SNMP import SNMP
from pycopia.mibs import IF_MIB

class SNMPChannel(rtgraph.Channel):
    def __init__(self, session, klass, port, color):
        intf = klass(indexoid=[port])
        intf.set_session(session)
        self.rater = intf.get_ratecounter()
        super(SNMPChannel, self).__init__(name=klass.__name__, color=color)

    def getValue(self):
        try:
            self.rater.update(self._t)
        except SNMPNoResponse:
            return None
        return self.rater.EWRA

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

    argv = argv[1:]
    while argv:
        host = argv.pop(0)
        port = int(argv.pop(0))

        sess = SNMP.get_session(host, community)

        graph = rtgraph.HScrollLineGraph(
            scrollRate = 2,
            pollInterval = 1000,
            size       = (384,128),
            gridSize   = 32,
            channels   = [SNMPChannel(sess, IF_MIB.ifInUcastPkts, port, color=(1,0,0)), 
                          SNMPChannel(sess, IF_MIB.ifOutUcastPkts, port, color=(0,1,0))],
            bgColor    = (0, 0, 0.3),
            gridColor  = (0, 0, 0.5),
            range      = (0, 3500),
            )
        graph.show()

        frame = gtk.Frame()
        frame.set_label("device %s port %s" % (host, port))
        frame.add(graph)
        frame.show()

        vbox.pack_end(frame)

    win.show()
    win.connect("destroy", gtk.mainquit)
    gtk.main()


