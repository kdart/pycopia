.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.

Pycopia utils package
=====================

This package collects the compiled (C) modules and utilities. A set of SUID
helpers is installed that allow non-root users to perform certain tasks that
usually require root priviledges.

These are:

pyntping
    Allows opening ICMP sockets for sending pings from the *pycopia.ping* module.

slogsink
    Open an syslog socket and proxy it to a user accessible unix socket.

straps
    Open and SNMP trap port and proxy it to a user accessible Unix socket.

daemonize
    Perform system calls to make any process a daemon process (service that runs in background).


.. toctree::
   :maxdepth: 2

Itimer
------

This module provides the following functions.

* getitimer
* setitimer
* alarm
* nanosleep
* absolutesleep


These provide low-level timing functions that are interruptable and resumable.

.. automodule:: pycopia.itimer
   :members:

