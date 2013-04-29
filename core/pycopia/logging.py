#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 Keith Dart <keith@dartworks.biz>
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
Replacement logging module. The Java-inspired Python logging module is
overkill, we just let syslog handle everything.

The configuration file /etc/pycopia/logging.conf can set the default
logging parameters.
"""

import sys
import syslog

from pycopia import basicconfig


# stderr functions

def warn(*args):
    print(*args, file=sys.stderr)

def DEBUG(*args, **kwargs):
    """Can use this instead of 'print' when debugging.
    """
    parts = []
    for name, value in kwargs.items():
        parts.append("{}: {!r}".format(name, value))
    print("DEBUG", " ".join(args), ", ".join(parts), file=sys.stderr)

# config file is optional here
try:
    cf = basicconfig.get_config("logging.conf")
except basicconfig.ConfigReadError as err:
    warn(err, "Using default values.")
    FACILITY = "USER"
    LEVEL = "WARNING"
else:
    FACILITY = cf.FACILITY
    LEVEL = cf.LEVEL
    del cf

del basicconfig


syslog.openlog(sys.argv[0].split("/")[-1], syslog.LOG_PID, getattr(syslog, "LOG_" + FACILITY))

_oldloglevel = syslog.setlogmask(syslog.LOG_UPTO(getattr(syslog, "LOG_" + LEVEL)))

def close():
    syslog.closelog()


def debug(msg):
    syslog.syslog(syslog.LOG_DEBUG, _encode(msg))

def info(msg):
    syslog.syslog(syslog.LOG_INFO, _encode(msg))

def notice(msg):
    syslog.syslog(syslog.LOG_NOTICE, _encode(msg))

def notice(msg):
    syslog.syslog(syslog.LOG_NOTICE, _encode(msg))

def warning(msg):
    syslog.syslog(syslog.LOG_WARNING, _encode(msg))

def error(msg):
    syslog.syslog(syslog.LOG_ERR, _encode(msg))

def critical(msg):
    syslog.syslog(syslog.LOG_CRIT, _encode(msg))

def alert(msg):
    syslog.syslog(syslog.LOG_ALERT, _encode(msg))

def emergency(msg):
    syslog.syslog(syslog.LOG_EMERG, _encode(msg))

### set loglevels

def loglevel(level):
    global _oldloglevel
    _oldloglevel = syslog.setlogmask(syslog.LOG_UPTO(level))

def loglevel_restore():
    syslog.setlogmask(_oldloglevel)

def loglevel_debug():
    loglevel(syslog.LOG_DEBUG)

def loglevel_info():
    loglevel(syslog.LOG_INFO)

def loglevel_notice():
    loglevel(syslog.LOG_NOTICE)

def loglevel_warning():
    loglevel(syslog.LOG_WARNING)

def loglevel_error():
    loglevel(syslog.LOG_ERR)

def loglevel_critical():
    loglevel(syslog.LOG_CRIT)

def loglevel_alert():
    loglevel(syslog.LOG_ALERT)


# common logging patterns
def exception_error(prefix):
    ex, val, tb = sys.exc_info()
    error("{}: {}: {}".format(prefix, ex.__name__, val))

def exception_warning(prefix):
    ex, val, tb = sys.exc_info()
    warning("{}: {}: {}".format(prefix, ex.__name__, val))

# compatibility functions

def msg(source, *msg):
    info("{0!s} ** {1!r}".format(source, " ".join(msg)))

def _encode(s):
    return s.encode("ascii").replace("\r\n", " ")

# Allow use of names, and useful aliases, to select logging level.
LEVELS = {
    "DEBUG": syslog.LOG_DEBUG,
    "INFO": syslog.LOG_INFO,
    "NOTICE": syslog.LOG_NOTICE,
    "WARNING": syslog.LOG_WARNING,
    "WARN": syslog.LOG_WARNING,
    "ERR": syslog.LOG_ERR,
    "ERROR": syslog.LOG_ERR,
    "CRIT": syslog.LOG_CRIT,
    "CRITICAL": syslog.LOG_CRIT,
    "ALERT": syslog.LOG_ALERT,
}


class LogLevel(object):
    """Context manager to run a block of code at a specific log level.

    Supply the level name as a string.
    """
    def __init__(self, level):
        self._level = LEVELS[level.upper()]

    def __enter__(self):
        self._oldloglevel = syslog.setlogmask(syslog.LOG_UPTO(self._level))

    def __exit__(self, extype, exvalue, traceback):
        syslog.setlogmask(self._oldloglevel)



