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
A Globally Unique Identifier object. Mostly stolen from ASPN snippet.

"""


import random
import time

from pycopia import socket

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
    rand = random.Random()
    ip = ''
    try:
        ip = socket.get_myaddress()
    except (socket.gaierror): # if we don't have an ip, default to someting in the 10.x.x.x private range
        ip = '10'
        for i in range(3):
            ip += '.' + str(rand.randrange(1, 254))
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
                now = long(time.time() * 1000)
                self.guid = ("%016x" % now) + self.__class__.hexip
                # random part
                self.guid += ("%03x" % (self.__class__.rand.randrange(0, 4095)))
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


