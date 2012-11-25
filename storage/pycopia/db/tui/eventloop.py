#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
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
from __future__ import division

"""
An urwid event loop that integrates with the Pycopia event loop and timer.
"""

from urwid.main_loop import ExitMainLoop

from pycopia import asyncio
from pycopia import scheduler


class PycopiaEventLoop(object):

    def __init__(self):
        self._idle_handle = 0
        self._idle_callbacks = {}

    def alarm(self, seconds, callback):
        """
        Call callback() given time from from now.  No parameters are
        passed to callback.

        Returns a handle that may be passed to remove_alarm()

        seconds -- floating point time to wait before calling callback
        callback -- function to call from event loop
        """
        return scheduler.get_scheduler().add(seconds, callback=callback)

    def remove_alarm(self, handle):
        """
        Remove an alarm.

        Returns True if the alarm exists, False otherwise
        """
        return scheduler.get_scheduler().remove(handle)

    def watch_file(self, fd, callback):
        """
        Call callback() when fd has some data to read.  No parameters
        are passed to callback.

        Returns a handle that may be passed to remove_watch_file()

        fd -- file descriptor to watch for input
        callback -- function to call when input is available
        """
        asyncio.poller.register_fd(fd, asyncio.EPOLLIN, callback)
        return fd

    def remove_watch_file(self, handle):
        """
        Remove an input file.

        Returns True if the input file exists, False otherwise
        """
        return asyncio.poller.unregister_fd(handle)

    def enter_idle(self, callback):
        """
        Add a callback for entering idle.

        Returns a handle that may be passed to remove_idle()
        """
        return asyncio.poller.register_idle(callback)

    def remove_enter_idle(self, handle):
        """
        Remove an idle callback.

        Returns True if the handle was removed.
        """
        return asyncio.poller.unregister_idle(handle)

    def run(self):
        """
        Start the event loop.  Exit the loop when any callback raises
        an exception.  If ExitMainLoop is raised, exit cleanly.
        """
        try:
            asyncio.poller.loop()
        except ExitMainLoop:
            pass

