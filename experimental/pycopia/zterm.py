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

import sys
import os

import gtk
import gnome.zvt

class ZTerm(object):
    """ZTerm([title], [cols], [rows], [font])
    Wraps a GNOME ZvtTerm with a window. 
    """
    default_font = "-misc-fixed-medium-r-normal-*-*-120-*-*-c-*-iso8859-1"
    def __init__(self, title=None, cols=80, rows=25, font=None):
        self.win = gtk.GtkWindow()
        self.win.connect("delete_event", gtk.mainquit)
        if title is None:
            title = "ZTerm"
        if font is None:
            font = ZTerm.default_font
        self.win.set_title(title)
        self.win.set_policy(gtk.FALSE, gtk.TRUE, gtk.TRUE)

        hbox = gtk.GtkHBox()
        self.win.add(hbox)
        hbox.show()
        
        term = gnome.zvt.ZvtTerm(cols, rows)
        term.set_scrollback(500)
        term.set_font_name(font)
        term.connect("child_died", child_died_event)
        hbox.pack_start(term)
        term.show()
        self.term = term

        scroll = gtk.GtkVScrollbar(term.adjustment)
        hbox.pack_start(scroll, expand=gtk.FALSE)
        scroll.show()

        charwidth = term.charwidth
        charheight = term.charheight
        self.win.set_geometry_hints(geometry_widget=term,
                       min_width=2*charwidth, min_height=2*charheight,
                       base_width=charwidth,  base_height=charheight,
                       width_inc=charwidth,   height_inc=charheight)
        self.win.show()

    def feed(self, text):
        self.term.feed(text)

    def run_process(self, argv=None):
        if type(argv) is str:
            argv = argv.split()
        elif argv is None:
            argv = []
        pid = self.term.forkpty()
        if pid == -1:
            print "Couldn't fork"
        if pid == 0:
            if not argv:
                os.execv('/usr/bin/env', ['/usr/bin/env', 'python'])
            else:
                os.execvp(argv[0], argv)
            print "Couldn't exec"
            os._exit(1)
        # this is executed by parent process only:
        #gtk.mainloop()


def child_died_event(zvt):
    zvt.destroy()

if __name__ == '__main__': 
    import time
    zt = ZTerm()
    while 1:
        while gtk.events_pending():
            gtk.mainiteration()
        zt.feed("Some text\r\n")    
        time.sleep(1)


