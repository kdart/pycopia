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
from gtk import *
from gnome.ui import *
import GtkExtra

project = {}
project["output_support_files"] = "True"
project["gettext_support"] = "True"
project["gnome_support"] = "True"
project["name"] = "Gnomeined"
project["pixmaps_directory"] = "pixmaps"
project["program_name"] = "gnomeined"
project["support_header_file"] = "support.h"
project["directory"] = ""
project["support_source_file"] = "support.c"
project["handler_header_file"] = "callbacks.h"
project["backup_source_files"] = "True"
project["handler_source_file"] = "callbacks.c"
project["output_build_files"] = "True"
project["main_header_file"] = "interface.h"
project["main_source_file"] = "interface.c"
project["source_directory"] = "src"
project["language"] = "C"
project["use_widget_names"] = "False"
project["output_main_file"] = "True"
project["translatable_strings_file"] = ""
from JordyHandlers import *
class JordyWidget(object):
    def __init__(self):
        Jordy=GnomeApp(WINDOW_TOPLEVEL)
        Jordy.set_usize(-1, -1)
        Jordy.set_policy(FALSE, TRUE, FALSE)
        Jordy.set_position(WIN_POS_NONE)
        dock1=GnomeDock()
        Jordy.add(dock1)
        dock1.set_usize(-1, -1)
        dockitem1=GnomeDockItem()
        dock1.add(dockitem1)
        dockitem1.set_usize(-1, -1)
        dockitem1.set_border_width(2)
        menubar1=GtkMenuBar()
        dockitem1.add(menubar1)
        menubar1.set_usize(-1, -1)
