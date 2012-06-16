.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia WWW package
===================

Modules for working with the world wide web protocols and documents. This
package contains the web application framework ad various document parsers and
generators.

.. toctree::
   :maxdepth: 2

Documents
---------

.. automodule:: pycopia.WWW.XHTML
   :members:

.. automodule:: pycopia.WWW.XHTMLparse
   :members:

.. automodule:: pycopia.WWW.HTML5
   :members:

.. automodule:: pycopia.WWW.HTML5parse
   :members:


Client support
--------------

A web client based on curl library. Can also perform parallel requests.

.. automodule:: pycopia.WWW.client
   :members:


Application framework
---------------------

.. automodule:: pycopia.WWW.framework
   :members:

.. automodule:: pycopia.WWW.website
   :members:

.. automodule:: pycopia.WWW.json
   :members:

.. automodule:: pycopia.WWW.fcgiserver
   :members:


Application middleware
----------------------

.. automodule:: pycopia.WWW.middleware.auth
   :members:

