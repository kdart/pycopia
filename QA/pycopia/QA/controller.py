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


class ControllerError(Exception):
    pass


# base class for all types of Controllers. This is the basic interface.
class Controller(object):
    def __init__(self, equipment, logfile=None):
        self._equipment = equipment
        if logfile:
            self.set_logfile(logfile)
        else:
            self._logfile = None
        self.initialize()

    def __del__(self):
        self.finalize()
        self.close()

    def set_logfile(self, lf):
        if not hasattr(lf, "write"):
            raise ValueError("Logfile object must have write method.")
        self._logfile = lf

    def writelog(self, text):
        if self._logfile is not None:
            self._logfile.write(text)

    def __str__(self):
        return "<%s: %r>" % (self.__class__.__name__, self._equipment)

    def initialize(self):
        pass

    def finalize(self):
        pass

    def close(self):
        pass


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



