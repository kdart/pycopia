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
Encapsulates all the docutils insanity to provide an easy way to render
small chunks of RST text into XHTML.
"""

import docutils.core
import docutils.io
import docutils.parsers.rst
import docutils.writers.html4css1
import docutils.readers.standalone
import docutils.frontend

class BadVersionError(StandardError):
    pass

def check_version(needed):
    version_info = map(int, docutils.core.__version__.split("."))
    for i in range(2):
        if version_info[i] < needed[i]:
            return False
    return True

class Renderer(object):
    def __init__(self):
        if not check_version((0, 5)):
            raise BadVersionError("Need at least version 0.5 of docutils.")
        self.reader = docutils.readers.standalone.Reader()
        self.writer = docutils.writers.html4css1.Writer()
        self.parser = docutils.parsers.rst.Parser()

        self.dst = docutils.io.StringOutput(encoding="utf-8")

        self.settings = docutils.frontend.OptionParser(
                        (self.reader, self.writer, self.parser),
                     {"link_stylesheet": True, 
                     "stylesheet":None, 
                     "stylesheet_path":None,
                     "traceback": 1,}).get_default_values()

    def render(self, text):
        src = docutils.io.StringInput(text)
        p = docutils.core.Publisher(
           source=src, 
           destination=self.dst,
           source_class=docutils.io.StringInput,
           destination_class=docutils.io.StringOutput,
           reader=self.reader,
           writer=self.writer,
           parser=self.parser,
           settings=self.settings,
       )
        p.publish()
        return p.writer.parts["html_body"]

def get_renderer():
    r = Renderer()
    return r.render


def RSTtoXHTML(rsttext):
    from pycopia.WWW import XHTML
    tempdoc = XHTML.new_document()
    renderer = get_renderer()
    parser = tempdoc.get_parser()
    xhtml = renderer(rsttext)
    parser.feed(xhtml)
    parser.close()
    return tempdoc.root

