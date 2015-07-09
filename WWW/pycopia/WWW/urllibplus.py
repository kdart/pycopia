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




