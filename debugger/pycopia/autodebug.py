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
Importing this module sets up the Python interpreter to enter a debugger
on an uncaught exception, rather than exiting. If the -O flag is used then
the default bahavior is kept.
"""

import sys

if __debug__:
    if sys.platform == "win32":
        def debugger_hook(exc, value, tb):
            if hasattr(sys, 'ps1') or not hasattr(sys.stderr, "isatty") or \
                not sys.stderr.isatty() or exc in (SyntaxError, IndentationError, KeyboardInterrupt):
                sys.__excepthook__(exc, value, tb)
            else:
                import pdb
                pdb.post_mortem(tb)
    else:
        def debugger_hook(exc, value, tb):
            if hasattr(sys, 'ps1') or not hasattr(sys.stderr, "isatty") or \
                not sys.stderr.isatty() or exc in (SyntaxError, IndentationError, KeyboardInterrupt):
                # we are in interactive mode or we don't have a tty-like
                # device, or it was a SyntaxError, so we call the default hook
                sys.__excepthook__(exc, value, tb)
            else:  # we are NOT in interactive mode, print the exception...
                from pycopia import debugger
                # ...then start the debugger in post-mortem mode.
                debugger.post_mortem(tb, exc, value)

    sys.excepthook = debugger_hook

else: # -O mode is "production mode"
    import warnings
    warnings.filterwarnings("ignore")

