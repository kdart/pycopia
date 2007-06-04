#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2007  Keith Dart <keith@kdart.com>
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
Objects for RSS.

"""

from pycopia.XML import POM
from pycopia.dtds import rss2 as DTD

class RSSDocument(POM.POMDocument):
    pass

def new_document():
    return RSSDocument(DTD, "utf-8")

def get_document(url):
    doc = RSSDocument(DTD, "utf-8")
    p = doc.get_parser()
    p.parse(url)
    return doc


