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
A sequencer for running various object at different time periods.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from _heapq import heappop, heappush

from pycopia.itimer import FDTimer, gettime, CLOCK_REALTIME
from pycopia import asyncio


class PeriodicTask(asyncio.PollerInterface):
    def __init__(self, callback, period=0.0, delay=0.0, callback_args=()):
        self._callback = callback
        self._args = callback_args
        self._period = period
        self._timer = timer = FDTimer()
        if delay:
            timer.settime(delay, period)
        else:
            timer.settime(period, period)

    def __del__(self):
        self.close()

    def fileno(self):
        return self._timer.fileno()

    def close(self):
        self._timer.close()

    def stop(self):
        self._timer.settime(0.0, 0.0)

    def start(self):
        self._timer.settime(self._period, self._period)

    def readable(self):
        if self._timer.closed:
            return False
        value, interval = self._timer.gettime()
        return not (value == 0.0 and interval == 0.0)

    def read_handler(self):
        count = self._timer.read()
        while count > 0:
            self._callback(*self._args)
            count -= 1
        if self._period == 0.0:
            fd = self._timer.fileno()
            self._timer.close()
            raise asyncio.UnregisterFDNow(fd)


class Sequencer(object):

    def __init__(self, poller=None):
        self._expireq = []
        self._poller = poller or asyncio.Poll()
        self._duration_timer = FDTimer(CLOCK_REALTIME)
        self._poller.register_fd(self._duration_timer.fileno(), asyncio.EPOLLIN, self._duration_timeout)

    def __del__(self):
        self.close()

    def fileno(self):
        return self._poller.fileno()

    poller = property(lambda self: self._poller)

    def close(self):
        if self._poller is not None:
            self._poller.unregister_all()
            self._duration_timer.close()
            for expire, task in self._expireq:
                task.close()
            self._poller = None
            self._duration_timer = None
            self._expireq = []

    def add_task(self, callback, period=0.0, delay=0.0, duration=None, callback_args=()):
        task = PeriodicTask(callback, period, delay, callback_args)
        self._poller.register(task)
        if duration:
            expire = gettime() + duration + delay
            heappush(self._expireq, (expire, task))
            self._duration_timer.settime(self._expireq[0][0], 0.0, absolute=True)

    def _duration_timeout(self):
        count = self._duration_timer.read()
        expire, task = heappop(self._expireq)
        task.stop()
        self._poller.unregister(task)
        task.close()
        if self._expireq:
            self._duration_timer.settime(self._expireq[0][0], 0.0, absolute=True)
        else:
            self._duration_timer.settime(0.0, 0.0)
            self._poller.unregister_fd(self._duration_timer.fileno())

    def run(self, progress_cb=None):
        poller = self._poller
        while self._expireq:
            poller.poll(5.0)
            if progress_cb is not None:
                progress_cb(len(self._expireq))

