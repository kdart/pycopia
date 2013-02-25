.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia CLI toolkit
===================

A toolkit for quickly creating interactive command interfaces. The interface is
similar to a shell (command, options, and arguments), but supports "contexts",
built-in help, and colorized prompts.

You can use this to wrap other Python objects to interact with them.

.. toctree::
   :maxdepth: 2

.. automodule:: pycopia.CLI
   :members:
   :undoc-members:

.. automodule:: pycopia.UI
   :members:
   :undoc-members:

.. automodule:: pycopia.IO
   :members:
   :undoc-members:

Examples
--------

These are complete CLI implementations that let you navigate some hierarchical
configuration formats and edit them interactively.

.. automodule:: pycopia.jsoncli
   :members:

.. automodule:: pycopia.plistcli
   :members:

