.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia SNMP package
====================

Provices SNMP protocol modules and manager objects.

SNMP package
------------

Basic Pythonic SNMP code. There is a low-level interface that allows you to use
raw OIDs in requests, and a high-level that uses object names defined in the
MIB.

.. toctree::
   :maxdepth: 2

.. automodule:: pycopia.SNMP.SNMP
   :members:
   :undoc-members:

.. automodule:: pycopia.SNMP.trapserver
   :members:

.. automodule:: pycopia.SNMP.traps
   :members:

.. automodule:: pycopia.SNMP.Manager
   :members:
   :undoc-members:

Devices
-------

The Devices package contains pre-written device manager objects that
encapsulate device specific functionality. This may include special methods
unique to a device.

For example, the EtherSwitch module allows you to get a table of VLAN entries easily. ::

    manager = EtherSwitch.get_manager(agent, community)
    print manager.get_vlan_table()

There is also support for controlling power switches. New modules can be added as needed.

Modules
-------

.. automodule:: pycopia.Devices.EtherSwitch
   :members:
   :undoc-members:

.. automodule:: pycopia.Devices.APC
   :members:

