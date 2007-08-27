#!/usr/bin/python2.4
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
XML
===

XML related modules.
"""


class XMLError(Exception):
    pass

class ValidationError(XMLError):
    """ValidationError
    This exception is raised when an attempt is made to construct an XML POM
    tree that would be invalid.
    """
    pass


class XMLVisitorContinue(Exception):
    """Signal walk method to bybass children."""
    pass


class XMLPathError(XMLError):
    """Raised when a path method is called and it cannot find the
    referenced path.
    """
