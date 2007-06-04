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
Module for managing FreeBSD firewall feature from Python, using sudo to run
ipfw program.

NOTE: this only works on FreeBSD with firewall option enabled in the kernel.

"""

import sudo
import socketlib


def port_forward(srcport, destport, rule=None):
    """Use firewall rule to forward a TCP port to a different port. Useful for
    redirecting privileged ports to non-privileged ports.  """
    myself = socketlib.get_myaddress()
    rule = rule or srcport
    cmd = "ipfw add %d fwd %s,%d tcp from any to me %d" % (rule, myself, destport, srcport)
    sudo.sudo_command(cmd)
    return rule

def add(rule, action):
    cmd = "ipfw add %d %s" % (rule, action)
    return sudo.sudo_command(cmd)

def delete(rule):
    cmd = "ipfw -f delete %d" % (rule,)
    return sudo.sudo_command(cmd)

def flush():
    return sudo.sudo_command("ipfw -f flush")

# XXX some day make this complete... :-)
class Firewall(object):
    def read(self):
        """Read current rule set."""
        pass


if __name__ == "__main__":
    pass

