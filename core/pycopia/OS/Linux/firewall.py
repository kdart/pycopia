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
Module for managing Linux firewall feature from Python, using sudo to run
ipfw program.

NOTE: this only works on Linux with firewall option enabled in the kernel.

"""

import sudo
#import socketlib


def port_forward(srcport, destport, rule=None):
    """Use firewall rule to forward a TCP port to a different port. Useful for
    redirecting privileged ports to non-privileged ports.  """
    return NotImplemented

def add(rule, action):
    return NotImplemented

def delete(rule):
    return NotImplemented

def flush():
    return NotImplemented

# XXX some day make this complete... :-)
class Firewall(object):
    def read(self):
        """Read current rule set."""
        return NotImplemented

class IPChains(object):
    pass

if __name__ == "__main__":
    pass

