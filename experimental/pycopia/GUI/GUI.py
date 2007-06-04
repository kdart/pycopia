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

import pygtk
pygtk.require('2.0')
import gtk
import diacanvas


class NMSGUI(gtk.Window):
    def __init__(self):
        self.canvas = diacanvas.Canvas()
        #box = diacanvas.CanvasBox()
        #box.set(border_width=0.3, color=diacanvas.color(200, 100, 100, 128))
        #self.canvas.root.add(box)
        #box.move(20, 20)
        view = diacanvas.CanvasView(canvas=self.canvas)
        view.show()
        self.add(view)
        self.connect("destroy", gtk.mainquit)
        self.show()


def main(argv):
    window = NMSGUI()
    gtk.main()


