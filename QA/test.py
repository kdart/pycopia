#!/usr/bin/python
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

from pycopia import QA
from pycopia.QA import core
from pycopia.QA import testrunner

from pycopia import ANSIterm
from pycopia import terminal
from pycopia import getdocs
from pycopia import NPS
from pycopia import PsuedoFile
from pycopia import ScriptManager
from pycopia import datafile
from pycopia import dataset

from pycopia import reports
from pycopia import remote
from pycopia import smartbits

from pycopia.remote import Client
from pycopia.remote import RemoteCLI


class QATests(unittest.TestCase):

    def test_terminal_screen(self):
        """Test terminal emulator Screen."""
        term = terminal.Screen()
        term.fill("*")
        term.cursor_down()
        term.cursor_down()
        term.cursor_forward()
        term.cursor_forward()
        term.erase_end_of_line()
        print term

    def test_terminal_keyboard(self):
        """Test terminal emulator Keyboard."""
        kb = terminal.Keyboard()
        print kb
        kb.lock()
        print kb
        kb.unlock()

    def test_reports(self):
        """Test basic reports."""
        rpt = reports.get_report(("StandardReport", "-"))
        rpt.initialize()
        rpt.info("Some info")
        rpt.failed("failed message")
        rpt.diagnostic("diagnostic message")
        rpt.passed("passed message")
        rpt.finalize()

    def test_ansi_report(self):
        """Test ANSI reports."""
        rpt = reports.get_report(("StandardReport", "-", "text/ansi"))
        rpt.initialize()
        rpt.info("Some info")
        rpt.failed("failed message")
        rpt.diagnostic("diagnostic message")
        rpt.passed("passed message")
        rpt.finalize()


    def test_datafile(self):
        metadata = datafile.DataFileData()
        metadata.name = "test_datafile"
        metadata.set_timestamp()
        metadata["state"] = datafile.ON
        metadata["voltage"] = 2.5
        fname = metadata.get_filename("/tmp")
        fo = open(fname, "w")
        fo.write("some data.\n")
        fo.close()
        newmeta = datafile.decode_filename(fname)
        with open(fname) as fo:
            fo.read()
        assert metadata.voltage == newmeta.voltage
        assert newmeta.state == datafile.ON

if __name__ == '__main__':
    unittest.main()
