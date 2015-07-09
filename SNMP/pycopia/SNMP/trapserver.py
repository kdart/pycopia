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
