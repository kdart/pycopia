#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Abstract interfaces for object controllers.

"""

import warnings


class ControllerError(AssertionError):
    pass


# base class for all types of Controllers. This is the basic interface.
class Controller(object):
    def __init__(self, equipment, interface, logfile=None):
        self.hostname = equipment["hostname"]
        self._intf = interface # the low-level device interface, whatever it is.
        if logfile:
            self.set_logfile(logfile)
        self.initialize()

    def __del__(self):
        self.finalize()

    def set_logfile(self, lf):
        self._logfile = lf

    def __getattr__(self, name):
        return getattr(self._intf, name)

    def __str__(self):
        return "%s for %r." % (self.__class__.__name__, self.hostname)

    def reachable(self):
        from pycopia import ping
        pinger = ping.get_pinger()
        res = pinger.reachable(self.hostname)
        pinger.close()
        return res[0][1]

    def initialize(self):
        pass

    def finalize(self):
        pass



class HypervisorController(Controller):

    def get_release(self):
        exitstatus, text = self._intf.run("cat /etc/vmware-release")
        if exitstatus:
            return text.strip()
        else:
            return None


class VIXClientController(Controller):
    pass


ROLEMAP = {
    "hypervisor": HypervisorController,
    "vixclient": VIXClientController,
}

def register_role(name, klass):
    if issubclass(klass, Controller):
        ROLEMAP[name] = klass
    else:
        raise ValueError("Controller class must be subclass of Controller.")


# Factory for figuring out the correct Controller to use, determined by
# the "accessmethod" attribute, and returning it.
def get_controller(equipment, accessmethod, logfile=None):
    """Return controller instance that is based on the equipment role."""
    role = equipment["role"]
    if role == "DUT":
        role = equipment["default_role"]
    roleclass = ROLEMAP.get(role, Controller)

    if accessmethod == "ssh":
        #from pycopia.QA import ssh_controller
        #return ssh_controller.get_controller(equipment, logfile)
        return NotImplemented
    elif accessmethod == "remote":
        from pycopia.remote import Client
        client = Client.get_remote(equipment["hostname"])
        return roleclass(equipment, client, logfile=logfile)
    elif accessmethod == "serial":
        return NotImplemented
    elif accessmethod == "telnet":
        return NotImplemented
    elif accessmethod == "http":
        return NotImplemented
    elif accessmethod == "https":
        return NotImplemented
    elif accessmethod == "console":
        return NotImplemented
    elif accessmethod == "snmp":
        return NotImplemented
    else:
        raise ValueError("invalid accessmethod: %r." % accessmethod)


