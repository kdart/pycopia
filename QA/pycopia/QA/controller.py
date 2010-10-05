#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Abstract interfaces for object controllers.

"""

from pycopia import module

_CONTROLLERMAP = {}


class ControllerError(AssertionError):
    pass


# base class for all types of Controllers. This is the basic interface.
class Controller(object):
    def __init__(self, equipment, logfile=None):
        self._equipment = equipment
        if logfile:
            self.set_logfile(logfile)
        self.initialize()

    def __del__(self):
        self.finalize()
        self.close()

    def set_logfile(self, lf):
        self._logfile = lf

    def __getattr__(self, name):
        return getattr(self._equipment, name)

    def __str__(self):
        return "<%s: %r>" % (self.__class__.__name__, self._equipment)

    def initialize(self):
        pass

    def finalize(self):
        pass

    def close(self):
        pass



def reachable(target):
    from pycopia import ping
    pinger = ping.get_pinger()
    res = pinger.reachable(target)
    pinger.close()
    return res[0][1]


def register_controller(accessmethod, classpath):
    _CONTROLLERMAP[accessmethod] = classpath


# Factory for figuring out the correct Controller to use, determined by
# the "accessmethod" attribute, and returning it.
def get_controller(equipment, accessmethod, logfile=None):
    """Return controller instance that is based on the equipment role."""
    path = _CONTROLLERMAP[accessmethod]
    constructor = module.get_object(path)
    return constructor(equipment, logfile)


def initialize(cf):
    # Built-in accessmethods controllers. More are added at runtime from
    # entries in the "controllers" section of the configuration database.
    register_controller("ssh", "pycopia.QA.ssh_controller.get_controller")
    register_controller("remote", "pycopia.remote.Client.get_controller")
    try:
        cont = cf.get_container("controllers")
    except:
        pass
    else:
        for name, value in cont.iteritems():
            register_controller(name, value)



