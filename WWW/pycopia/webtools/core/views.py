#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 2007  Keith Dart <keith@dartworks.biz>
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
Web tools.

"""

from pycopia.WWW import framework
from pycopia.WWW import XHTML
from pycopia.aid import partial

from pycopia import ezmail


EMAILBODY = """Here is the header information you requested.
"""

def doc_constructor(request, **kwargs):
    doc = XHTML.new_document()
    for name, val in kwargs.items():
        setattr(doc, name, val)
    container = doc.add_section("container")
    header = container.add_section("container", id="header")
    wrapper = container.add_section("container", id="wrapper")
    content = wrapper.add_section("container", id="content")
    navigation = container.add_section("container", id="navigation")
    extra = container.add_section("container", id="extra")
    footer = container.add_section("container", id="footer")
    doc.header = header
    doc.content = content
    doc.nav = navigation
    doc.extra = extra
    doc.footer = footer
    return doc


def renderval(d, NM, key):
    return repr(d[key])

def get_header_table(section, environ):
    d = dict([(k[5:].replace("_", "-").capitalize(), v) for k, v in environ.items() if k.startswith("HTTP")])
    tbl = section.new_table(d.keys(), [partial(renderval, d)], ("HTTP Headers",))
    tbl.width = "100%"


def main(request):
    resp = framework.ResponseDocument(request, doc_constructor, 
                title="Web Tools", 
                stylesheet=request.get_url("css", name="default.css"))
    resp.doc.header.add_header(1, "Web Utilities and Tools")
    resp.doc.nav.append(resp.anchor2(headers, "Request Headers"))
    return resp.finalize()


def headers(request):
    resp = framework.ResponseDocument(request, doc_constructor, title="Request Headers")
    get_header_table(resp.doc, request.META)
    frm = resp.doc.add_form(method="get", action=request.get_url(emailrequest))
    frm.add_textinput("rcpt", "Email")
    frm.add_input(type="submit", value="Send")
    return resp.finalize()



def emailrequest(request):
    """Send HTTP request headers to provided email address."""
    resp = framework.ResponseDocument(request, doc_constructor, title="Web Responder")
    recipients = request.GET.getlist("recipient")+request.GET.getlist("rcpt") or resp.config.ADMINS
    # some basic validation. Mailer shuould validate the rest.
    recipients = filter(lambda name: "@" in name, recipients)
    recipients = filter(lambda name: "." in name, recipients)

    if recipients:
        rpt = XHTML.new_document()
        get_header_table(rpt.body, request.META)

        body = ezmail.AutoMessage(EMAILBODY)
        body["Content-Disposition"] = 'inline'
        msg = ezmail.AutoMessage(str(rpt), mimetype=rpt.MIMETYPE, charset=rpt.encoding)
        msg["Content-Disposition"] = 'attachment; filename=headers.html'
        ezmail.mail([body, msg], To=recipients, 
                  subject="Webtool header request from %s." % (request.META.get("REMOTE_ADDR", "<unknown>"),))

    get_header_table(resp.doc.content, request.META)

    if recipients:
        resp.doc.content.new_para("Header data emailed to %s." % (", ".join(recipients),))
    else:
        resp.doc.content.new_para("No valid email recipients.")
    return resp.finalize()

