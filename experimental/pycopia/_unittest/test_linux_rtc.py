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
Test the Linux rtc device, and Python interface module.
This test is mostly translated from the rtctest.c program.

"""

# module under test
import Linux.rtc

import qatest
import select
import scheduler
import proc.interrupts
from timelib import now

class RTCBaseTest(qatest.Test):
    def _timeout_cb(self):
        self._timeout = 1

class ReadTimeTest(RTCBaseTest):
    """Read the RTC time/date """
    def test_method(self):
        tm = self.config.rtc.time_read()
        return self.passed("Current RTC date/time is: %s" % (tm,))

class ProcReadTest(RTCBaseTest):
    """Read the RTC /proc entry. """
    def test_method(self):
        pe = self.config.rtc.procinfo()
        self.info(pe)
         # let's just check the battery status too
        self.assert_equal(pe['batt_status'], 'okay', "battery status not ok!")
        return self.passed("Got proc info.")

# the actual test implementation class. There may be more than one of these.
class BlockingReadTest(RTCBaseTest):
    """Normal blocking read. Use scheduler to force a timeout."""
    PREREQUISITES = [qatest.PreReq("ReadTimeTest")]
    def test_method(self):
        # Turn on update interrupts (one per second) */
        self.info("RTC Driver (and Python rtc module) Test.")
        self.irqcount = 0
        rtc = self.config.rtc

        def _rtc_counter():
            irqcount = 0
            while irqcount < 5:
                count, status = rtc.read()  # will block
                irqcount += 1
                self.info(" counted %d (rtc count = %d, status = %s)" % (irqcount, count, status))
            return irqcount
        
        rtc.update_interrupt_on()
        self.info("Counting 5 update (1/sec) interrupts from reading /dev/rtc")
        try:
            # should take 5 seconds to run, timeout is 7 seconds
            irqcount = self.config.sched.iotimeout(_rtc_counter, timeout=7)
        except TimeoutError:
            rtc.update_interrupt_off()
            return self.failed("rtc.read() did not finish before timeout")
        rtc.update_interrupt_off()
        self.assert_equal(irqcount, 5, "wrong count of timer events")
        return self.passed("counted %d events" % (irqcount,))

class SelectTest(RTCBaseTest):
    """Poll the rtc using select"""
    PREREQUISITES = [qatest.PreReq("ReadTimeTest")]
    def test_method(self):
        rtc = self.config.rtc
        self.info("Using select(2) on /dev/rtc")

        def _rtc_counter():
            irqcount = 0
            while irqcount < 5:
                rd, wr, ex = select.select([rtc], [], [], 5)
                if rtc in rd:
                    count, status = rtc.read()  # will not block
                    irqcount += 1
                    self.info(" counted %d (rtc count = %d, status = %s)" % (irqcount, count, status))
            return irqcount

        rtc.update_interrupt_on()
        try:
            # should take 5 seconds to run, timeout is 7 seconds
            irqcount = self.config.sched.iotimeout(_rtc_counter, timeout=7)
        except TimeoutError:
            rtc.update_interrupt_off()
            return self.failed("rtc.read() from select did not finish before timeout")
        rtc.update_interrupt_off()
        self.assert_equal(irqcount, 5, "wrong count of timer events")
        return self.passed("counted %d events" % (irqcount,))


class AlarmTest(RTCBaseTest):
    """Test alarm function."""
    PREREQUISITES = [qatest.PreReq("ReadTimeTest")]
    def test_method(self):
        rtc = self.config.rtc
        # Read the RTC time/date
        tm = rtc.time_read()
        self.info("Current RTC date/time is: %s" % (tm,))
        tm.add_seconds(10)
        rtc.alarm_set(tm)
        # Read the current alarm settings
        tm = rtc.alarm_read()
        self.info("Alarm time now set to: %s" % (tm,))
        start = now()
        rtc.alarm_interrupt_on()
        self.info("Waiting 10 seconds for alarm...")
        count, status = rtc.read()
        self.info("okay. Alarm rang.")
        rtc.alarm_interrupt_off()
        self.assert_approximately_equal(now() - start, 10, 1)
        return self.passed("alarm in specified time")

class PeriodicTest(RTCBaseTest):
    """Test changing of periodic rate."""
    PREREQUISITES = [qatest.PreReq("ReadTimeTest")]
    def test_method(self):
        rtc = self.config.rtc
        # Read periodic IRQ rate 
        rate = rtc.irq_rate_read()
        self.info("Periodic IRQ rate was %ldHz."% (rate,))

        self.info( "Counting 20 interrupts:")
        for freq in [2**i for i in xrange(1, 7)]: # powers of 2
            self.info("setting %2ld Hz, counting 20 events..." % (freq,))
            rtc.irq_rate_set(freq)
            rtc.periodic_interrupt_on()
            for i in range(20):
                rtc.read()
            rtc.periodic_interrupt_off()
            self.info("   counted 20.")
        return self.passed("period test ran") #XXX


class IRQCountTest(RTCBaseTest):
    """Verify that total amount of IRQ firings match what we expect."""
    PREREQUISITES = [qatest.PreReq("ReadTimeTest")]
    def test_method(self):
        self.config.interrupts.update()
        irqcount = self.config.interrupts[8][0].count - self.config.irqstart
        self.info('%s more events on IRQ 8.' % (irqcount,))
        # previous testing determined that this set of tests will fire IRQ 8
        # exactly 131 times. If new tests are added then this number should be
        # hand-verified and changed.
        self.assert_equal(131, irqcount, "strange IRQ count")
        return self.passed("got expected IRQ count")


### suite ###
class RTCSuite(qatest.TestSuite):
    def initialize(self):
        self.config.rtc = Linux.rtc.RTC()
        self.config.sched = scheduler.get_scheduler()
        self.config.interrupts = proc.interrupts.get_interrupts()
        self.config.irqstart = self.config.interrupts[8][0].count

    def finalize(self):
        self.config.rtc.close()
        del self.config.rtc
        del self.config.sched
        del self.config.interrupts


def get_suite(conf):
    suite = RTCSuite(conf)
    suite.add_test(ReadTimeTest)
    suite.add_test(ProcReadTest)
    suite.add_test(BlockingReadTest)
    suite.add_test(SelectTest)
    suite.add_test(AlarmTest)
    suite.add_test(PeriodicTest)
    suite.add_test(IRQCountTest)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()

if __name__ == "__main__":
    import os
    os.system("qaunittest test_linux_rtc")


