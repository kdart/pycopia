#!/usr/bin/python

"""
rebuilds the pycopia.ISO.iso639a module from the ISO web site.
"""

import os
from pycopia import ISO

FILE = os.path.join(ISO.__path__[0], "iso639a.py")

ISO.build_iso639a(FILE)

# to force compilation and test result
import pycopia.ISO.iso639a
