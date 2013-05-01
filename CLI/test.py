#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

from __future__ import print_function

"""


"""

import unittest


from pycopia import IO
from pycopia import UI
from pycopia import CLI


class TestCommands(CLI.BaseCommands):

    def f(self, argv):
        """command"""
        return argv[0]


class CLITests(unittest.TestCase):

    def setUp(self):
        pass

    def test_build_CLI(self):
        cli = CLI.get_cli(TestCommands)
        #print(dir(cli))
        cli.interact()



if __name__ == '__main__':
    unittest.main()
