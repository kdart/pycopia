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

class SMBAddress(object):
    def __init__(self, hub_or_addr, slot=0, port=0):
        if isinstance( hub_or_addr, self.__class__):
            self.hub = hub_or_addr.hub
            self.slot = hub_or_addr.slot
            self.port = hub_or_addr.port
        else:
            self.hub = hub_or_addr
            self.slot = slot
            self.port = port

    def __str__(self):
        return "%d:%d:%d" % (self.hub, self.slot, self.port)

    def __repr__(self):
        return "%s(%d, %d, %d)" % (self.__class__.__name__, self.hub, self.slot, self.port)


