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
WindowMaker menu classes. Mostly used to make menus for the WindowMaker window
manager.

Brought to you by Keith Dart, <kdart@kdart.com>

exports:

    Menu: A dictionary type that holds the menu elements. This will
    typically hold MenuItem subclasses (see below).

    MenuItem: base class for various WindowMaker menu types. Don't use
    directly. Instead, use:

    Open_menu(MenuItem)
    Workspace_menu(MenuItem)
    Exec(MenuItem)
    Exit(MenuItem)
    Restart(MenuItem)
    Refresh(MenuItem)
    Arrange_icons(MenuItem)
    Shutdown(MenuItem)
    Show_all(MenuItem)
    Hide_others(MenuItem)
    Save_session(MenuItem)
    Clear_session(MenuItem)
    Info(MenuItem)

Example:

from WindowMaker import *

m = Menu("Menu Title")
m["Xterm"] = Exec("xterm")
m["Rxvt"] = Exec("rxvt")
m["Apps"] = Open_menu("apps.menu")

print m

# Can nest menus by creating new menu and adding it to another menu.
m2 = Menu("Nested Menu")
m2["Nested item"] = Exec("wterm")

m["nest"] = m2

print m

"""

from UserDict import UserDict
import string, types

class Menu(UserDict):
    """
    The menu class is a WindowMaker menu definiton.  It uses dictionary
    semantics (inherits the UserDict class).  You should supply the menu
    title as a string. It simply defaults to "Menu" if omited.

    Menu("Title")

    You may also change the menu title after the fact with the settitle()
    method. 

    The elements are expected to be an instance of a MenuItem subclass
    (e.g Exec.) 
    """

    def __init__(self, title="Menu"):
        self.data = {}
        self.title = title
    
    def __repr__(self):
        s = []
        list = self.data.keys()
        list.sort()
        s.append('"%s" MENU\n' % self.title)
        for item in list:
        # allow for nested menus
            if self.data[item].__class__.__name__ == "Menu":
                s.append(`self.data[item]`)
            else:
                s.append('  "%s" %s\n' % (item, `self.data[item]`))
        s.append('"%s" END\n' % self.title)
        return string.join(s, '')
    
#   def __setitem__(self, name, value):
#   def __delitem__(self):
#   def __getitem__(self):

    def settitle(self, newtitle):
        self.title = newtitle


class MenuItem(object):

    """
    Root Menu definition for WindowMaker
    
    Syntax is:
    
    <Title> [SHORTCUT <Shortcut>] <Command> <Parameters>
    
    <Title> is any string to be used as title. Must be enclosed with " if it
        has spaces
    
    SHORTCUT specifies a shortcut for that item. <Shortcut> has the same
    syntax of the shortcuts key options in the
    ~/GNUstep/Defaults/WindowMaker file, such as RootMenuKey or
    MiniaturizeKey.  You can't specify a shortcut for a MENU or OPEN_MENU
    entry.  

    Note that this class is not intended to be used directly, but is the
    base class for the specific menu item classes. The class you use is
    the same name as the menu command, but lowercase with first letter
    capitalized.
    """

    def __init__(self, params="", shortcut=""):
        self.params = params
        if len(shortcut) != 0:
            self.shortcut = 'SHORTCUT "%s"' % (shortcut)
        else:
            self.shortcut = ""
        self.command = string.upper(self.__class__.__name__)    

    def __repr__(self):
        return '%s %s %s' % \
            (self.shortcut, self.command, self.params)

    def setparams(self, params):
        self.params = params

    def setshortcut(self, shortcut):
        self.shortcut = 'SHORTCUT "%s"' % (shortcut)


import os
from stat import *
class Open_menu(MenuItem):
    """
    opens a menu from a file, pipe or directory(ies) contents and
    eventually precede each with a command.  

    Open_menu(params, [withcommand], [no extension])
        params = desired menu file, executable command, or directory.
        withcommand = optional command to that will be used when params is
        a directory. Each directory entry will be opened with this command
        when selected.
        no_extension = flag to indicate is file extension in a directory
        are to be stripped. Default is no.
    """
    def __init__(self, params, withopt="", noext=0):
        self.params = params
        self.shortcut = ""
        self.command = string.upper(self.__class__.__name__)    
        self.withopt = withopt
        if noext > 0:
            self.command = self.command + " -noext"

        firstparam = string.split(params)[0]
        # flag is paramter is a directory. Must be directory to use WITH.
        self.isdir = os.path.isdir(firstparam)
        # check if parameter is an executable file. If so, use pipe
        # option. Note that this program must produce valid menu format
        # output or bad things will happen.
        if os.path.isfile(firstparam):
            mode = os.stat(firstparam)[ST_MODE]
            if (mode & (S_IXUSR | S_IXGRP | S_IXOTH)):
                self.params = '|' + params

    def __repr__(self):
        if self.isdir and len(self.withopt) > 0:
            return '%s %s WITH %s' % (self.command, self.params, self.withopt)
        else:
            return '%s %s' % (self.command, self.params)


class Workspace_menu(MenuItem):
    """
    adds a submenu for workspace operations. Only one workspace_menu is
    allowed.        
    """

class Exec(MenuItem):
    """
    Executes an external program.

    Options for command line in EXEC:
    %s - substitute with current selection
    %a(title[,prompt]) - opens a input box with the specified title and the
                     optional prompt and do substitution with what you typed
    %w - substitute with XID for the current focused window

    You can override special characters (as % and ") with the \ character:
    ex: xterm -T "\"Hello World\""

    You can also use character escapes, like \n

    """

class Exit(MenuItem):
    """
    exits the window manager
    """

class Restart(MenuItem):
    """
    restarts WindowMaker or start another window manager
    """

class Refresh(MenuItem):
    """
    refreshes the desktop
    """

class Arrange_icons(MenuItem):
    """
    rearranges the icons on the workspace
    """

class Shutdown(MenuItem):
    """
    kills all clients (and close the X window session)
    """

class Show_all(MenuItem):
    """
    unhides all windows on workspace
    """

class Hide_others(MenuItem):
    """
    hides all windows on the workspace, except the focused one (or the last
    one that received focus)
    """

class Save_session(MenuItem):
    """
    saves the current state of the desktop, which include all running
    applications, all their hints (geometry, position on screen, workspace
    they live on, the dock or clip from where they were launched, and if
    minimized, shaded or hidden. Also saves the current workspace the user
    is on. All will be restored on every start of windowmaker until another
    SAVE_SESSION or CLEAR_SESSION is used. If SaveSessionOnExit = Yes; in
    WindowMaker domain file, then saving is automatically done on every
    windowmaker exit, overwriting any SAVE_SESSION or CLEAR_SESSION.
    """

class Clear_session(MenuItem):
    """
    clears any previous saved session. This will not have any effect if
    SaveSessionOnExit is True.
    """

class Info(MenuItem):
    """
    shows the Info Panel
    """

# Shortcut keys
#class ShortcutKeys:
#   def __init__(self):
#       keys = ["RootMenuKey", "MiniaturizeKey", "CloseKey",
#           "RaiseLowerKey", "MoveResizeKey", "Workspace1Key",
#           "Workspace2Key", "Workspace3Key", "Workspace4Key",
#           "Workspace5Key", "Workspace6Key", "Workspace7Key",
#           "Workspace8Key", "Workspace9Key", "Workspace10Key",
#           "WindowShortcut1Key", "WindowShortcut2Key",
#           "WindowShortcut3Key", "WindowShortcut4Key" ]


