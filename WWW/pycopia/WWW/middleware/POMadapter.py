#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
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
Adapt Pycopia XML/XHTML objects to WSGI.

"""

class WSGIAdapter(object):
    """Adapt the emit() method of a POM document to the WSGI spec. It is an
    iterable object that you can return to the WSGI caller. This is also
    the file-like for the document's (or node's) emit() method.
    First, pass this to a document or node's emit() method. Then, return
    it to the WSGI caller.
    Alternatively, use the WSGI write function by passing it to the
    constructor.

    Use it like this:

    def SampleApp(environ, start_response): # use write callabled
      doc = <POMDocument from somewhere>
      response = "200 OK"
      headers = [("Content-Type", doc.MIMETYPE)]
      writer = start_response(response, headers)
      adapter = WSGIAdapter(writer=writer)
      doc.emit(adapter)
      return adapter

    def SampleApp2(environ, start_response): # use iterator
      doc = <POMDocument from somewhere>
      adapter = WSGIAdapter(doc)
      start_response(adapter.response, adapter.headers)
      doc.emit(adapter)
      return adapter

    """
    def __init__(self, doc=None, writer=None):
        if writer:
            self.write = writer # override write method
        self._chunks = []
        self.length = 0
        if doc:
            self.mimetype = doc.MIMETYPE
            self.charset = doc.encoding
        else:
            self.mimetype = None
            self.charset = None

    def __iter__(self):
        return iter(self._chunks)

    def __len__(self):
        return self.length

    def close(self):
        self._chunks = []
        self.length = 0

    #  emit() calls this
    def write(self, data):
        self.length += len(data)
        self._chunks.append(data)

    def get_headers(self):
        if self.length:
            rv = [("Content-Length", str(self.length))]
        else:
            rv = []
        if self.mimetype:
            rv.append(("Content-Type", "%s; charset=%s" % (self.mimetype, self.charset)))
        return rv

    headers = property(get_headers, None, None, "WSGI style header list")


def get_iterator(doc, writer=None, encoding=None):
    """Return an iterable of the content."""
    it = WSGIAdapter(mimetype=doc.MIMETYPE, writer=writer)
    doc.emit(it, encoding)
    return it

