.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.

Pycopia core package
====================

These are modules that provide core functionality to the rest of the packages,
but also contains more general modules that may be used independently.

.. toctree::
   :maxdepth: 2

.. automodule:: pycopia.anypath
   :members:

.. automodule:: pycopia.asyncio
   :members:

.. automodule:: pycopia.basicconfig
   :members:

.. automodule:: pycopia.benchmarks
   :members:

.. automodule:: pycopia.cliutils
   :members:

.. automodule:: pycopia.combinatorics
   :members:

.. automodule:: pycopia.daemonize
   :members:

.. automodule:: pycopia.devenviron
   :members:

.. automodule:: pycopia.devhelpers
   :members:

.. automodule:: pycopia.environ
   :members:

.. automodule:: pycopia.ezmail
   :members:

.. automodule:: pycopia.fsm
   :members:

.. automodule:: pycopia.gtktools
   :members:

.. automodule:: pycopia.guid
   :members:

.. automodule:: pycopia.ipv4
   :members:

.. automodule:: pycopia.jsonconfig
   :members:

.. automodule:: pycopia.logfile
   :members:

.. automodule:: pycopia.makepassword
   :members:

.. automodule:: pycopia.methodholder
   :members:

.. automodule:: pycopia.netstring
   :members:

.. automodule:: pycopia.passwd
   :members:

.. automodule:: pycopia.plistconfig
   :members:

.. automodule:: pycopia.protocols
   :members:

.. automodule:: pycopia.re_inverse
   :members:

.. automodule:: pycopia.scheduler
   :members:

.. automodule:: pycopia.sharedbuffer
   :members:

.. automodule:: pycopia.shparser
   :members:

.. automodule:: pycopia.sourcegen
   :members:

.. automodule:: pycopia.ssmtpd
   :members:

.. automodule:: pycopia.sysrandom
   :members:

.. automodule:: pycopia.table
   :members:

.. automodule:: pycopia.stringmatch
   :members:

.. automodule:: pycopia.texttools
   :members:


Measurement
-----------

Objects for dealing with measurement values with units and supports unit conversion.

.. automodule:: pycopia.physics.physical_quantities
   :members:

.. automodule:: pycopia.physics.conversions
   :members:


Internet protocol support
-------------------------

Modules for working with Internet protocols.

.. automodule:: pycopia.inet.httputils
   :members:

.. automodule:: pycopia.inet.fcgi
   :members:

.. automodule:: pycopia.inet.rfc2822
   :members:

.. automodule:: pycopia.inet.SMTP
   :members:

.. automodule:: pycopia.inet.DICT
   :members:


OS Information and interfaces
-----------------------------

A set of modules for interfacing with OS specific features.

Linux
+++++

Linux /proc data
****************

.. automodule:: pycopia.OS.Linux.proc.devices
   :members:

.. automodule:: pycopia.OS.Linux.proc.interrupts
   :members:

.. automodule:: pycopia.OS.Linux.proc.mounts
   :members:

.. automodule:: pycopia.OS.Linux.proc.net.dev
   :members:

.. automodule:: pycopia.OS.Linux.proc.net.netstat
   :members:

.. automodule:: pycopia.OS.Linux.proc.net.route
   :members:

.. automodule:: pycopia.OS.Linux.proc.net.snmp
   :members:


Process info
************

.. automodule:: pycopia.OS.Linux.procfs
   :members:

Devices
*******

.. automodule:: pycopia.OS.Linux.rtc
   :members:

.. automodule:: pycopia.OS.Linux.event
   :members:

.. automodule:: pycopia.OS.Linux.Input
   :members:

.. automodule:: pycopia.OS.Linux.keyboard
   :members:

.. automodule:: pycopia.OS.Linux.mouse
   :members:


SunOS
+++++

Process info
************

.. automodule:: pycopia.OS.SunOS.procfs
   :members:


FreeBSD
+++++++

Process and device info
***********************

.. automodule:: pycopia.OS.FreeBSD.procfs
   :members:




