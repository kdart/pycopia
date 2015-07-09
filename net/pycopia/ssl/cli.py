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
CLI wrapper for SSL and CA activities.

TODO

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia.ssl import certs
from pycopia.ssl import operations
from pycopia import CLI


class SSLCommands(CLI.BaseCommands):

    def key(self, argv):
        """key {generate | load | save}
    Create or load and save a private key.  """
        subcmd = argv[1]
        if subcmd.startswith("gen"):
            pass


class ClientCommands(SSLCommands):
    pass


class CACommands(SSLCommands):
    pass


def sslcli(argv):
    b"""sslcli [-?D]
Provides an interactive CLI for managing SSL certificates and CA operations.

Options:
   -?        = This help text.
   -D        = Debug on.
    """
    import os
    import getopt

    try:
        optlist, args = getopt.getopt(argv[1:], b"?hD")
    except getopt.GetoptError:
        print (sslcli.__doc__)
        return
    for opt, val in optlist:
        if opt in (b"-?", b"-h"):
            print (sslcli.__doc__)
            return
        elif opt == b"-D":
            from pycopia import autodebug

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    ui._env[b"PS1"] = b"SSL> "
    cmd = SSLCommands(ui)
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars(b"$HOME/.hist_sslcli"))
    parser.interact()


if __name__ == "__main__":
    import sys
    sslcli(sys.argv)
