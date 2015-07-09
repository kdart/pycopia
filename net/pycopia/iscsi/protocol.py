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
iSCSI protocol module.

"""

import re
import unicodedata

from pycopia import socket
from pycopia import asyncio

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


class Connection(socket.AsyncSocket):
    """Connection contains associated transactions.
    Assures connection allegiance.
    """

    def __init__(self, debug=False):
        super(Connection, self).__init__(socket.AF_INET, socket.SOCK_STREAM)


    def __init__(self, sock, session_context):
        self._sock = sock
        self._context = session_context
        self.cid = 0 # connection ID

    def fileno(self):
        return self._sock.fileno()

    def close(self):
        sock = self._sock
        self._sock = None
        sock.close()

    def login(self):
        pdu = headers.LoginPDU()
        pdu.current_stage = SECURITY_NEGOTIATION_STAGE
        pdu.next_stage = OP_PARMS_NEGOTIATION_STAGE
        pdu.ISID = self._context["isid"]
        # add data part
        pdu["SessionType"] = "Normal"
        pdu["AuthMethod"] = "Chap,None"
        pdu["InitiatorName"] = self._context["initiator"]
        pdu["TargetName"] = self._context["target"]
        self._sock.send(pdu.encode())



#     I-> Login (CSG,NSG=0,1 T=0)
#         InitiatorName=iqn.1999-07.com.os:hostid.77
#         TargetName=iqn.1999-07.com.example:diskarray.sn.88
#         AuthMethod=KRB5,CHAP,None
#
#     T-> Login-PR (CSG,NSG=0,0 T=0)
#         AuthMethod=CHAP
#
#     I-> Login (CSG,NSG=0,0 T=0)
#         CHAP_A=<A1,A2>
#
#     T-> Login (CSG,NSG=0,0 T=0)
#         CHAP_A=<A1>
#         CHAP_I=<I>
#         CHAP_C=<C>
#
#     I-> Login (CSG,NSG=0,1 T=1)
#         CHAP_N=<N>
#         CHAP_R=<R>
#
#     If the initiator authentication is successful, the target
#       proceeds:
#
#     T-> Login (CSG,NSG=0,1 T=1)
#
#     I-> Login (CSG,NSG=1,0 T=0)
#         ... iSCSI parameters
#
#     T-> Login (CSG,NSG=1,0 T=0)
#         ... iSCSI parameters
#
#     And at the end:
#
#     I-> Login (CSG,NSG=1,3 T=1)
#         optional iSCSI parameters
#
#     T-> Login (CSG,NSG=1,3 T=1) "login accept"
#




class Session(object):
    """Represents an iSCSI session."""

    def __init__(self, host, target):
        self.host = host
        self._connections = []
        #self.sessionid = (None, None)
        self._context = dict(host=host, target=target, tsih=0,
                isid=headers.ISID(0, 0x023d, 3, 0))

    def add_connection(self, port=constants.LISTEN_PORT):
        sock = Connection(self._context)
        h = asyncio.register(sock)
        self._connections.append(sock)

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
        conn = self._connections[0] # TODO multi-connection
        self.tsih = conn.login()

    def logout(self):
        conn = self._connections[0] # TODO multi-connection
        self.tsih = conn.logout()

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



