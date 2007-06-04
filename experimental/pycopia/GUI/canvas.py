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

win = GtkWindow()
win.connect('destroy', mainquit)
win.set_title('Canvas test')

canvas = GnomeCanvas()
canvas.set_size(300, 300)
win.add(canvas)
canvas.show()

canvas.root().add('line', points=(10,10, 90,10, 90,90, 10,90),
          width_pixels=10, fill_color='blue')

win.show()

mainloop()

