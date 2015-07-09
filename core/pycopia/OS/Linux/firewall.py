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
Module for managing Linux firewall feature from Python, using sudo to run
ipfw program.

NOTE: this only works on Linux with firewall option enabled in the kernel.

"""

import sudo


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

