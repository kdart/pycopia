#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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

import HTMLParser

class HrefGetter(HTMLParser.HTMLParser):
    def __init__(self, writer):
        HTMLParser.HTMLParser.__init__(self)
        self.current_href = None
        self.adata = ""
        self.state = ""
        if callable(writer):
            self.writer = writer
        else:
            raise ValueError, "HrefGetter: writer must be callable."
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    self.current_href = value
            self.state = "a"
    def handle_data(self, data):
        if self.state == "a":
            self.adata = data
    def handle_endtag(self, tag):
        if tag == "a" and self.state == "a":
            self.writer(self.current_href, self.adata)
            self.state = ""
            self.adata = ""

def default_writer(href, data):
    print href, data

if __name__ == "__main__":
    import sys, xreadlines
    if len(sys.argv) < 2:
        print "%s <htmlfile>" % (sys.argv[0])
        print "emits the hyperlink reference and associated text found in an HTML file."
    hget = HrefGetter(default_writer)
    fo = open(sys.argv[1], "r")
    for line in xreadlines.xreadlines(fo):
        hget.feed(line)
    fo.close()

