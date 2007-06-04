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

from gtk import *
from gnome.ui import *

class MapWindow(object):
    def __init__(self):
        self.win = GnomeApp("pyNMS", "pyNMS")
        self.win.set_wmclass("pyNMS", "pyNMS")
        self.win.connect('destroy', self._quit)
        self.win.create_menus( self._create_menu() )

#       self.vbox = GtkVBox()

        self.canvas = GnomeCanvas()
        self.canvas.set_usize(500, 500)
        self.canvas.set_scroll_region(0,0, 1500, 1500)
#       self.vbox.pack_start(self.canvas)
#       self.vbox.show()

#       self.win.set_contents(self.vbox)
        self.win.set_contents(self.canvas)
        self.win.show()

    def mainloop(self):
        mainloop()

    def _create_menu(self):
        file_menu = [
            UIINFO_ITEM_STOCK('Open...', None, self._open, STOCK_MENU_OPEN),
            UIINFO_ITEM_STOCK('Save', None, self._save, STOCK_MENU_SAVE),
            UIINFO_ITEM_STOCK('Save As...', None, self._saveas, STOCK_MENU_SAVE_AS),
            UIINFO_SEPARATOR,
            UIINFO_ITEM_STOCK('Quit', None, self._quit, STOCK_MENU_QUIT)
            ]
        edit_menu = [
            UIINFO_ITEM_STOCK('Cut', None, self._edit_cut, STOCK_MENU_CUT),
            UIINFO_ITEM_STOCK('Copy', None, self._edit_copy, STOCK_MENU_COPY),
            UIINFO_ITEM_STOCK('Paste', None, self._edit_paste, STOCK_MENU_PASTE),
            UIINFO_SEPARATOR,
            UIINFO_ITEM_STOCK('Search', None, None, STOCK_MENU_SEARCH),
            UIINFO_ITEM_STOCK('Select All', None, self._sel_all, STOCK_MENU_BLANK),
            UIINFO_ITEM_STOCK('Unselect All', None, self._usel_all, STOCK_MENU_BLANK),
            UIINFO_SEPARATOR,
            UIINFO_ITEM_STOCK('Preferences', None, self._set_prefs, STOCK_MENU_PREF),
            ]
        tools_menu = [
            UIINFO_ITEM_STOCK('IP Monitor', None, self._ip_monitor, STOCK_MENU_BLANK),
            UIINFO_ITEM_STOCK('SNMP Monitor', None, self._snmp_monitor, STOCK_MENU_BLANK),
            UIINFO_ITEM_STOCK('IP Troubleshooting', None, self._ip_troubleshooting, STOCK_MENU_BLANK)
            ]
        help_menu = [
            UIINFO_ITEM_STOCK('About', None, self._about, STOCK_MENU_ABOUT)
            ]
        menu_info = [
            UIINFO_SUBTREE('File', file_menu),
            UIINFO_SUBTREE('Edit', edit_menu),
            UIINFO_SUBTREE('Tools', tools_menu),
            UIINFO_SUBTREE('Help', help_menu)
            ]

        return menu_info

    def _quit(self, b=None, a=None):
        self.win.destroy()
        mainquit()
        raise SystemExit

    def _open(self, b):
        pass

    def _save(self, b):
        pass

    def _saveas(self, b):
        pass

    def _edit_cut(self, b):
        pass

    def _edit_copy(self, b):
        pass

    def _edit_paste(self, b):
        pass

    def _sel_all(self, b):
        pass

    def _usel_all(self, b):
        pass

    def _set_prefs(self, b):
        pass
    
    def _about(self, item):
        aboutwin = GnomeAbout('pyNMS', '0.1', 'GPL',
                              ['Keith Dart <kdart@kdart.com>'],
                              'GNOME network management tool.')
        aboutwin.set_parent(self.win)
        aboutwin.show()

    def _ip_monitor(self, b):
        pass

    def _snmp_monitor(self, b):
        pass

    def _ip_troubleshooting(self, b):
        pass

    def item_event(self, widget, event=None):
        if event.type == GDK.BUTTON_PRESS:
            if event.button == 1:
                print widget
                print dir(widget)
                return TRUE

            elif event.button == 3:
                # Destroy the item.
                widget.destroy()
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


    def newrect(self, w=None, event=None):
        w = self.canvas.root().add("rect", x1=20, y1=20, x2=40, y2=40, 
                                   fill_color='white', outline_color='black',
                                   width_units=1.0)
        w.connect("event", self.item_event)




if __name__ == '__main__':
    w = MapWindow()
    w.mainloop()
