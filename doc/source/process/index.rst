.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia Process package
=======================

These are modules control or interact with other processes.

.. toctree::
   :maxdepth: 2

Proctools
---------

Process manager and process objects. Presents a Pythonic file-like interface to
subprocesses.

.. automodule:: pycopia.proctools
   :members:

Expect
------

Interact with processes and other io objects using command-response
interaction. Provids a powerful interaction engine that can invoke callback
function for different events.

.. automodule:: pycopia.expect
   :members:

Utility Modules
---------------

These modules use the Expect object to provide easy access to some common programs.

.. automodule:: pycopia.sshlib
   :members:

.. automodule:: pycopia.sudo
   :members:

.. automodule:: pycopia.crontab
   :members:

