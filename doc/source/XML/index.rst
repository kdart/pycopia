.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.

Pycopia XML package
===================

These modules provide methods for parsing, modifying, and generating XML
documents. They have a functional style that allows you to compose document
trees easily.

It is also partially validating, and needs a DTD file to work with. The model
won't allow you to, say, add an attribute to a node if it is not allowed by the
DTD. Or if an attribute is required but not present when serialized to XML an
exception is raised. These DTDs are compiled into a Python form. You add node
objects by instantiated a class with a name based on an element name in the
DTD. This prevents you from accidentally writing invalid XML.

.. toctree::
   :maxdepth: 2

Pythonic Object Model
---------------------

.. automodule:: pycopia.XML.POM
   :members:

.. automodule:: pycopia.XML.POMparse
   :members:

DTD Parsing
-----------

.. automodule:: pycopia.XML.DTD
   :members:



