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

