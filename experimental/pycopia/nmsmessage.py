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
Register sources and sinks for pyNMS messages. Use the descriptor protocol to
implement a mediated Observer pattern.


"""

class _MessageSwitch(dict):
    def register(self, message, callback):
        try:
            cblist = self[message]
        except KeyError:
            cblist = []
            self[message] = cblist
        cblist.append(callback)

    def unregister(self, message, callback):
        cblist = self[message]
        cblist.remove(callback)
    
    def get_messages(self):
        return map(str, self.keys())

    def register_source(self, message):
        if not self.has_key(message):
            self[message] = []

    def unregister_source(self, message):
        if not self[message]:
            del self[message]
    
    def execute(self, message, *args, **kwargs):
        for cb in self[message]:
            cb(*args, **kwargs)


_SWITCH = _MessageSwitch()
register = _SWITCH.register
unregister = _SWITCH.unregister
sink = _SWITCH.register # alias


# best used as a class attribute
class source(object):
    def __init__(self, name):
        self._name = str(name)
        _SWITCH.register_source(self._name)

    def __get__(self, obj, type=None):
        _SWITCH.execute(self._name, obj)

    def __set__(self, obj, value):
        _SWITCH.execute(self._name, obj, value)

    def __delete__(self, obj):
        _SWITCH.unregister_source(self._name)
    
    def __str__(self):
        return self._name
    
    def __repr__(self):
        return "source(%r)" % (self._name, )


add2builtin("sink", sink)
add2builtin("source", source)




def _test(argv):
    
    class Emitter(object):
        msg_message = source("msg")
    
    class SinkApp(object):
        def __init__(self):
            sink("msg", self.app_handler)

        def app_handler(self, obj, value=None):
            print "Got message with object: %r, value %r" % (obj, value)
    
    emitter = Emitter()
    emitter2 = Emitter()

    sa1 = SinkApp()
    sa2 = SinkApp()

    emitter.msg_message = 1
    emitter.msg_message
    emitter2.msg_message
    del emitter.msg_message
    emitter2.msg_message



if __name__ == "__main__":
    import sys
    _test(sys.argv)

