#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Basic configuration holder objects.


"""

import sys, os

class BasicConfigError(Exception):
    pass

class ConfigLockError(BasicConfigError):
    pass

class ConfigReadError(BasicConfigError):
    pass


class ConfigHolder(dict):
    """ConfigHolder() Holds named configuration information. For convenience,
it maps attribute access to the real dictionary. This object is lockable, use
the 'lock' and 'unlock' methods to set its state. If locked, new keys or
attributes cannot be added, but existing ones may be changed."""
    def __init__(self, init={}, name=None):
        name = name or self.__class__.__name__.lower()
        dict.__init__(self, init)
        dict.__setattr__(self, "_locked", 0)
        dict.__setattr__(self, "_name", name)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __str__(self):
        n = self._name
        s = ["%s(name=%r)" % (self.__class__.__name__, n)]
        s = s+map(lambda it: "%s.%s = %r" % (n, it[0], it[1]), self.items())
        s.append("\n")
        return "\n".join(s)

    def __setitem__(self, key, value):
        if self._locked and not self.has_key(key):
            raise ConfigLockError, "setting attribute on locked config holder"
        return super(ConfigHolder, self).__setitem__(key, value)

    def __getitem__(self, name):
        return super(ConfigHolder, self).__getitem__(name)

    def __delitem__(self, name):
        return super(ConfigHolder, self).__delitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__
#    __delattr__ = __delitem__

    def lock(self):
        dict.__setattr__(self, "_locked", 1)

    def unlock(self):
        dict.__setattr__(self, "_locked", 0)
    
    def islocked(self):
        return self._locked
    
    def copy(self):
        ch = ConfigHolder(self)
        if self.islocked():
            ch.lock()
        return ch

    def add_section(self, name):
        self.name = SECTION(name)


class SECTION(ConfigHolder):
    def __init__(self, name):
        super(SECTION, self).__init__(name=name)

    def __repr__(self):
        return super(SECTION, self).__str__()


class BasicConfig(ConfigHolder):
    def mergefile(self, filename):
        """Merge in a Python syntax configuration file that should assign
        global variables that become keys in the configuration. Returns
        True if file read OK, False otherwise."""
        if os.path.isfile(filename):
            gb = {} # temporary global namespace for config files.
            gb["SECTION"] = SECTION
            gb["sys"] = sys # in case config stuff needs these.
            gb["os"] = os
            try:
                execfile(filename, gb, self)
            except:
                ex, val, tb = sys.exc_info()
                print >>sys.stderr, "BasicConfig error in %s: %s (%s)." % (
                        filename, ex, val)
                return False
            else:
                return True
        else:
            return False

def get_pathname(basename):
    basename = os.path.expandvars(os.path.expanduser(basename))
    if basename.find(os.sep) < 0:
        basename = os.path.join(os.sep, "etc", "pycopia", basename)
    return basename

# main function for getting a configuration file. gets it from the common
# configuration location (/etc/pycopia), but if a full path is given then
# use that instead.
def get_config(fname, initdict=None, **kwargs):
    fname = get_pathname(fname)
    cf = BasicConfig()
    if cf.mergefile(fname):
        if isinstance(initdict, dict):
            cf.update(initdict)
        cf.update(kwargs)
        return cf
    else:
        raise ConfigReadError, "did not successfully read %r." % (fname,)

def check_config(fname):
    """check_config(filename) -> bool
    Check is a config file can be read without errors and contains
    something.
    """
    fname = get_pathname(fname)
    cf = BasicConfig()
    if cf.mergefile(fname):
        return bool(cf)
    else:
        return False


def _test(argv):
    cf = get_config("ezmail.conf")
    print cf


if __name__ == "__main__":
    _test(sys.argv)

