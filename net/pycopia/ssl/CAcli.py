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
CLI wrapper for the pycopia.ssl.CA module.

TODO

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


from pycopia.ssl import CA
from pycopia import CLI


class CACommands(CLI.BaseCommands):
    pass


def cacli(argv):
    """cacli [-?D] <configfile>...
Provides an interactive CLI for managing the certificate authority.

Options:
   -?        = This help text.
   -D        = Debug on.
    """
    import os
    import getopt

    try:
        optlist, args = getopt.getopt(argv[1:], "?D")
    except getopt.GetoptError:
        print (cacli.__doc__)
        return
    for opt, val in optlist:
        if opt == "-?":
            print (cacli.__doc__)
            return
        elif opt == "-D":
            from pycopia import autodebug

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    cmd = CACommands(ui)
    mgr = CA.get_manager()
    cmd._setup(mgr, "%YCA%N> ")
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_cacli"))
    parser.interact()


if __name__ == "__main__":
    import sys
    cacli(sys.argv)
