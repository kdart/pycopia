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

    def __del__(self):
        self.close()

    def close(self):
        self._chunks = []
        self.length = 0

    #  emit() calls this
    def write(self, data):
        data = data.encode(self.charset)
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

