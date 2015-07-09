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
Importing this module sets up the Python interpreter to enter a debugger
on an uncaught exception, rather than exiting. If the -O flag is used then
the default bahavior is kept.
"""

import sys

debugger_hook = sys.__excepthook__

if sys.platform == "win32":
    def debugger_hook(exc, value, tb):
        if (not hasattr(sys.stderr, "isatty") or
            not sys.stderr.isatty() or exc in (SyntaxError, IndentationError, KeyboardInterrupt)):
            sys.__excepthook__(exc, value, tb)
        else:
            import pdb
            pdb.post_mortem(tb)
# IronPython
elif sys.platform == "cli":
    def debugger_hook(exc, value, tb):
        if (not hasattr(sys.stderr, "isatty") or
            not sys.stderr.isatty() or exc in (SyntaxError, IndentationError, KeyboardInterrupt)):
            sys.__excepthook__(exc, value, tb)
        else:
            from pycopia.fepy import debugger
            debugger.post_mortem(tb, exc, value)
else:
    def debugger_hook(exc, value, tb):
        if (not hasattr(sys.stderr, "isatty") or
            not sys.stderr.isatty() or exc in (SyntaxError, IndentationError, KeyboardInterrupt)):
            # We don't have a tty-like device, or it was a SyntaxError, so
            # call the default hook.
            sys.__excepthook__(exc, value, tb)
        else:
            from pycopia import debugger
            debugger.post_mortem(tb, exc, value)

sys.excepthook = debugger_hook
