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
More featurful trap server.

"""

import ezmail
import SNMP.traps as traps

import storage.Storage as Storage

class PersistentTrapRecord(Storage.Persistent):
    """Persistent holder for SNMP Traps.    """
    def __init__(self, timestamp, ip, community, pdu):
        self.timestamp = timestamp
        self.ip = ip
        self.community = community
        self.pdu = pdu


class TrapRecorder(object):
    """Holds a persistent storage and adds traps to it when called.
    """
    def __init__(self, storage):
        if not storage.has_key("traps"):
            storage.add_container("traps")
            storage.commit()
        self._store = storage["traps"]

    def __call__(self, timestamp, ip, community, pdu):
        tr = PersistentTrapRecord(timestamp, ip, community, pdu)
        self._store[tr.timestamp] = tr
        self._store.commit()
        return False


class TrapMailer(object):
    def __init__(self, storage):
        self._recipients = storage.get("recipients")
        self._from = storage.get("mailfrom")

    def __call__(self, timestamp, ip, community, pdu):
        tr = traps.TrapRecord(timestamp, ip, community, pdu)
        ezmail.mail(str(tr), To=self._recipients, From=self._from,
                    subject="Trap from %r" % (str(ip),))
        return False


def pytrapd(argv):
    """pytrapd [-d]

    Run the Gtest trap daemon. Fork to background if -d is provided.
    """
    import asyncio
    if len(argv) > 1 and argv[1] == "-d":
        import daemonize
        daemonize.daemonize()
    cf = Storage.get_config()

    recorder = TrapRecorder(cf)
    mailer = TrapMailer(cf)

    handlers = [recorder, mailer]
    dispatcher = traps.get_dispatcher(handlers)
    asyncio.poller.loop()


if __name__ == "__main__":
    import sys
    pytrapd(sys.argv)
