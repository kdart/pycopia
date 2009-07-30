#!/usr/bin/python

"""
rebuilds the ISO.iso3166 module from the ISO web site.
"""

import os
from pycopia import ISO

FILE = os.path.join(ISO.__path__[0], "iso3166.py")

ISO.build_iso3166(FILE)

import pycopia.ISO.iso3166
