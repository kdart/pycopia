.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.
.. highlight:: console


Pycopia reference documentation
===============================

Pycopia is a collection of useful modules for developing Python applications.
It's primary focus is on applications for network management, software QA and
other kinds of testing, and web applications.

Pycopia is divided into a collection of sub-packages containing modules in
various broad categories. You don't need to install all of them if you don't
need them.

However, some packages depend on others, but the packages are arranged in
dependecy order, as follows.

* aid
* utils
* core
* CLI
* debugger
* process
* SMI
* mibs
* SNMP
* storage
* net
* audio
* XML
* WWW
* QA

IF you only want the *pycopia.CLI* toolkit modules, for example, you only need
to install *pycopia-aid*, *pycopia-utils*, *pycopia-core* and finally
*pycopia-CLI*.

It strives to provide Pythonic_ interfaces for various functionality. You may
find similar modules elsewhere, often ported from Perl or Java, that just don't
have that elegance that a good Python module has. This may take some getting
used to for people not having a good familiarity with the Python language.

Functionality
-------------

Some examples of core functionality include:

SNMP
    An implementation of SNMP v1 and v2c protocol and manager objects. With
    this you can write readable SNMP code that interacts with SNMP enabled
    devices using object names. For example, scalars map to Python attributes
    on the manager object,

SMI
    A library, based on wrapping libsmi, for parsing and accessing MIB files.

POM
    Python Object Model for XML. This is patterned after XML DOM, but is more
    pythonic. It also incorporates some XPath funcionality. You can parse and
    generate XML documents.

XHTML
    Utilities and classes for creating XHTML documents. This is based on the
    Pythonic Object Model (POM) module, also found here. These documents can be
    streamed to a socket, useful for dynamic web content.

WWW.framework
    A web application framework supporting virtual domains, security features,
    AJAJ (asynchronous calls from Javascript to Python with JSON
    serialization), and pure-Python markup generation (no templating language).

process
    Spawn supprocesses. Interact with them using the Expect object. Get process
    stats. Manage a collection of subprocesses with optional restart on failure.

CLI
    Toolkit for making interactive command tools fast and easy.

debugger
    Enhanced Python debugger. More commands and colored output. Spawn your
    editor in the right spot.

QA
    Test harness and framework for running tests, managing tests, and recording
    results. Its focus is on the whole gamut of the testing process, from
    device interaction to test case management to result analysis and reporting.

storage
    A database for keeping persistent configuration, the equipment object
    model, test cases and test results. Used by the network management and QA
    framework tools.

enhancements
    The *pycopia-aid* package includes various modules that imporove on the
    standard modules found in the standard library.


Operating System support
------------------------

Pycopia is developed on, runs on, and targeted for the Linux operating system.
Some modules leverage Linux specific features. While many modules will work on
other operating systems, this set of modules is only guaranteed to work in Linux.


Download
--------

There are no releases to download. You can get the latest code using *subversion*
client. The code is currently hosted at Google code hosting.

Run the following::

    mkdir ~/src
    cd ~/src
    svn checkout http://pycopia.googlecode.com/svn/trunk/ pycopia

That will get you the lastest code from trunk.


Documentation contents
----------------------

.. toctree::
   :maxdepth: 3

   install/index
   aid/index
   utils/index
   core/index
   CLI/index
   debugger/index
   process/index
   SMI/index
   mibs/index
   SNMP/index
   storage/index
   net/index
   audio/index
   XML/index
   WWW/index
   QA/index
   vim/index



.. _Pythonic: http://faassen.n--tree.net/blog/view/weblog/2005/08/06/0

