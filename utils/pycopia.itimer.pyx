# python wrapper for setitimer and getitimer.
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2007  Keith Dart <keith@kdart.com>
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

# definition:
# int getitimer(int which, struct itimerval *value);
# int setitimer(int which, const struct itimerval *value, struct itimerval *ovalue);

from posix.unistd cimport close, read

cdef extern from "Python.h":
    int PyErr_CheckSignals()


#cdef extern from "sys/time.h":
cdef extern from "time.h":

    cdef struct timeval:
       long int tv_sec
       long int tv_usec

    cdef struct itimerval:
       timeval it_interval
       timeval it_value

    cdef struct timespec:
       long int tv_sec
       long int tv_nsec

    cdef struct itimerspec:
        timespec it_interval
        timespec it_value

    int c_getitimer "getitimer" (int , itimerval *)
    int c_setitimer "setitimer" (int , itimerval *, itimerval *)
    int c_nanosleep "nanosleep" (timespec *, timespec *)

    IF UNAME_SYSNAME == "Linux":
        int clock_gettime(int timerid, timespec *value)
        int clock_nanosleep(int clock_id, int flags, timespec *rqtp, timespec *rmtp)

cdef extern from "string.h":
    char *strerror(int errnum)

cdef extern from "errno.h":
    int errno

cdef extern double floor(double)
cdef extern double fmod(double, double)


ITIMER_REAL = 0
ITIMER_VIRTUAL = 1
ITIMER_PROF = 2


CLOCK_REALTIME = 0
CLOCK_MONOTONIC = 1
DEF CLOCK_REALTIME = 0
DEF CLOCK_MONOTONIC = 1

DEF TIMER_ABSTIME = 0x01
DEF TFD_TIMER_ABSTIME = 1
DEF EINTR = 4


cdef inline void _set_timeval(timeval *tv, double n):
    tv.tv_sec = <long> floor(n)
    tv.tv_usec = <long> (fmod(n, 1.0) * 1000000.0)


cdef inline double _timeval2float(timeval *tv):
    return <double> tv.tv_sec + (<double> tv.tv_usec / 1000000.0)


cdef inline void _set_timespec(timespec *ts, double n):
    ts.tv_sec = <long> floor(n)
    ts.tv_nsec = <long> (fmod(n, 1.0) * 1000000000.0)


class ItimerError(Exception):
  pass


def alarm(double delay):
    """Arrange for SIGALRM to arrive after the given number of seconds.
The argument may be floating point number for subsecond precision. Returns
the original value of the timer.
    """
    cdef itimerval new
    cdef itimerval old

    _set_timeval(&new.it_value, delay)
    new.it_interval.tv_sec = new.it_interval.tv_usec = 0
    if c_setitimer(0, &new, &old) == -1:
        raise ItimerError, "Could not set itimer for alarm"
    return _timeval2float(&old.it_value)


def setitimer(int which, double delay, double interval=0.0):
    """setitimer(which, delay, interval)
Sets the given itimer to fire after value delay and after that every interval
seconds. Interval can be omitted. Clear by setting seconds to zero.
Returns old values as a tuple: (delay, interval).
    """
    cdef itimerval new
    cdef itimerval old

    _set_timeval(&new.it_value, delay)
    _set_timeval(&new.it_interval, interval)
    if c_setitimer(which, &new, &old) == -1:
        raise ItimerError, "Could not set itimer %d" % which
    return _timeval2float(&old.it_value), _timeval2float(&old.it_interval)


def getitimer(int which):
    """getitimer(which)
Returns current value of given itimer.
    """
    cdef itimerval old
    if c_getitimer(which, &old) == -1:
        raise ItimerError, "Could not get itimer %d" % which
    return _timeval2float(&old.it_value), _timeval2float(&old.it_interval)


def nanosleep(double delay):
    """Sleep for <delay> seconds, with nanosecond precision. Unlike
    time.sleep(), signal handlers are run during this sleep."""
    cdef timespec ts_delay

    _set_timespec(&ts_delay, delay)
    while c_nanosleep(&ts_delay, &ts_delay) == -1:
        if errno == EINTR:
            PyErr_CheckSignals()
        else:
            raise OSError((errno, strerror(errno)))
    return 0


