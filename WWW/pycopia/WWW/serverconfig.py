#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
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

    include_shell "/usr/libexec/pycopia/config_lighttpd"

"""

import os

from pycopia import basicconfig
from pycopia import socket

SITE_CONFIG = "/etc/pycopia/website.conf"


class LighttpdConfig(object):
    GLOBAL = """
server.port          = %(port)s
"""

# See: http://redmine.lighttpd.net/projects/lighttpd/wiki/Docs:SSL
    GLOBAL_SSL = """
$SERVER["socket"] == ":%(sslport)s" {
  ssl.engine    = "enable"
  ssl.cipher-list = "ECDHE-RSA-AES256-SHA384:AES256-SHA256:RC4-SHA:RC4:HIGH:!MD5:!aNULL:!EDH:!AESGCM"
  ssl.ca-file   = "/etc/pycopia/ssl/ca-certs.crt"
  ssl.pemfile   = "/etc/pycopia/ssl/localhost.crt"
  server.document-root = "/var/www/localhost/htdocs-secure"
}
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
  accesslog.filename = var.logdir + "/%(hostname)s/access.log"
  #server.error-handler-404 = "/error-404.html"
  alias.url = ("/media/" => "/var/www/%(hostname)s/media/")
  %(SSL)s
"""
    VHOST_TEMPLATE_TAIL = "}\n"

    VHOST_TEMPLATE_SSL = """ ssl.pemfile = "/etc/pycopia/ssl/%(hostname)s.crt" """

    REDIR_TEMPLATE = """
$HTTP["host"] == "%(hostname)s" {
    url.redirect = ( ".*" => "http://%(fqdn)s" )
}
"""

    def __init__(self):
        self._parts = []
        self._myhostname = os.uname()[1].split(".")[0]

    def add_global(self, **kwargs):
        self._parts.append(self.GLOBAL % kwargs)

    def add_vhost(self, hostname, servers, usessl=False):
        """Add a virtual host section.
        Provide the virtual host name and a list of FCGI servers to invoke.
        """
        if usessl:
            ssl = self.VHOST_TEMPLATE_SSL % {"hostname": hostname}
        else:
            ssl = ""
        self._parts.append(self.VHOST_TEMPLATE % {"hostname": hostname, "SSL": ssl})
        if servers:
            self._parts.append(self.FCGI_HEAD)
            for server in servers:
                cf = _get_server_config(server)
                self._parts.append(self.FCGI_TEMPLATE % {
                        "name": server,
                        "socketpath":cf.SOCKETPATH,
                        })
            self._parts.append(self.FCGI_TAIL)
        self._parts.append(self.VHOST_TEMPLATE_TAIL)
        # Redirect plain host name to FQDN. You might see this on local networks.
        if "." in hostname:
            hp = hostname.split(".")[0]
            if hp == self._myhostname:
                self._parts.append(self.REDIR_TEMPLATE % {"hostname":hp, "fqdn": hostname})

    def add_ssl_support(self, sslport):
        self._parts.append(self.GLOBAL_SSL % {"sslport":sslport})

    def __str__(self):
        return "".join(self._parts)

    def emit(self, fo):
        for part in self._parts:
            fo.write(part)


def _get_server_config(servername):
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
    glbl = {"FQDN": socket.get_fqdn()}
    return basicconfig.get_config(filename, globalspace=glbl)


def config_lighttpd(argv, filelike):
    config = get_site_config()
    ltc = LighttpdConfig()
    ltc.add_global(port=config.PORT)
    sslport = config.get("SSLPORT", None)
    if sslport:
        ltc.add_ssl_support(sslport)
    for name, serverlist in config.VHOSTS.items():
        ssl_used = bool(sslport) and os.path.exists("/etc/pycopia/ssl/%s.crt" % (name,))
        ltc.add_vhost(name, serverlist, ssl_used)
    ltc.emit(filelike)

