#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
iSCSI protocol module.

"""

import re
import unicodedata

from pycopia import socket
from pycopia.iscsi import headers
from pycopia.iscsi import constants
from pycopia.iscsi import exceptions

#### functions ##### 

ALLOWED_CHARS = re.compile(u'^[-.:a-z0-9]+$') # charset allowed in iSCSI identifier names.

def normalize_name(uname):
    """Normalize identifier per RFC 3722."""
    # TODO: filter disallowed character blocks and proper IDN mappings.
    assert type(uname) is unicode
    nrm = unicodedata.normalize("NFKC", uname.lower())
    if ALLOWED_CHARS.match(nrm):
        return nrm.encode("utf8")
    else:
        raise exceptions.ValidationError("bad iscsi name: %r" % (uname,))


def get_iqn_name(year, month, hostname, identifier=None):
    """Construct an iSCSI qualified name from components."""
    revdomain = ".".join(reversed(hostname.split(".")))
    name = u"iqn.%04d-%02d.%s" % (year, month, revdomain)
    if identifier:
        name += (u":" + unicode(identifier))
    return normalize_name(name)



class Task(object):
    def __init__(self, id=0):
        self.id = id


class Connection(object):
    """Connection contains associated transactions.
    Assures connection allegiance.
    """
    def __init__(self, sock, targetid):
        self._sock = sock
        self._targetid = targetid

    def close(self):
        sock = self._sock
        self._sock = None
        sock.close()

    def login(self, target):
        pass
# TODO; login sequence


class Session(object):
    """Represents an iSCSI session."""

    def __init__(self, host, target):
        self.host = host
        self.target = target
        self._connections = []
        self.sessionid = (None, None)

    def add_connection(self, port=constants.LISTEN_PORT):
        conn = socket.connect_tcp(self.host, port)
        self._connections.append(Connection(conn, self.target))

    def remove_connection(self):
        try:
            conn = self._connections.pop()
        except IndexError:
            pass
        else:
            conn.close()

    def login(self):
        if not self._connections:
            self.add_connection()
        conn = self._connections[0]
        conn.login()

    def logout(self):
        pass

    def command(self):
        pass



if __name__ == "__main__":
    # Q&D unit tests
    # test normalizing
    ref = 'iqn.2004-01.biz.dartworks.nasmodel:sdc'
    assert normalize_name(u'iqn.2004-01.biz.dartworks.nasmodel:sdc') == ref
    assert normalize_name(u'iqn.2004-01.biz.Dartworks.nasmodel:sdc') == ref
    try:
        normalize_name(u'iqn.2004-01.biz.Dar&works.nasmodel:sdc')
    except exceptions.ValidationError:
        print "OK, caught malformed name."

    # iqn construction
    assert get_iqn_name(2004, 1, 'nasmodel.dartworks.biz', u'sdc') == ref



