.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia net package
===================

Networking related modules.

.. toctree::
   :maxdepth: 2

.. automodule:: pycopia.clientserver
   :members:

.. automodule:: pycopia.asyncserver
   :members:

.. automodule:: pycopia.httpserver
   :members:

.. automodule:: pycopia.ping
   :members:

.. automodule:: pycopia.slogsink
   :members:

Protocol modules
----------------

Modules that use the protocol engine to implement low-level protocols. Usually
used for testing servers and clients of these protocols for functionality and
vulnerabilites.

Clients
+++++++

.. automodule:: pycopia.clientservers.clients.http_protocols
   :members:

.. automodule:: pycopia.clientservers.clients.smtp
   :members:


Servers
+++++++

.. automodule:: pycopia.clientservers.servers.http_protocols
   :members:


Measurement package
-------------------

Modules that provide network parameter measurements.

.. automodule:: pycopia.measure.Counters
   :members:


Reporting
---------

.. automodule:: pycopia.pcap.report
   :members:

SSL
---

SSL certificate management, including code to manage a certificate authority.

.. automodule:: pycopia.ssl.CA
   :members:

