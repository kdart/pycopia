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

import sys
import os

import pycopia.inet.XHTMLcgi as CGI

def test(environ=os.environ):
    """Robust test CGI script, usable as main program.

    Write minimal HTTP headers and dump all information provided to
    the script in HTML form.

    """
    print "Content-type: text/html"
    print
    print_head()
    try:
        print_directory()
        print_arguments()
        form = CGI.get_form(sys.stdin) # Replace with other classes to test those
        print_form(form.get_form_values())
        print_environ(environ)
        print_environ_usage()
#        def f():
#            exec "testing print_exception() -- <I>italics?</I>"
#        def g(f=f):
#            f()
#        print "<H3>What follows is a test, not an actual exception:</H3>"
#        g()
    except:
        print_exception()
    print_tail()

def print_head():
    print """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<HTML>
<HEAD>
  <TITLE>cgi test</TITLE>
</HEAD>
<BODY>
"""

def print_tail():
    print """
</BODY>
</HTML>
"""

def print_exception(type=None, value=None, tb=None, limit=None):
    if type is None:
        type, value, tb = sys.exc_info()
    import traceback
    print
    print "<H3>Traceback (most recent call last):</H3>"
    list = traceback.format_tb(tb, limit) + \
           traceback.format_exception_only(type, value)
    print "<PRE>%s<B>%s</B></PRE>" % (
        escape("".join(list[:-1])),
        escape(list[-1]),
        )
    del tb

def print_environ(environ=os.environ):
    """Dump the shell environment as HTML."""
    keys = environ.keys()
    keys.sort()
    print
    print "<H3>Shell Environment:</H3>"
    print "<DL>"
    for key in keys:
        print "<DT>", escape(key), "</DT>"
        print "<DD>", escape(environ[key]), "</DD>"
    print "</DL>"
    print

def print_form(form):
    """Dump the contents of a form as HTML."""
    keys = form.keys()
    keys.sort()
    print
    print "<H3>Form Contents:</H3>"
    if not keys:
        print "<P>No form fields."
    print "<DL>"
    for key in keys:
        print "<DT>", escape(repr(key)), "</DT>"
        value = form[key]
        print "<DD>", escape(repr(value.value)), "</DD>"
    print "</DL>"
    print

def print_directory():
    """Dump the current directory as HTML."""
    print
    print "<H3>Current Working Directory:</H3>"
    try:
        pwd = os.getcwd()
    except os.error, msg:
        print "os.error:", escape(str(msg))
    else:
        print escape(pwd)
    print

def print_arguments():
    print
    print "<H3>Command Line Arguments:</H3>"
    print
    print sys.argv
    print

def print_environ_usage():
    """Dump a list of environment variables used by CGI as HTML."""
    print """
<H3>These environment variables could have been set:</H3>
<UL>
<LI>AUTH_TYPE</LI>
<LI>CONTENT_LENGTH</LI>
<LI>CONTENT_TYPE</LI>
<LI>DATE_GMT</LI>
<LI>DATE_LOCAL</LI>
<LI>DOCUMENT_NAME</LI>
<LI>DOCUMENT_ROOT</LI>
<LI>DOCUMENT_URI</LI>
<LI>GATEWAY_INTERFACE</LI>
<LI>LAST_MODIFIED</LI>
<LI>PATH</LI>
<LI>PATH_INFO</LI>
<LI>PATH_TRANSLATED</LI>
<LI>QUERY_STRING</LI>
<LI>REMOTE_ADDR</LI>
<LI>REMOTE_HOST</LI>
<LI>REMOTE_IDENT</LI>
<LI>REMOTE_USER</LI>
<LI>REQUEST_METHOD</LI>
<LI>SCRIPT_NAME</LI>
<LI>SERVER_NAME</LI>
<LI>SERVER_PORT</LI>
<LI>SERVER_PROTOCOL</LI>
<LI>SERVER_ROOT</LI>
<LI>SERVER_SOFTWARE</LI>
</UL>
In addition, HTTP headers sent by the server may be passed in the
environment as well.  Here are some common variable names:
<UL>
<LI>HTTP_ACCEPT</LI>
<LI>HTTP_CONNECTION</LI>
<LI>HTTP_HOST</LI>
<LI>HTTP_PRAGMA</LI>
<LI>HTTP_REFERER</LI>
<LI>HTTP_USER_AGENT</LI>
</UL>
"""


# Utilities

def escape(s, quote=None):
    """Replace special characters '&', '<' and '>' by SGML entities."""
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
    return s

if __name__ == "__main__":
    test()

