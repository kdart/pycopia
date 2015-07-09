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
Tools for working with the xfce4 environment.

Used to create or edit XFCE4 menus from Python.

"""

from pycopia.aid import newclass
from pycopia.dtds import xfdesktop_menu

from pycopia.XML import POM

class XFCE4Menu(POM.POMDocument):
    DOCTYPE = "<!DOCTYPE xfdesktop-menu>\n"

    def emit(self, fo):
        pp = POM.BeautifulWriter(fo)
        super(XFCE4Menu, self).emit(pp)

    def add_submenu(self, **attribs):
        return self.root.add_submenu(**attribs)

    def add_title(self, **attribs):
        self.root.add_title(**attribs)

    def add_app(self, **attribs):
        self.root.add_app(**attribs)

    def add_separator(self):
        self.root.add_separator()

    def add_include(self, **attribs):
        self.root.add_include(**attribs)

    
class MenuMixin(object):
    def add_title(self, **attribs):
        title = xfdesktop_menu.Title(**attribs)
        self.append(title)
    
    def add_app(self, **attribs):
        app = xfdesktop_menu.App(**attribs)
        self.append(app)

    def add_separator(self):
        self.append(xfdesktop_menu.Separator())
    
    def add_include(self, **attribs):
        pass

    def add_submenu(self, **attribs):
        Menu = newclass("Menu", MenuMixin, xfdesktop_menu.Menu)
        menu = Menu(**attribs)
        self.append(menu)
        return menu
    


# factory for menu files
def new_menu():
    doc = XFCE4Menu(xfdesktop_menu)
    RootMenu = newclass("RootMenu", MenuMixin, xfdesktop_menu.Xfdesktop_menu)
    root = RootMenu()
    doc.set_root(root)
    return doc

def open_menu(filename):
    fo = open(filename)
    doc = XFCE4Menu(xfdesktop_menu)
    doc.parseFile(fo)
    fo.close()
    return doc


