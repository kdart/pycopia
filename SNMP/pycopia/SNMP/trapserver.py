#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Trap handlers.

"""

from pycopia import basicconfig
from pycopia import ezmail
from pycopia.SNMP import traps


class TrapMailer(object):
    """Trap handler that emails you."""
    def __init__(self, cf):
        self._recipients = cf.get("recipients")
        self._from = cf.get("mailfrom")

    def __call__(self, timestamp, ip, community, pdu):
        tr = traps.TrapRecord(timestamp, ip, community, pdu)
        ezmail.mail(str(tr), To=self._recipients, From=self._from,
                    subject="Trap from %r" % (str(ip),))
        return False


def pytrapd(argv):
    """pytrapd [-d]

    Run a SNMP trap handler and email you on reciept of a trap.
    """
    from pycopia import asyncio
    if len(argv) > 1 and argv[1] == "-d":
        import daemonize
        daemonize.daemonize()
    cf = basicconfig.get_config("trapserver")

    mailer = TrapMailer(cf)

    handlers = [mailer]
    dispatcher = traps.get_dispatcher(handlers)
    asyncio.poller.loop()


if __name__ == "__main__":
    import sys
    pytrapd(sys.argv)
