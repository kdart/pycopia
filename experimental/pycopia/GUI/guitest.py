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
MODULE_DESCRIPTION

"""

import gtk

class MyWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.gc = None  # initialized in realize-event handler
        self.width  = 0 # updated in size-allocate handler
        self.height = 0 # idem
        self.connect('size-allocate', self.on_size_allocate)
        self.connect('expose-event',  self.on_expose_event)
        self.connect('realize',       self.on_realize)

    def on_realize(self, widget):
        self.gc = widget.window.new_gc()
        self.gc.set_line_attributes(3, gtk.gdk.LINE_ON_OFF_DASH,
                                    gtk.gdk.CAP_ROUND, gtk.gdk.JOIN_ROUND)

    def on_size_allocate(self, widget, allocation):
        self.width = allocation.width
        self.height = allocation.height

    def on_expose_event(self, widget, event):
        # This is where the drawing takes place

        widget.window.draw_rectangle(self.gc, False,
                                     1, 1, self.width - 2, self.height - 2)
        widget.window.draw_line(self.gc,
                                0, 0, self.width - 1, self.height - 1)
        widget.window.draw_line(self.gc,
                                self.width - 1, 0, 0, self.height - 1)


def main(argv):
    win = gtk.Window()
    win.add(MyWidget())
    win.show_all()
    win.connect("destroy", lambda w: gtk.main_quit())
    gtk.main()

if __name__ == "__main__":
    import sys
    main(sys.argv)

