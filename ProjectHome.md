# Introduction #

> A framework of frameworks for rapid application development in Python. It
> includes packages for XML and XHTML parsing and generating, SNMP manager,
> SMI query API, Cisco-style CLI framework, QA automation, program control,
> and more.

> Some assembly required.

> More documentation is available at the home site. http://www.pycopia.net/

# sub-projects #

> Pycopia is divided up into a collection of sub-projects, each
> concentrating on a specific problem domain or category. The following
> lists the current set of sub-projects.


## pycopia-aid ##
> General purpose objects that enhance Python's core modules.  You can use
> these modules in place of the standard modules with the same name.  This
> package is part of the collection of python packages known as pycopia.

## pycopia-utils ##
> Some functions of Pycopia require root privileges. This module contains
> some helper programs so that Pycopia scripts can run as non-root, but
> still perform some functions that require root (e.g. open ICMP socket,
> SNMP trap port, and syslog port).  It also includes the Python 2.5
> readline module for older Pythons.

## pycopia-core ##
> Core components of the Pycopia application framework.  Modules used by
> other PYcopia packages, that you can also use in your applications. There
> is a asynchronous handler interface, CLI tools, and misc modules.

## pycopia-CLI ##
> Pycopia framework for constructing POSIX/Cisco style command line
> interface tools.  Supports context commands, argument parsing, debugging
> aids.  Modular design allows you to wrap any object with a CLI tool.

## pycopia-debugger ##
> Enhanced Python debugger.  Like pdb, but has more inspection commands,
> colorized output, command history.

## pycopia-process ##
> Modules for running, interacting with, and managing processes.  A process
> manager for spawning and managing multiple processess. Support for Python
> coprocess.  Expect module for interacting with processes. Can connect with
> pipes or pty.  Objects for status reporting and process information.

## pycopia-SMI ##
> Python wrapper for libsmi, providing access to MIB/SMI data files.  Also
> provides a nicer API that is more object-oriented. Includes node
> interators.

## pycopia-mibs ##
> Collection of pre-compiled MIBs for Pycopia SNMP.  These are generated
> Python modules, produced by mib2py program.

## pycopia-SNMP ##
> SNMP protocol module for Python.  Provides SNMP query, traps, and device
> manager objects.

## pycopia-storage ##
> Pycopia persistent storage and object model.  Provides a storage build on
> top of Durus that defines container types and some persistent objects
> useful for networks and network device testing.

## pycopia-QA ##
> Pycopia packages to support professional QA roles.  A basic QA automation
> framework. Provides base classes for test cases, test suites, test
> runners, reporting, lab models, terminal emulators, remote control, and
> other miscellaneous functions.

## pycopia-net ##
> General purpose network related modules.  Modules for updating DNS,
> modeling metworks, measuring networks, and a framework for the creation of
> arbitrary chat-style protocols.

## pycopia-audio ##
> Audio and telephony modules for Python.  Provides modules for controlling
> the alsaplayer program, and interfacing to mgetty/vgetty. Also includes a
> basic telephone answering machine, with email message delivery (you need a
> voice modem).  NOTE: I can't test this code right now, and the alsaplayer
> interface is changing. But it all used to work...

## pycopia-XML ##
> Work with XML in a Pythonic way.  Provides Python(ic) Object Model, or
> POM, for creating, inspecting, or modifying basic XML documents. Partially
> validates documents. This framework requires a DTD for the XML. Never
> "print" XML tags again.

## pycopia-WWW ##
> Pycopia WWW tools and web application framework.  Provides FCGI servers,
> XHTML page generator with functional style interfaces, and lightweight web
> application framework. Designed to work closely with the lighttd front-end
> server.

## pycopia-vim ##
> Extend Vim with Python helpers for Python IDE functionality.  Includes
> enhanced syntax files, color scheme, and key mappings for Python
> development with the vim editor.