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
    import sys
    if len(sys.argv) < 2:
        print "%s <htmlfile>" % (sys.argv[0])
        print "emits the hyperlink reference and associated text found in an HTML file."
    hget = HrefGetter(default_writer)
    fo = open(sys.argv[1], "r")
    for line in fo:
        hget.feed(line)
    fo.close()

