#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

