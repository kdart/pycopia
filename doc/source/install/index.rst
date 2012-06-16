.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia Installation
====================

How to install Pycopia as a test framework.

General
-------

Pycopia is divided into packages that can be used for various roles. These
instructions describe how to install the full system for running as a QA
framework.

Pycopia runs on most Linux distributions. However, some may not have dependent
packages available or not the right versions. These documents describe how to
install in specific Linux distributions.

You will need a basic development environment installed (gcc plus "dev" packages).

Installation is a little bit of a chore. This system is really intended to
be installed and run in a testing or QA "appliance". That is, a the whole
system pre-installed in a dedicated host or virtual machine. If you would like
a VMware virtual machine image instead just let us know.


Main Setup Script
-----------------

The top-level setup script helps with dealing with all sub-packages at
once. It also provides an installer for a developer mode.

Invoke it like a standard setup.py script. However, Any names after the
operation name are taken as sub-package names that are operated on. If no
names are given then all packages are operated on.

Commands:

 list
    List available subpackages. These are the names you may optionally supply.
 publish
    Put source distribution on pypi.
 build
    Run setuptools build phase on named sub-packages (or all of them).
 install
    Run setuptools install phase.
 eggs
    Build distributable egg package.
 rpms
    Build RPMs on platforms that support building RPMs.
 msis
    Build Microsoft .msi on Windows.
 wininst
    Build .exe installer on Windows.
 develop
    Developer mode, as defined by setuptools.
 develophome
    Developer mode, installing .pth and script files in user directory.
 clean
    Run setuptools clean phase.
 squash
    Squash (flatten) all named sub-packages into single tree
    in $PYCOPIA_SQUASH, or user site-directory if no $PYCOPIA_SQUASH defined.
    This also removes the setuptools runtime dependency.


Most regular setuptools commands also work. They are passed through by
default. For a basic intallation you just need to use the `install` command.

NOTE: The install operation requires that the sudo command be configured for
      you, or you run it as root.

.. toctree::
   :maxdepth: 2

   ubuntu_LTS

   gentoo

   CentOS

   Redhat


