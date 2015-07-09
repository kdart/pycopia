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
Implements an SNMP agent role.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

class Agent(object):
    """
An instance of this class will act as an SNMP agent. This is a generic base
class that should be subclassed by a module in the Devices package to implement
a specific Agent.

    """
    def add_mibs(self, XXX):
        raise NotImplementedError

    def add_mib(self, XXX):
        raise NotImplementedError

    def open(self, socket=161):
        pass

    def send_trap(self, XXX):
        pass

    def register_managed_object(self, oid, callback):
        pass



