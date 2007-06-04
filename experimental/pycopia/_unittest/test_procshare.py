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
Test the procshare module.

"""

import qatest

import procshare
import proctools

proctools.use_shared_objects()



class Producer(object):
    def __init__(self, queue):
        self.queue = queue
        self._val = 0

    def run(self):
        import scheduler
        import traceback
        try:
            while 1:
                scheduler.sleep(1.0)
                self.queue.insert(0, self._val)
                self._val += 1
        except KeyboardInterrupt:
            return 0 # Exit status
        except:
            traceback.print_exc()
            return 1 # Exit status



class Consumer(object):
    def __init__(self, queue):
        self.queue = queue

    def run(self):
        import scheduler
        import traceback
        try:
            while 1:
                try:
                    item = self.queue.pop()
                except IndexError:
                    scheduler.sleep(0.5)
        except KeyboardInterrupt:
            return 0 # Exit status
        except:
            traceback.print_exc()
            return 1 # Exit status



class ProcshareBaseTest(qatest.Test):
    pass


class ProducerTest(ProcshareBaseTest):
    """Spawn a producer, I am the consumer."""
    def initialize(self):
        q = procshare.SharedList()
        self.q = procshare.share(q)

    def finalize(self):
        del self.q

    def test_method(self):
        import scheduler
        p = Producer(self.q)
        #c = Consumer(self.q)
        procp = proctools.submethod(p.run)
        item = self.queue.pop()
        n = 0
        try:
            while n<10:
                try:
                    item = self.q.pop()
                    self.info("Consumer got item: %s" % (item,))
                except IndexError:
                    scheduler.sleep(0.5)
                n += 1
        finally:
            procp.kill()
            procp.wait()


### suite ###
class ProcshareSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = ProcshareSuite(conf)
    suite.add_test(ProducerTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()