IF UNAME_SYSNAME == "Linux":

    cdef extern from "sys/timerfd.h":
        int timerfd_create (int, int)
        int timerfd_settime (int, int, itimerspec *, itimerspec *)
        int timerfd_gettime (int, itimerspec *)

    DEF TFD_CLOEXEC = 02000000
    DEF TFD_NONBLOCK = 00004000

    cdef inline double _timespec2float(timespec *tv):
        return <double> tv.tv_sec + (<double> tv.tv_nsec / 1000000000.0)


    def absolutesleep(double time, int clockid=CLOCK_REALTIME):
        """Sleep until <time>, with nanosecond precision. Signal
        handlers are run while sleeping."""
        cdef timespec ts_delay
        cdef int rv

        _set_timespec(&ts_delay, time)
        while 1:
            rv = clock_nanosleep(clockid, TIMER_ABSTIME, &ts_delay, NULL)
            if rv == EINTR:
                PyErr_CheckSignals()
            elif rv == 0:
                return 0
            else:
                raise OSError((rv, strerror(rv)))


    def gettime(int clockid=CLOCK_REALTIME):
        cdef timespec time
        if clock_gettime(clockid, &time) == -1:
            raise OSError((errno, strerror(errno)))
        return _timespec2float(&time)


    cdef extern from "stdint.h":
    #if __WORDSIZE == 64
        ctypedef unsigned long int uint64_t
    #else
        ctypedef unsigned long long int uint64_t
    #endif


    cdef class FDTimer:
        """A timer that is a file-like object. It may be added to select or poll. A
        read returns the number of times timer has expired since last read.
        """
        cdef int _fd

        def __init__(self, int clockid=CLOCK_MONOTONIC, int flags=TFD_CLOEXEC):
            cdef int fd = -1
            fd = timerfd_create(clockid, flags)
            if fd == -1:
                raise OSError((errno, strerror(errno)))
            self._fd = fd

        def __dealloc__(self):
            self.close()

        def __nonzero__(self):
            cdef itimerspec ts
            if self._fd == -1:
                return False
            if timerfd_gettime(self._fd, &ts) == -1:
                raise OSError((errno, strerror(errno)))
            return not (ts.it_value.tv_sec == 0 and ts.it_value.tv_nsec == 0 and
                    ts.it_interval.tv_sec == 0 and ts.it_interval.tv_nsec == 0)

        def close(self):
            if self._fd != -1:
                close(self._fd)
                self._fd = -1

        def fileno(self):
            return self._fd

        property closed:
            def __get__(self):
                return self._fd == -1

        def settime(self, double expire, double interval, int absolute=0):
            """Set time for initial timeout, and subsequent intervals. Set interval
            to zero for one-shot timer.
            """
            cdef itimerspec ts
            cdef timespec ts_interval
            cdef timespec ts_expire
            cdef int flags
            _set_timespec(&ts_expire, expire)
            _set_timespec(&ts_interval, interval)
            ts.it_interval = ts_interval
            ts.it_value = ts_expire
            if timerfd_settime(self._fd, TFD_TIMER_ABSTIME if absolute else 0, &ts, NULL) == -1:
                raise OSError((errno, strerror(errno)))

        def gettime(self):
            """Returns tuple of (time until next expiration, interval).
            If next is zero, timer is disabled. If interval is zero time is one-shot"""
            cdef itimerspec ts
            if timerfd_gettime(self._fd, &ts) == -1:
                raise OSError((errno, strerror(errno)))
            return _timespec2float(&ts.it_value), _timespec2float(&ts.it_interval)

        def read(self, int amt=-1):
            """Returns number of times timer has expired since last read."""
            cdef uint64_t buf
            cdef int rv
            while 1:
                rv = read(self._fd, &buf, 8)
                if rv == 8:
                    return <unsigned long long> buf
                elif rv == -1 and errno == EINTR:
                    PyErr_CheckSignals()
                else:
                    raise OSError((errno, strerror(errno)))

