#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Controller for remote agents.

"""


from pycopia.QA import controller
from pycopia.remote import Client



class RemoteController(controller.Controller):

    def attach(self, name):
        self._intf = Client.get_remote(name)


def get_controller(device, logfile=None):
    client = Client.get_remote((device.hostname)
    rmt = RemoteController(client, logfile=logfile)
    return rmt
