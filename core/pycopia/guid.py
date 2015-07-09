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
A Globally Unique Identifier object. Mostly stolen from ASPN snippet.

"""

from pycopia import socket
from pycopia import ifconfig
from pycopia import timelib
from pycopia import sysrandom


class GUID(object):
    '''
     A globally unique identifier that combines ip, time, and random bits.  Since the
     time is listed first, you can sort records by guid.  You can also extract the time
     and ip if needed.

     GUIDs make wonderful database keys.  They require no access to the
     database (to get the max index number), they are extremely unique, and they sort
     automatically by time.   GUIDs prevent key clashes when merging
     two databases together, combining data, or generating keys in distributed
     systems.
    '''
    ip = ''
    try:
        ip = ifconfig.get_myaddress()
    except (socket.gaierror): # if we don't have an ip, default to someting in the 10.x.x.x private range
        ip = '10'
        for i in range(3):
            ip += '.' + str(sysrandom.randrange(1, 254))
    # leave space for ip v6 (65K in each sub)
    hexip = ''.join(["%04x" % long(i) for i in ip.split('.')])
    lastguid = ""

    def __init__(self, guid=None):
        '''Use no args if you want the guid generated (this is the normal method)
       or send a string-typed guid to generate it from the string'''
        if guid is None:
            self.guid = self.__class__.lastguid
            while self.guid == self.__class__.lastguid:
                # time part
                now = long(timelib.now() * 1000)
                self.guid = ("%016x" % now) + self.__class__.hexip
                # random part
                self.guid += ("%03x" % (sysrandom.randrange(0, 4095)))
            self.__class__.lastguid = self.guid

        elif type(guid) == type(self): # if a GUID object, copy its value
            self.guid = str(guid)

        else: # if a string, just save its value
            assert self._check(guid), guid + " is not a valid GUID!"
            self.guid = guid

    def __eq__(self, other):
        '''Return true if both GUID strings are equal'''
        if isinstance(other, self.__class__):
            return str(self) == str(other)
        return 0

    def __str__(self):
        '''Returns the string value of this guid'''
        return self.guid

    def time(self):
        '''Extracts the time portion out of the guid and returns the
           number of milliseconds since the epoch'''
        return long(self.guid[0:16], 16)

    def ip(self):
        '''Extracts the ip portion out of the guid and returns it
           as a string like 10.10.10.10'''
        ip = []
        index = 16
# XXX


def _test(argv):
    guid = GUID()
    guid_s = str(guid)
    guid2 = GUID(guid_s)
    print guid
    print guid2
    assert guid == guid2

if __name__ == "__main__":
    import sys
    _test(sys.argv)


