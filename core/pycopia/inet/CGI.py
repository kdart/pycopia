#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

"""Support module for CGI (Common Gateway Interface) scripts.

"""

# email.Message
from email.MIMEMultipart import MIMEMultipart
#import email.Errors as Errors
import email.Parser as Parser


class MIMEMultipartForm(MIMEMultipart):
    """Base class for MIME multipart/* type messages."""
    def __init__(self, boundary=None, **_params):
        MIMEMultipart.__init__(self, 'form-data', boundary, **_params)

    def __str__(self):
        return self.as_string(unixfrom=False)

    # payload part methods
    def get_data(self):
        name = self.get_param("name", None, "content-disposition")
        if name is None:
            raise RuntimeError, "disposition not found"
        data = self.get_payload()
        return name, data

    # toplevel methods
    def get_form_values(self):
        """Condenses form data to a dictionary with list values."""
        rv = {}
        for part in self.get_payload():
            name, value = part.get_data()
            if rv.has_key(name):
                rv[name].append(value)
            else:
                rv[name] = [value]
        return rv

     # works with XHTML module widgets
    def get_widget(self, name, widgetclass):
        values = []
        for part in self.get_payload():
            fname, value = part.get_data()
            if name == fname:
                values.append(value)
        w = widgetclass()
        w.initialize(values)
        return w

class FormParser(Parser.Parser):
    def parse(self, fp, headersonly=False):
        root = self._class()
        # fix the lame interface...
        root.set_unixfrom(None)
        #del root["content-type"]
        #del root["mime-version"]
        firstbodyline = self._parseheaders(root, fp)
        if not headersonly:
            self._parsebody(root, fp, firstbodyline)
        return root

#   def _parsebody(self, container, fp, firstbodyline=None):
#       # Parse the body, but first split the payload on the content-type
#       # boundary if present.
#       boundary = container.get_boundary()
#       isdigest = (container.get_content_type() == 'multipart/digest')
#       # If there's a boundary and the message has a main type of
#       # 'multipart', split the payload text into its constituent parts and
#       # parse each separately.  Otherwise, just parse the rest of the body
#       # as a single message.  Note: any exceptions raised in the recursive
#       # parse need to have their line numbers coerced.
#       if container.get_content_maintype() == 'multipart' and boundary:
#           preamble = epilogue = None
#           # Split into subparts.  The first boundary we're looking for won't
#           # always have a leading newline since we're at the start of the
#           # body text, and there's not always a preamble before the first
#           # boundary.
#           separator = '--' + boundary
## XXX
#           payload = read_until_stop(fp, boundary[-15:]+'--')
#           #payload = fp.read()
#           if firstbodyline is not None:
#               payload = firstbodyline + '\n' + payload
#           # We use an RE here because boundaries can have trailing
#           # whitespace.
#           mo = re.search(
#               r'(?P<sep>' + re.escape(separator) + r')(?P<ws>[ \t]*)', payload)
#           if not mo:
#               if self._strict:
#                   raise Errors.BoundaryError(
#                       "Couldn't find starting boundary: %s" % boundary)
#               container.set_payload(payload)
#               return
#           start = mo.start()
#           if start > 0:
#               # there's some pre-MIME boundary preamble
#               preamble = payload[0:start]
#           # Find out what kind of line endings we're using
#           start += len(mo.group('sep')) + len(mo.group('ws'))
#           mo = Parser.NLCRE.search(payload, start)
#           if mo:
#               start += len(mo.group(0))
#           # We create a compiled regexp first because we need to be able to
#           # specify the start position, and the module function doesn't
#           # support this signature. :(
#           cre = re.compile('(?P<sep>\r\n|\r|\n)' +
#                            re.escape(separator) + '--')
#           mo = cre.search(payload, start)
#           if mo:
#               terminator = mo.start()
#               linesep = mo.group('sep')
#               if mo.end() < len(payload):
#                   # There's some post-MIME boundary epilogue
#                   epilogue = payload[mo.end():]
#           elif self._strict:
#               raise Errors.BoundaryError(
#                       "Couldn't find terminating boundary: %s" % boundary)
#           else:
#               # Handle the case of no trailing boundary.  Check that it ends
#               # in a blank line.  Some cases (spamspamspam) don't even have
#               # that!
#               mo = re.search('(?P<sep>\r\n|\r|\n){2}$', payload)
#               if not mo:
#                   mo = re.search('(?P<sep>\r\n|\r|\n)$', payload)
#                   if not mo:
#                       raise Errors.BoundaryError(
#                         'No terminating boundary and no trailing empty line')
#               linesep = mo.group('sep')
#               terminator = len(payload)
#           # We split the textual payload on the boundary separator, which
#           # includes the trailing newline. If the container is a
#           # multipart/digest then the subparts are by default message/rfc822
#           # instead of text/plain.  In that case, they'll have a optional
#           # block of MIME headers, then an empty line followed by the
#           # message headers.
#           parts = re.split(
#               linesep + re.escape(separator) + r'[ \t]*' + linesep,
#               payload[start:terminator])
#           for part in parts:
#               if isdigest:
#                   if part.startswith(linesep):
#                       # There's no header block so create an empty message
#                       # object as the container, and lop off the newline so
#                       # we can parse the sub-subobject
#                       msgobj = self._class()
#                       part = part[len(linesep):]
#                   else:
#                       parthdrs, part = part.split(linesep+linesep, 1)
#                       # msgobj in this case is the "message/rfc822" container
#                       msgobj = self.parsestr(parthdrs, headersonly=1)
#                   # while submsgobj is the message itself
#                   msgobj.set_default_type('message/rfc822')
#                   maintype = msgobj.get_content_maintype()
#                   if maintype in ('message', 'multipart'):
#                       submsgobj = self.parsestr(part)
#                       msgobj.attach(submsgobj)
#                   else:
#                       msgobj.set_payload(part)
#               else:
#                   msgobj = self.parsestr(part)
#               container.preamble = preamble
#               container.epilogue = epilogue
#               container.attach(msgobj)
#       elif container.get_main_type() == 'multipart':
#           # Very bad.  A message is a multipart with no boundary!
#           raise Errors.BoundaryError(
#               'multipart message with no defined boundary')
#       elif container.get_main_type() == 'message':
#           # Create a container for the payload, but watch out for there not
#           # being any headers left
#           try:
#               msg = self.parse(fp)
#           except Errors.HeaderParseError:
#               msg = self._class()
#               self._parsebody(msg, fp)
#           container.attach(msg)
#       else:
#           #text = fp.read()
#           text = fp.readline()
#           if firstbodyline is not None:
#               text = firstbodyline + '\n' + text
#           container.set_payload(text)
#
#
#
#def read_until_stop(fp, stop):
#   lines = []
#   line = fp.readline()
#   while line.find(stop) < 0:
#       lines.append(line)
#       line = fp.readline()
#   else:
#       lines.append(line)
#   payload = "".join(lines)
#   return payload
#

def get_form(fp, strict=False):
    p = FormParser(MIMEMultipartForm, strict=strict)
    return p.parse(fp, False)


if __name__ == "__main__":
    import os
    fname = os.path.expandvars("$HOME/form-data-dump.txt")
    fo = open(fname)
    frm = get_form(fo)
    fo.close() ; del fo
    print frm.get_form_values()

