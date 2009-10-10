#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>
# $Id$

"""
Abstract interfaces for object controllers.

"""


class ControllerError(AssertionError):
    pass


# base class for all types of Controllers.
class Controller(object):
    def __init__(self, intf, logfile=None):
        self._intf = intf # the low-level device interface, whatever it is.
        if logfile:
            self.set_logfile(logfile)
        self.initialize()

    def __del__(self):
        self.finalize()

    def set_logfile(self, lf):
        try:
            self._intf.set_logfile(lf)
        except AttributeError:
            pass

    def initialize(self):
        pass

    def finalize(self):
        pass


# factory for figuring out the correct Controller to use, and returning it.
def get_controller(dut, logfile=None):
    return _get_controller(dut, dut.accessmethod, logfile)


def get_initial_controller(dut, logfile=None):
    return _get_controller(dut, dut.initialaccessmethod, logfile)


def _get_controller(dut, cm, logfile):
    if cm == "ssh":
        from pycopia.QA import ssh_controller
        return ssh_controller.get_controller(dut, logfile)
    elif cm == "remote":
        from pycopia.QA import remote_controller
        return remote_controller.get_controller(dut, logfile)
    elif cm == "serial":
        return NotImplemented
    elif cm == "telnet":
        return NotImplemented
    elif cm == "http":
        return NotImplemented
    elif cm == "https":
        return NotImplemented
    elif cm == "console":
        return NotImplemented
    elif cm == "snmp":
        return NotImplemented
    else:
        raise ValueError, "invalid configuration method: %s." % (cm,)


