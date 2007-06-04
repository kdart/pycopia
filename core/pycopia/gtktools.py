#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 

import gobject
import gtk


class _ListPicker(gtk.Dialog):
    def __init__(self, items=()):
        gtk.Dialog.__init__(self)
        self.ret = None
        self._started = 0
        self.connect("destroy", self.quit)
        self.connect("delete_event", self.quit)
        self.set_geometry_hints(min_width=250, min_height=300)
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_win.show()
        self.vbox.pack_start(scrolled_win)
        #self.vbox.show()

        button = gtk.Button("Cancel")
        button.connect("clicked", self.cancel)
        button.set_flags(gtk.CAN_DEFAULT)
        self.action_area.pack_start(button)
        button.show()

        ls = gtk.ListStore(gobject.TYPE_STRING)
        for item in items:
            iter = ls.append()
            ls.set(iter, 0, item)

        lister = gtk.TreeView(ls)
        selection = lister.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        selection.unselect_all()
        lister.set_search_column(0)
        scrolled_win.add_with_viewport(lister)

        column = gtk.TreeViewColumn('Keyword', gtk.CellRendererText(), text=0)
        lister.append_column(column)
        lister.set_headers_visible(False)
        lister.connect("row-activated", self.row_activated)
        lister.show()

    def cancel(self, but):
        self.ret = None
        self.quit(but)

    def quit(self, *args):
        self.hide()
        self.destroy()
        gtk.main_quit()

    def row_activated(self, lister, path, column):
        selection = lister.get_selection()
        value = selection.get_selected()
        if value:
            model, iter = value
            self.ret = model.get_value(iter, 0)
            self.quit()


def list_picker(items):
    win = _ListPicker(items)
    win.set_title("Select From List")
    win.show()
    gtk.main()
    return win.ret



if __name__ == "__main__":
    print list_picker(dir())

