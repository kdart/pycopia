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

import gtk
import gnome.ui
import glade


FONT= "-monotype-arial-medium-r-normal-*-*-120-*-*-p-*-iso8859-1"

class GUIWindow(gtk.Window):
    def __init__(self, GLADEFILE):
        self.xml = glade.GladeXML(GLADEFILE, self.__class__.__name__)
        self.xml.signal_autoconnect(self.__class__.__dict__)
        self.win = self.xml.get_widget(self.__class__.__name__)
        self.win.set_data("instance", self)
        self.win.show()
    
    def getWidget(self, wname):
        return self.xml.get_widget(wname)


