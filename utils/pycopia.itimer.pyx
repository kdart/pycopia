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

    int c_getitimer "getitimer" (int which, itimerval *value)
    int c_setitimer "setitimer" (int which, itimerval *value, itimerval *ovalue)
    int c_nanosleep "nanosleep" (timespec *req, timespec *rem)

    int clock_gettime(int timerid, timespec *value)
    int clock_nanosleep(int clock_id, int flags, timespec *rqtp, timespec *rmtp)


cdef extern from "errno.h":
    int errno

cdef extern double floor(double)
cdef extern double fmod(double, double)

ITIMER_REAL = 0
ITIMER_VIRTUAL = 1
ITIMER_PROF = 2

CLOCK_REALTIME = 0
CLOCK_MONOTONIC = 1

TIMER_ABSTIME = 0x01

EINTR = 4

class ItimerError(Exception):
  pass

cdef double _timeval2float(timeval *tv):
    return <double> tv.tv_sec + (<double> tv.tv_usec / 1000000.0)

cdef double _timespec2float(timespec *tv):
    return <double> tv.tv_sec + (<double> tv.tv_nsec / 1000000000.0)

cdef void _set_timeval(timeval *tv, double n):
    tv.tv_sec = <long> floor(n)
    tv.tv_usec = <long> (fmod(n, 1.0) * 1000000.0)

cdef void _set_timespec(timespec *ts, double n):
    ts.tv_sec = <long> floor(n)
    ts.tv_nsec = <long> (fmod(n, 1.0) * 1000000000.0)


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


def nanosleep(double delay):
    """Sleep for <delay> seconds, with nanosecond precision."""
    cdef timespec ts_delay

    _set_timespec(&ts_delay, delay)
    while c_nanosleep(&ts_delay, &ts_delay) == -1:
        if errno == EINTR:
            PyErr_CheckSignals()
        else:
            raise OSError("nanosleep: (%d) %s" % (errno, strerror(errno)))
    return 0


def absolutesleep(double delay):
    """Sleep for <delay> seconds, with nanosecond precision."""
    cdef timespec ts_delay
    cdef double expire
    cdef int rv

    clock_gettime(CLOCK_REALTIME, &ts_delay)
    expire = _timespec2float(&ts_delay) + delay
    _set_timespec(&ts_delay, expire)

    while 1:
        rv = clock_nanosleep(CLOCK_REALTIME, TIMER_ABSTIME, &ts_delay, NULL)
        if rv == 0:
            break
        elif rv == EINTR:
            PyErr_CheckSignals()
        else:
            raise OSError("absolutesleep: (%d) %s" % (rv, strerror(rv)))
    return 0



