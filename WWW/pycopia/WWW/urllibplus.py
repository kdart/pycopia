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

"""
Wrapper for urllib2.

Provides a new urlopen function that allows specifying a specific
character encoding.

"""


import urllib2

DEFAULT_ACCEPT = "application/xhtml+xml,text/html;q=0.9"
DEFAULT_ENCODING = "utf-8"
DEFAULT_USERAGENT = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.13) Gecko/20060418"


class PlusErrorHandler(urllib2.HTTPDefaultErrorHandler):
    pass

def urlopen(url, data=None, encoding=None, useragent=None, accept=None):
    """Get a URL with a particular character encoding.

    Parameters:
        url:
            The full URL to fetch.
        data:
            A set of data to post. See the docs for urllib2.
        encoding:
            The character encoding to accept. Default to utf-8.

    Returns:
        A file-like object.
    """
    req = urllib2.Request(url, data)
    # just in case server checks browser type.
    req.add_header("User-Agent", useragent or DEFAULT_USERAGENT)
    req.add_header("Accept", accept or DEFAULT_ACCEPT)
    # the charset we want
    req.add_header("Accept-Charset", "%s,*;q=0.7" % (encoding or DEFAULT_ENCODING,))
    return urllib2.urlopen(req)


def get_page(url, data=None, encoding=DEFAULT_ENCODING, useragent=DEFAULT_USERAGENT, 
                accept=DEFAULT_ACCEPT):
    """Get the entire page pointed to by url as a unicode string.

    Parameters:
        url:
            The full URL to fetch.
        data:
            A set of data to post. See the docs for urllib2.
        encoding:
            The character encoding to accept. Default is utf-8.

    """
    fo = urlopen(url, data, encoding, useragent, accept)
    try:
        raw = fo.read()
    finally:
        fo.close()
    return raw




