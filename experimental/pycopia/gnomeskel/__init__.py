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
RATIONALE
The recommended way to use the Gnome/GTK python bindings is to use glade
and libglade. However, this library does not provide good encapsulation of
windows and their methods. So, this module provides a skeletal framwork
for creating GUI applications with Gnome/gtk widgets.

Basically, this works with widgets created with glade. You subclass a Gapp
(or GCanvasApp) class with a name that exactly matches a window name
defined in your glade file. Methods will be autoconnected.

"""

### try to avoid namespace pollution
#from gtk import *
#from gnome.ui import *
import sys, os
import string
import gnome.ui
import libglade
gtk = libglade._gtk


#CANVASFONT= "-monotype-arial-medium-r-normal-*-*-120-*-*-p-*-iso8859-1"

def _print_children(app):
    for child in app.children():
        print child
        _print_children(child)

def get_self(object):
    top = string.split(libglade.get_widget_long_name(object), ".")[0]
    xml = libglade.get_widget_tree(object)
    return xml.get_widget(top).get_data("instance")

class GApp(gnome.ui.GnomeApp):
    def __init__(self, argv=None, gladefile=None):
        if not gladefile:
            self.GLADEFILE = self.__class__.__name__ + ".glade"
        else:
            self.GLADEFILE = gladefile
        if not os.path.isfile(self.GLADEFILE):
            print "Cannot find GLADEFILE", self.GLADEFILE
            sys.exit(1)
        self.xml = libglade.GladeXML(self.GLADEFILE, self.__class__.__name__)
        # the app should be a GnomeApp object from the glade file
        app = self.xml.get_widget(self.__class__.__name__)
        gnome.ui.GnomeApp.__init__(self, _obj=app._o)
        # stash this instance so get_self() can find it (for callbacks)
        self.set_data("instance", self)
        self._init_buttons()
        for baseclass in self.__class__.__bases__:
            self.xml.signal_autoconnect(baseclass.__dict__)
        self.xml.signal_autoconnect(self.__class__.__dict__)
        self.app_init(argv)
        self.show()
        libglade._gtk.mainloop()
    
    # override this in your subclass
    def app_init(self, argv):
        pass

    def getWidget(self, wname):
        return self.xml.get_widget(wname)

    def add_widget(self, wname):
        setattr(self, wname, self.xml.get_widget(wname))

    def add_widgets(self, wlist):
        for w in wlist:
            self.add_widget(w)

    def _init_buttons(self):
        self.main_toolbar = self.getWidget("main_toolbar")
        if self.main_toolbar:
            self.main_toolbar.set_style(libglade._gtk.TOOLBAR_ICONS)

    #### NOTE ####
    # With these on_* callbacks the "object" parameter will be the gui
    # object, not this class instance. But, we stashed the instance as a
    # GTK attribute, so we get the python instance again.

    def on_menu_exit_activate(object):
        self = get_self(object)
        self.cleanup()
        libglade._gtk.mainquit()

    def on_app_destroy(object):
        object.get_data("instance").cleanup()
        libglade._gtk.mainquit()

    def on_toolbar_exit_clicked(object):
        object.get_data("instance").cleanup()
        libglade._gtk.mainquit()

    def on_about_activate(self):
        return About()

    def on_preferences_activate(self):
        GPreferences(self)

    def on_preferences_changed(self):
        self.win.changed()

    def cleanup(self):
        pass


class GCanvasApp(GApp):
    def __init__(self, argv):
        GApp.__init__(self)
        self.main_canvas = GCanvas(self.xml.get_widget("main_canvas"), self)
        self._init_canvas()

    def _init_canvas(self):
        self.main_canvas.add_menu(GContext_menu())
        vpnlist = self.server.getVpnList()
        for vpn in vpnlist:
            self.main_canvas.addVPN(vpn)

    def cleanup(self):
        del self.main_canvas


#class GMenu(gtk.GtkMenu):
class GMenu(object):
    def __init__(self):
        xml = libglade.GladeXML(GLADEFILE, self.__class__.__name__)
        xml.signal_autoconnect(self.__class__.__dict__)
        widget = xml.get_widget(self.__class__.__name__)
        #gtk.GtkMenu.__init__(self, widget._o)


class GContext_menu(GMenu):
    def on_popup_cut_activate(X):
        print X

    def on_popup_copy_activate(X):
        print X

    def on_popup_clear_activate(X):
        print X

    def on_popup_properties_activate(X):
        print X
        print X.children()


class GCanvas(object):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.canvas.set_data("instance", parent)
        self.x1, self.y1, self.x2, self.y2 = self.canvas.get_scroll_region()
        self.popupmenu = None
        self.canvas.show()

    def _item_event(self, W, event=None):
        if event.type == GDK.BUTTON_PRESS:
            if event.button == 1:
                # Remember starting position.
                self.remember_x = event.x
                self.remember_y = event.y
                print W
                return TRUE
            elif event.button == 2:
                # Remember starting position.
                self.remember_x = event.x
                self.remember_y = event.y
                return TRUE
            elif event.button == 3:
                if self.popupmenu:
                    self.popupmenu.popup(None, None, None, event.button, event.time)
                return TRUE
#       elif event.type == GDK._2BUTTON_PRESS:
#           #Change the item's color.
#           self.change_item_color(W)
#           return TRUE
        elif event.type == GDK.MOTION_NOTIFY:
            if event.state & GDK.BUTTON1_MASK or event.state & GDK.BUTTON2_MASK:
                # Get the new position and move by the difference
                new_x = event.x
                new_y = event.y
                W.move(new_x - self.remember_x, new_y - self.remember_y)
                self.remember_x = new_x
                self.remember_y = new_y
                return TRUE
#       elif event.type == GDK.ENTER_NOTIFY:
#           # Make the outline wide.
#           W.set(width_units=3)
#           return TRUE
#       elif event.type == GDK.LEAVE_NOTIFY:
#           # Make the outline thin.
#           W.set(width_units=2)
#           return TRUE
        return FALSE

    def add_menu(self, menu):
        self.popupmenu = menu


### The about dialog.
class About(GApp):
    # Nothing needs to be done here!
    pass

### The preferences selection windows XXX
class GPreferences(GApp):
    def on_preferences_apply(self, page):
        # We only want to set preferences for the whole thing
        # and not a page at a time.
        if (page != -1):
            return
        # Check the display toolbar radio buttons
        if GApp.getWidget(self, 'display_toolbar_both').get_active():
            display_toolbar = TOOLBAR_BOTH
        elif GApp.getWidget(self, 'display_toolbar_icons').get_active():
            display_toolbar = TOOLBAR_ICONS
        elif GApp.getWidget(self, 'display_toolbar_text').get_active():
            display_toolbar = TOOLBAR_TEXT
        else:
            # If all else fails
            print 'display_toolbar error in prefs'
            display_toolbar = TOOLBAR_BOTH
        GApp.getWidget(self, 'toolbar').set_style(display_toolbar)


