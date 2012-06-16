.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia storage package
=======================

This package primarily provides the persistent storage model for the other
Pycopia packages *pycopia-QA*, *pycopia-WWW", and *pycopia-SNMP*. It defines a
schema that is used by those packages, so may not be generally useful. However,
the configuration table models a hierarchical storage that you may find useful.

It also provides web app helpers, importers, and exporters.

.. toctree::
   :maxdepth: 2

Models
------

.. automodule:: pycopia.db.models
   :members:


Importers
---------

NMAP Scan Importer
++++++++++++++++++

.. automodule:: pycopia.db.importers.nmap
   :members:

Test Case importer
++++++++++++++++++

.. automodule:: pycopia.db.importers.testcases
   :members:

