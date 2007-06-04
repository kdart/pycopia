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


"""

import unittest


from pycopia import CLI
from pycopia import UI
from pycopia import IO
from pycopia import cursesio


class CLITests(unittest.TestCase):

    def setUp(self):
        pass

    def test_CLI(self):
        """This is an interactive test."""
        testui = cursesio.get_curses_ui()
        cmd = CLI.GenericCLI(testui)
        parser = CLI.CommandParser(cmd)
        testui.Print("Type 'exit' when finished.")
        parser.interact()



if __name__ == '__main__':
    unittest.main()
