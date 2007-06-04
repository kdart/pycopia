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
This is a generic Python interface for an I2C bus device interface.

"""

import sys, os

class I2CError(Exception):
    def __str__(self):
        return self.__doc__

class SNAError(I2CError):
    "Slave Not Acknowledging"

class BusyError(I2CError):
    "Unit busy, command ignored."

class ArbitrationError(I2CError):
    "Arbitration Loss Detected"

class BusError(I2CError):
    "Bus error detected."

class BusTimeoutError(I2CError):
    "Bus time-out detected"

class NotOpenError(I2CError):
    "Port connection not open."

class ArgumentError(I2CError):
    "Invalid command argument."

class NoRequestError(I2CError):
    "Slave Transmit Request not active, command ignored."

class InvalidCommandError(I2CError):
    "Invalid controller command"

class BufferOverflowError(I2CError):
    "Receiver buffer overflow"

# generic base class for I2C controller devices. Subclass this for a
# specific type. This is here to define the interface.
class I2CController(object):
    def __init__(self):
        self.address = 0
        self.callback = lambda x: x # a null function
        self._allow_general_call = 1

    def open(self):
        pass

    def close(self):
        pass
    
    def set_my_address(self, address):
        pass

    def set_destination(self, destaddr):
        pass

    def master_read(self, destaddr=None):
        pass

    def master_write(self, data, destaddr=None):
        pass

    def reset(self):
        pass

    # this would normally be called from the responder callback
    def slave_write(self, data):
        pass

    def register_slave_callback(self, callback):
        self.callback = callback

    def allow_general_call(self, yesorno):
        self._allow_general_call = yesorno # 0 or 1 (false or true)


# This is an RS-232 to I2C host adapter device. Its interface to the host
# machine is an RS-232 serial port. However, we allow for connection
# through terminal servers. You jsut need to pass in any kind of port
# object that supports send and expect methods.
class MIIC202(I2CController):
    def __init__(self, port):
        I2CController.__init__(self)
        self.port = port # a telnet, socket, or tty port object

    def open(self):
        pass

    def close(self):
        pass
    
    def set_my_address(self, address):
        pass

    def set_destination(self, destaddr):
        pass

    def master_read(self, destaddr=None):
        pass

    def master_write(self, data, destaddr=None):
        pass

    def reset(self):
        self.port.send("\r\r\r")
        self.port.expect("*")

    # this would normally be called from the responder callback
    def slave_write(self, data):
        pass



# factory function to figure out what kind of controller object to get
# based on the given parameters. argv[0] is the model name.
def get_controller(*argv):
    try:
        klass = getattr(__dict__, argv[0])
    except:
        raise ValueError, "That model of controller is not supported."
    return apply( klass, argv[1:])

