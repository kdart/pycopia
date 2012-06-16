.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.
.. highlight:: console

Pycopia mibs package
====================

This is a package container for the mib files created by the *mib2py* compiler
tool. Compiled-to-Python MIB files are placed in this namespace.

The latest set of pre-compiled mibs, installed separately, is available here:

    http://code.google.com/p/pycopia/downloads/list


After downloading the mib tarball file do the following::

    mkdir -f /var/tmp/mibs
    cd /var/tmp
    tar xzf /path/to/pycopia_mibs.tar.gz

The package is coded to look there also for MIB modules.

