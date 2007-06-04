#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
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
Module to help with web server configuration.

In a lighttpd.conf file, add this:

    include_shell "/usr/bin/config_lighttpd"

"""

import os

from pycopia import basicconfig


# Master site config. controls all virtual host configuration.
SITE_CONFIG = "/etc/pycopia/website.conf"

class LighttpdConfig(object):
    GLOBAL = """
#server.modules += ("mod_fastcgi")
server.port          = %(port)s
"""

    FCGI_HEAD = "  fastcgi.server = ("
    FCGI_TEMPLATE = """
    "/%(name)s" => (
        (
            "socket" => "%(socketpath)s",
            "check-local" => "disable",
        )
    ),
"""
    FCGI_TAIL = "  )\n"

    VHOST_TEMPLATE = """
$HTTP["host"] == "%(hostname)s" {
  server.document-root = "/var/www/%(hostname)s/htdocs/"
  #server.error-handler-404 = "/error.xhtml" 
  alias.url = ("/media/" => "/var/www/%(hostname)s/media/")
"""
    VHOST_TEMPLATE_TAIL = "}\n"

    def __init__(self):
        self._parts = []

    def add_global(self, **kwargs):
        self._parts.append(self.GLOBAL % kwargs)

    def add_vhost(self, hostname, servers):
        """Add a virtual host section. 
        Provide the virtual host name and a list of FCGI servers to invoke.
        """
        self._parts.append(self.VHOST_TEMPLATE % {"hostname": hostname})
        if servers:
            self._parts.append(self.FCGI_HEAD)
            for server in servers:
                cf = get_server_config(server)
                self._parts.append(self.FCGI_TEMPLATE % {
                        "name": server,
                        "socketpath":cf.SOCKETPATH,
                        })
            self._parts.append(self.FCGI_TAIL)
        self._parts.append(self.VHOST_TEMPLATE_TAIL)

    def __str__(self):
        return "".join(self._parts)

    def emit(self, fo):
        for part in self._parts:
            fo.write(part)


def get_server_config(servername):
    logfilename = "/var/log/%s.log" % (servername,)
    cffilename = "/etc/pycopia/%s.conf" % (servername,)
    pidfile="/var/run/%s.pid" % (servername,)
    socketpath = "/tmp/%s.sock" % (servername,)

    config = basicconfig.get_config(cffilename, 
                CONFIGFILE=cffilename,
                PIDFILE=pidfile,
                SOCKETPATH=socketpath,
                LOGFILENAME=logfilename, 
                SERVERNAME=servername)
    return config

def get_site_config(filename=SITE_CONFIG):
    return basicconfig.get_config(filename)


