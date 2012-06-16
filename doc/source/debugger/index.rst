.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia enhanced debugger package
=================================

Provides a debugger that utilizes the pycopia CLI toolkit to provide a nicer
user experience. It also adds new commands.

The *pycopia.autodebug* module is special. You don't actually use anything from
it. But simply importing it will set up the Python interpreter to enter the
debugger on any uncaught exception. Rather than get a plain stack trace and
exiting, you have a change to inspect the program.

This is usually used in module self-test code, like this::

    if __name__ == "__main__":
        from pycopia import autodebug
        # some self test
        # ...


.. toctree::
   :maxdepth: 2

Debugger
--------

Like the standard debugger, but inherits CLI toolkit functionality such as
aliases, shell escapes, history. You can also invoke your text editor on the
current line.

.. automodule:: pycopia.debugger
   :members:

