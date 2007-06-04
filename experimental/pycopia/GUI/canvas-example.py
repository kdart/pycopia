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

import GDK
from gtk import *
from gnome.ui import *
from whrandom import *
import GdkImlib

class CanvasExample(object):
    def __init__(self):
        self.generator = whrandom()

        self.width = 400
        self.height = 400

        self.all = []

        self.colors = ("red",
                       "yellow",
                       "green",
                       "cyan",
                       "blue",
                       "magenta")


    def change_item_color(self, item):
        # Pick a random color from the list.
        n = int(self.generator.random() * len(self.colors)) - 1
        item.set(fill_color = self.colors[n])


    def item_event(self, widget, event=None):
        if event.type == GDK.BUTTON_PRESS:
            if event.button == 1:
                # Remember starting position.
                self.remember_x = event.x
                self.remember_y = event.y
                return TRUE

            elif event.button == 3:
                # Destroy the item.
                widget.destroy()
                return TRUE

        elif event.type == GDK._2BUTTON_PRESS:
            #Change the item's color.
            self.change_item_color(widget)
            return TRUE

        elif event.type == GDK.MOTION_NOTIFY:
            if event.state & GDK.BUTTON1_MASK:
                # Get the new position and move by the difference
                new_x = event.x
                new_y = event.y

                widget.move(new_x - self.remember_x, new_y - self.remember_y)

                self.remember_x = new_x
                self.remember_y = new_y

                return TRUE
            
        elif event.type == GDK.ENTER_NOTIFY:
            # Make the outline wide.
            widget.set(width_units=3)
            return TRUE

        elif event.type == GDK.LEAVE_NOTIFY:
            # Make the outline thin.
            widget.set(width_units=1)
            return TRUE

        return FALSE


    def add_object_clicked(self, widget, event=None):
        x1 = self.generator.random() * self.width
        y1 = self.generator.random() * self.height
        x2 = self.generator.random() * self.width
        y2 = self.generator.random() * self.height

        if x1 > x2:
            x2,x1 = x1,x2
        if y1 > y2:
            y2,y1 = y1,y2

        if (x2 - x1) < 10:
            x2 = x2 + 10

        if (y2 - y1) < 10:
            y2 = y2 + 10

        if (self.generator.random() > .5):
            type = 'rect'
        else:
            type = 'ellipse'

        w = self.canvas.root().add(type, x1=x1, y1=y1, x2=x2, y2=y2, 
                                   fill_color='white', outline_color='black',
                                   width_units=1.0)
        w.connect("event", self.item_event)

        self.all.append(w)

    def main(self):
        # Open window to hold canvas.
        win = GtkWindow()
        win.connect('destroy', mainquit)
        win.set_title('Canvas Example')

        # Create VBox to hold canvas and buttons.
        vbox = GtkVBox()
        win.add(vbox)
        vbox.show()

    # Some instructions for people using the example:
        label = GtkLabel("Drag - move object.\n" +
             "Double click - change colour\n" +
             "Right click - delete object")
        vbox.pack_start(label, expand=FALSE)
        label.show()

        # Create canvas.
        self.canvas = GnomeCanvas()
        self.canvas.set_usize(self.width, self.height)
        self.canvas.set_scroll_region(0,0, self.width, self.height)
        vbox.pack_start(self.canvas)
        self.canvas.show()

        # Create buttons.
        hbox = GtkHBox()
        vbox.pack_start(hbox, expand=FALSE)
        hbox.show()

        b = GtkButton("Add an object")
        b.connect("clicked", self.add_object_clicked)
        hbox.pack_start(b)
        b.show()

        b = GtkButton("Quit")
        b.connect("clicked", mainquit)
        hbox.pack_start(b)
        b.show()

        win.show()

if __name__ == '__main__':
    c = CanvasExample()
    c.main()
    mainloop()
