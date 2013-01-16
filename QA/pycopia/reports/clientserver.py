#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
#from __future__ import unicode_literals
from __future__ import division

"""
Special report/output that sends report messages to a socket.

The "reports" section of the configuration should have:

    remote=('pycopia.reports.database.clientserver.RemoteReport',)

Then you can use this as `--reportname=remote` in a test

This can be used to adapt the synchronous nature of running test scripts to
asynchronous user interfaces.
"""

import sys
import os
import struct
import cPickle as pickle

from pycopia import reports
from pycopia import socket
from pycopia import asyncio


NO_MESSAGE = "no message"


def _get_path():
    return "/tmp/qareport-{}.s".format(os.getuid())


class RemoteReport(reports.NullReport):
    """An object with a report interface that sends messages to a socket. Use
    this from the test framework, running a test.
    """

    def __init__(self):
        self._sock = socket.connect_unix(_get_path())
        self._packer = struct.Struct("II")

    def __del__(self):
        self.close()

    def close(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def _send(self, mid, *args):
        d = pickle.dumps(args)
        h = self._packer.pack(mid, len(d))
        self._sock.sendall(h+d)

    def initialize(self, config=None):
        self._send(0, None)

    def logfile(self, filename):
        self._send(1, filename)

    def finalize(self):
        self._send(2)

    def add_title(self, title):
        self._send(3, title)

    def add_heading(self, text, level=1):
        self._send(4, text, level)

    def add_message(self, msgtype, msg, level=1):
        self._send(5, msgtype, msg, level)

    def add_summary(self, entries):
        lines = [(repr(entry), entry.result) for entry in entries]
        self._send(6, lines)

    def add_text(self, text):
        self._send(7, text)

    def add_analysis(self, text):
        self._send(8, text)

    def add_data(self, data, note=None):
        self._send(9, data, note)

    def add_url(self, text, url):
        self._send(10, text, url)

    def passed(self, msg=NO_MESSAGE, level=1):
        self._send(11, msg, level)

    def failed(self, msg=NO_MESSAGE, level=1):
        self._send(12, msg, level)

    def expectedfail(self, msg=NO_MESSAGE, level=1):
        self._send(13, msg, level)

    def incomplete(self, msg=NO_MESSAGE, level=1):
        self._send(14, msg, level)

    def abort(self, msg=NO_MESSAGE, level=1):
        self._send(15, msg, level)

    def info(self, msg, level=1):
        self._send(16, msg, level)

    def diagnostic(self, msg, level=1):
        self._send(17, msg, level)

    def newpage(self):
        self._send(18)

    def newsection(self):
        self._send(19)


#### server side.

class LocalReportProxy(asyncio.AsyncWorkerHandler):

    REPORT = None

    _METHODMAP = {
        0: "initialize",
        1: "logfile",
        2: "finalize",
        3: "add_title",
        4: "add_heading",
        5: "add_message",
        6: "add_summary",
        7: "add_text",
        8: "add_analysis",
        9: "add_data",
        10: "add_url",
        11: "passed",
        12: "failed",
        13: "expectedfail",
        14: "incomplete",
        15: "abort",
        16: "info",
        17: "diagnostic",
        18: "newpage",
        19: "newsection",
    }

    def initialize(self):
        self._packer = struct.Struct("II")

    def read_handler(self):
        self._read()
        while socket.inq(self._sock):
            self._read()

    def _read(self):
        data = self._sock.recv(self._packer.size)
        if not data:
            return
        tag, length = self._packer.unpack(data)
        p = self._sock.recv(length)
        args = pickle.loads(p)
        getattr(self.REPORT, LocalReportProxy._METHODMAP[tag])(*args)


class ReportReceiver(object):
    """Manages a report receiver (server).
    Supply another object with a report interface that will be called.
    """
    def __init__(self, destination_report):
        class ReportProxyWrapper(LocalReportProxy):
            REPORT = destination_report
        sock = socket.unix_listener(_get_path())
        self._h = asyncio.AsyncServerHandler(sock, ReportProxyWrapper)

    def close(self):
        if self._h is not None:
            self._h.close()
            self._h = None
            os.unlink(_get_path())


if __name__ == "__main__":
    from pycopia import reports
    from pycopia import scheduler

    rpt = reports.get_report( ("StandardReport", "-", "text/plain") )

    rx = ReportReceiver(rpt)
    tx = RemoteReport()

    def txstepper(tx):
        yield tx.initialize()
        yield tx.add_title("The Title")
        yield tx.add_heading("Some heading")
        yield tx.info("some info")
        yield tx.passed("A message for a passed condition.")
        yield tx.finalize()

    scheduler.get_scheduler().add(0.1, callback=txstepper(tx).next, repeat=True)
    try:
        try:
            asyncio.poller.loop()
        except StopIteration:
            pass
    finally:
        tx.close()
        rx.close()

