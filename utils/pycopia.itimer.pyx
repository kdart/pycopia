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

cdef extern from "sys/time.h":

    cdef struct timeval:
        long int tv_sec
        long int tv_usec

    cdef struct itimerval:
        timeval it_interval
        timeval it_value

    int c_getitimer "getitimer" (int which, itimerval *value)
    int c_setitimer "setitimer" (int which, itimerval *value, itimerval *ovalue)

cdef extern double floor(double)
cdef extern double fmod(double, double)

ITIMER_REAL = 0
ITIMER_VIRTUAL = 1
ITIMER_PROF = 2

class ItimerError(Exception):
  pass

cdef double _timeval2float(timeval *tv):
    return <double> tv.tv_sec + (<double> tv.tv_usec / 1000000.0)

cdef void _set_timeval(timeval *tv, double n):
    tv.tv_sec = <long> floor(n)
    tv.tv_usec = <long> (fmod(n, 1.0) * 1000000.0)

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

