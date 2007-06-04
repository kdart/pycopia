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
Time related functions. You can use this in place of the stock 'time' module.
It adds some additional time related functions, and a MutableTime class.

This module also provides some time related functions.

"""


from time import *
now = time

# Python time tuple:
# Index   Attribute   Values 
# 0 tm_year (for example, 1993)
# 1 tm_mon range [1,12]
# 2 tm_mday range [1,31]
# 3 tm_hour range [0,23]
# 4 tm_min range [0,59]
# 5 tm_sec range [0,61]; see (1) in strftime() description
# 6 tm_wday range [0,6], Monday is 0
# 7 tm_yday range [1,366]
# 8 tm_isdst 0, 1 or -1; see below

# for some reason the Python time module uses a struct_time that is read only.
# So, this time class mirrors it,  but this can have different elements set. It
# also extends it with related time functionality.
class MutableTime(object):
    INDEXMAP = {"tm_year":0, "tm_mon":1, "tm_mday":2, "tm_hour":3, "tm_min":4,
            "tm_sec":5, "tm_wday":6, "tm_yday":7, "tm_isdst":8,
            # more "rememberable" names...
            "year":0, "month":1, "day":2, "hour":3, "minute":4,
            "second":5, "weekday":6, "yday":7, "isdst":8 }

    def __init__(self, init=None, fmt=None):
        if init is None:
            self._tm = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        else:
            self._tm = list(init)
            assert len(self._tm) == 9
        self._fmt = fmt or "%a %b %d %H:%M:%S %Y"

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self._tm, self._fmt)

    def __str__(self):
        return strftime(self._fmt, self._tm)

    def __iter__(self):
        return iter(self._tm)

    def __float__(self):
        return mktime(self._tm)

    def __int__(self):
        return int(self.__float__())

    def __coerce__(self, other):
        try:
            return mktime(self._tm), float(other)
        except:
            return None

    def __len__(self):
        return len(self._tm)

    def __eq__(self, other):
        return list(self) == list(other)

    def __getitem__(self, idx):
        return self._tm[idx]

    def __setitem__(self, idx, val):
        self._tm[idx] = int(val)

    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            try:
                return self._tm[self.INDEXMAP[key]]
            except KeyError:
                raise AttributeError, "no attribute '%s' found." % (key,)

    def __setattr__(self, name, val):
        idx = self.INDEXMAP.get(name, None)
        if idx is None:
            object.__setattr__(self, name, val)
        else:
            self._tm[idx] = int(val)

    def __sub__(self, other):
        return mktime(self._tm) - mktime(tuple(other))

    def __add__(self, secs):
        new = self.__class__(self._tm[:], self._fmt)
        new.add_seconds(secs)
        return new

    def __mul__(self, other):
        return mktime(self._tm) * float(other)

    def __div__(self, other):
        return mktime(self._tm) / float(other)

    def __iadd__(self, secs):
        csec = mktime(self._tm)
        csec += secs
        self._tm = localtime(csec)
        return self

    def __isub__(self, secs):
        csec = mktime(self._tm)
        csec -= secs
        self._tm = localtime(csec)
        return self
    
    def copy(self):
        return self.__class__(self._tm, self._fmt)

    def localtime(self, secs=None):
        if secs: # must do it this way because these functions check arg length, not value.
            self._tm = list(localtime(secs))
        else:
            self._tm = list(localtime())
        return self

    def gmtime(self, secs=None):
        if secs:
            self._tm = list(gmtime(secs))
        else:
            self._tm = list(gmtime())
        return self

    def strftime(self, fmt=None):
        return strftime(fmt or self._fmt, self._tm)

    def strptime(self, val, fmt=None):
        ttl = list(strptime(val, fmt or self._fmt))
        ttl[-1] = localtime()[-1] # preserve dstflag - bug workaround
        self._tm = ttl
        return self

    def set_format(self, fmt):
        self._fmt = str(fmt)

    def add_seconds(self, secs):
        self.__iadd__(secs)

    def add_minutes(self, mins):
        self.add_seconds(mins*60)

    def add_hours(self, hours):
        self.add_seconds(hours*3600)

    def add(self, minutes=0, hours=0, days=0, weeks=0):
        self.add_seconds(seconds(minutes, hours, days, weeks))

    def add_time(self, timediff):
        """add_time(timediff) Adds specificed amount of time to the current
        time held in this object. The format of difftime is a string,
        "HH:MM:SS"."""
        [h, m, s] = map(int, timediff.split(":"))
        self.add_seconds(h*3600+m*60+s)


# time module equivalents that return MutableTime objects.
def localtime_mutable(secs=None):
    mt = MutableTime()
    mt.localtime(secs)
    return mt

def gmtime_mutable(secs=None):
    mt = MutableTime()
    mt.gmtime(secs)
    return mt

def strptime_mutable(string, fmt=None):
    mt = MutableTime(fmt=fmt)
    mt.strptime(string)
    return mt

def weekof(secs=None):
    """Returns a date that is the Monday of the week specified in universal seconds."""
    if secs is None:
        secs = time()
    secs = ((secs // 604800)*604800)-172800
    return localtime(secs)

def seconds(minutes=0, hours=0, days=0, weeks=0):
    """Returns a value in seconds given some minutes, hours, days, or weeks."""
    return minutes*60 + hours*3600 + days*86400 + weeks*604800

def HMS(secs):
    """Return tuple of hours, minutes, and seconds given value in seconds."""
    minutes, seconds = divmod(secs, 60.0)
    hours, minutes = divmod(minutes, 60.0)
    return hours, minutes, seconds

def HMS2str(hours, minutes, seconds):
    return "%02.0f:%02.0f:%02.2f" % (hours, minutes, seconds)

def gmtimestamp(fmt="%a, %d %b %Y %H:%M:%S +0000", tm=None):
    return strftime(fmt, tm or gmtime())
rfc822time = gmtimestamp

def timestamp(secs=None, fmt="%a, %d %b %Y %H:%M:%S +0000"):
    """Return string with current time, according to given format. Default is
rfc822 compliant date value."""
    if secs:
        return strftime(fmt, gmtime(secs))
    else:
        return strftime(fmt, gmtime())

def localtimestamp(secs=None, fmt="%a, %d %b %Y %H:%M:%S %Z"):
    """Return string with , according to given format. Default is
rfc822 compliant date value."""
    if secs:
        return strftime(fmt, localtime(secs))
    else:
        return strftime(fmt, localtime())


if __name__ == "__main__":
    mt = localtime_mutable()
    print mt
    mt.add_seconds(3600)
    print mt
    print strftime("%Y-%m-%d", weekof(time()))

    t = now()
    for d in range(1, 60):
        week = weekof(t+(d*60*60*24))
        print MutableTime(week)
    
    print "Local time:"
    print localtimestamp()


