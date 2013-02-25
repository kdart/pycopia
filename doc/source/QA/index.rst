.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia QA package
==================

This package provides a framework for quality assurance roles. It incorporates
years of experience in software testing and hardware testing to provide a means
to write flexible, quick, and robust test cases.

.. toctree::
   :maxdepth: 2

Core Tests and Suites
---------------------

.. automodule:: pycopia.QA.core
   :members:
   :undoc-members:

.. automodule:: pycopia.QA.constants
   :members:
   :undoc-members:

Special runtime configuration
-----------------------------

This is the dynamic configration object that magically creates things that
tests need, such as equipment information, controllers, and reports.

.. automodule:: pycopia.QA.config
   :members:
   :undoc-members:


Running tests and suites
------------------------

.. automodule:: pycopia.QA.testrunner
   :members:
   :undoc-members:

.. automodule:: pycopia.QA.testloader
   :members:

.. automodule:: pycopia.QA.shellinterface
   :members:

.. automodule:: pycopia.QA.jobrunner
   :members:

Supporting Modules
------------------

.. automodule:: pycopia.QA.controller
   :members:
   :undoc-members:

.. automodule:: pycopia.QA.logging
   :members:
   :undoc-members:

