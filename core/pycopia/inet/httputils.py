#!/usr/bin/python2.7
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 1999-  Keith Dart <keith@kdart.com>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


"""
Helpers and utilities for HTTP. Contains a set of classes for constructing and
verifying HTTP headers according to the syntax rules. See RFC 2616.
"""
import base64
import re
import calendar

from pycopia import timelib


# Some useful data!

HTTPMETHODS = [b"GET", b"HEAD", b"POST", b"PUT", b"DELETE", b"OPTIONS", b"TRACE", b"CONNECT"]

STATUSCODES = {
    100: b"Continue",
    101: b"Switching Protocols",
    200: b"OK",
    201: b"Created",
    202: b"Accepted",
    203: b"Non-Authoritative Information",
    204: b"No Content",
    205: b"Reset Content",
    206: b"Partial Content",
    300: b"Multiple Choices",
    301: b"Moved Permanently",
    302: b"Moved Temporarily",
    303: b"See Other",
    304: b"Not Modified",
    305: b"Use Proxy",
    307: b"Temporary Redirect",
    400: b"Bad Request",
    401: b"Unauthorized",
    402: b"Payment Required",
    403: b"Forbidden",
    404: b"Not Found",
    405: b"Method Not Allowed",
    406: b"Not Acceptable",
    407: b"Proxy Authentication Required",
    408: b"Request Time-out",
    409: b"Conflict",
    410: b"Gone",
    411: b"Length Required",
    412: b"Precondition Failed",
    413: b"Request Entity Too Large",
    414: b"Request-URI Too Large",
    415: b"Unsupported Media Type",
    416: b"Requested range not satisfiable",
    417: b"Expectation Failed",
    500: b"Internal Server Error",
    501: b"Not Implemented",
    502: b"Bad Gateway",
    503: b"Service Unavailable",
    504: b"Gateway Time-out",
    505: b"HTTP Version not supported",
 }



class HeaderInvalidError(Exception):
    pass

class ValueInvalidError(HeaderInvalidError):
    pass

class UnknownHeaderError(HeaderInvalidError):
    pass


#### header components. These are various parts of some headers, for general use.
class QuotedString(object):
    """QuotedString(data)
    Represents an HTTP quoted string. Automatically encodes the value.
    """

    def __init__(self, val):
        self.data = val

    def __str__(self):
        return httpquote(str(self.data).encode("ascii"))

    def __repr__(self):
        return b"%s(%r)" % (self.__class__, self.data)

    def parse(self, data):
        self.data = httpunquote(data)


class Comment(object):
    """An http header comment. This is extended a little bit to support semi-colon
    delimited fields. """
    def __init__(self, *items):
        self.data = list(items)
    def __str__(self):
        return b"( %s )" % (b"; ".join([str(o) for o in self.data]))
    def add_item(self, obj):
        self.data.append(obj)


class Product(object):
    """Product(vendor, [version])
    vendor is a vendor string. can contain a version, or not. If not, can
    supply version separately.  version is a version number, as a string."""
    def __init__(self, vendor=b"Mozilla/5.0", version=None):
        vl = vendor.split(b"/")
        if len(vl) == 2:
            self.vendor, self.version = tuple(vl)
        else:
            self.vendor = vendor
            self.version = version

    def __str__(self):
        return b"%s%s" % (self.vendor, (b"/" + self.version if self.version else ""))


class EntityTag(object):
    """Entity tags are used for comparing two or more entities from the same
    requested resource. HTTP/1.1 uses entity tags in the ETag, If-Match,
    If-None-Match, and If-Range header fields.
    """
    def __init__(self, tag, weak=0):
        self.tag = str(tag)
        self.weak = not not weak # force to boolean

    def __str__(self):
        return b'%s"%s"' % (b"W/" if self.weak else b"", self.tag)


class MediaRange(object):
    """MediaRange is an element in an Accept list. Here, a None values means
    ANY. These are essential MIME types."""

    def __init__(self, type=b"*", subtype=b"*", q=1.0, **kwargs):
        self.type = type
        self.subtype = subtype
        assert q >=0 and q <= 1.0
        self.q = q
        self.extensions = kwargs

    def __repr__(self):
        return b"%s(type=%r, subtype=%r, q=%r, **%r)" % (self.__class__.__name__,
            self.type, self.subtype, self.q, self.extensions)

    def __str__(self):
        if self.extensions:
            exts = []
            for extname, extval in self.extensions.items():
                exts.append(b"%s=%s" % (extname, httpquote(extval)))
            extstr = b";%s" % (b";".join(exts))
        else:
            extstr = ""
        if self.q != 1.0:
            return b"%s/%s;q=%1.1f%s" % (self.type, self.subtype, self.q, extstr)
        else:
            return b"%s/%s%s" % (self.type, self.subtype, extstr)

    def parse(self, text):
        if ";" in text:
            text, q = text.split(b";", 1)
            q, v = q.split(b"=")
            if q == b"q":
                self.q = float(v)
            else:
                self.extensions[q] = v
        self.type, self.subtype = text.split(b"/", 1)

    def __cmp__(self, other):
        qcmp = cmp(self.q, other.q)
        if qcmp == 0:
            tcmp = cmp(self.type, other.type)
            if tcmp == 0:
                tcmp = cmp(self.subtype, other.subtype)
                if tcmp == 0:
                    return cmp(self.extensions, other.extensions)
                else:
                    return tcmp
            else:
                return tcmp
        else:
            return qcmp

    def match(self, type, subtype):
        if self.type == b"*":
            return True
        if type == self.type:
            if subtype == b"*":
                return True
            else:
                return subtype == self.subtype
        else:
            return False


class HTTPDate(object):
    """HTTP-date    = rfc1123-date | rfc850-date | asctime-date"""
    def __init__(self, date=None, _value=None):
        if _value is not None:
            self._value = _value # a time tuple
        else:
            if date:
                self.parse(date.strip())
            else:
                self._value = None

    def parse(self, datestring):
        try:
            t = timelib.strptime(datestring, b"%a, %d %b %Y %H:%M:%S GMT") # rfc1123 style
        except ValueError:
            try:
                t = timelib.strptime(datestring, b"%A, %d-%b-%y %H:%M:%S GMT") # rfc850 style
            except ValueError:
                try:
                    t = timelib.strptime(datestring, b"%a %b %d %H:%M:%S %Y") # asctime style
                except ValueError:
                    raise ValueInvalidError(datestring)
        self._value = t

    def __str__(self):
        return timelib.strftime(b"%a, %d %b %Y %H:%M:%S GMT", self._value)

    @classmethod
    def now(cls):
        return cls(_value=timelib.gmtime())

    @classmethod
    def from_float(cls, timeval):
        return cls(_value=timelib.gmtime(timeval))


# Value object for Accept header.
class Media(list):
    def __repr__(self):
        return b"%s(%s)" % (self.__class__.__name__, ",".join([repr(o) for o in self]))


### base class for all header objects

class HTTPHeader(object):
    """HTTPHeader. Abstract base class for all HTTP headers. """
    HEADER = None
    def __init__(self, _value=None, **kwargs):
        self.initialize(**kwargs)
        self._name = self.HEADER
        if _value:
            if isinstance(_value, basestring):
                self.value = self.parse_value(_value)
            else:
                self.value = _value # some object
        else:
            self.value = b""

    def initialize(self, **kwargs):
        """Override this to set the value attribute based on the keyword
        arguments."""
        pass

    def parse_value(self, text):
        return text.lstrip()

    def __str__(self):
        return b"%s: %s" % (self._name, self.value)

    def value_string(self):
        return str(self.value)

    def asWSGI(self):
        return self._name, str(self.value)

    def verify(self):
        if not self.value:
            raise ValueInvalidError("No value")

    def parse(self, line):
        [name, val] = line.split(":", 1)
        self._name = name.strip()
        self.value = self.parse_value(val)

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return b"%s(%r)" % (self.__class__.__name__, self.value)

    def _normalize(self, other):
        if isinstance(other, basestring):
            return other.upper()
        else: # assume other HTTPHeader object.
            return other._name.upper()

    content = property(value_string)

    # Comparison operators compare only the header name.
    def __eq__(self, other):
        return self._name.upper() ==  self._normalize(other)
    def __ne__(self, other):
        return self._name.upper() !=  self._normalize(other)
    def __lt__(self, other):
        return self._name.upper() < self._normalize(other)
    def __gt__(self, other):
        return self._name.upper() > self._normalize(other)
    def __le__(self, other):
        return self._name.upper() <=  self._normalize(other)
    def __ge__(self, other):
        return self._name.upper() >=  self._normalize(other)


class HTTPHeaderWithParameters(HTTPHeader):

    def parse_value(self, text):
        parts = text.encode("ascii").split(b";")
        value = parts.pop(0).strip()
        params = {}
        for part in map(str.strip, parts):
            n, v = part.split(b"=", 1)
            if v.startswith(b'"'):
                params[n] = v[1:-1]
            else:
                params[n] = v
        self.parameters.update(params)
        return value

    def initialize(self, **kwargs):
        self.parameters = kwargs

    def asWSGI(self):
        return self._name, self._val_string()

    def _val_string(self):
        if self.parameters:
            parms = "; ".join([b'%s="%s"' % self._param_to_str(t) for t in self.parameters.iteritems()])
            return b"%s; %s" % (self.value, parms)
        else:
            return str(self.value)

    def _param_to_str(self, paramset):
        return (paramset[0].replace(b"_", b"-"), paramset[1])

    def __str__(self):
        return b"%s: %s" % (self._name, self._val_string())

    def __repr__(self):
        if self.parameters:
            return b"%s(%r, %s)" % (
                self.__class__.__name__, self.value,
                b", ".join([b"%s=%r" % t for t in self.parameters.iteritems()]))
        else:
            return b"%s(%r)" % (self.__class__.__name__, self.value)


### General headers

class CacheControl(HTTPHeaderWithParameters):
    HEADER=b"Cache-Control"


class Connection(HTTPHeader):
    HEADER=b"Connection"


class Date(HTTPHeader):
    HEADER=b"Date"

    def parse_value(self, value):
        return HTTPDate(value)

    @classmethod
    def now(cls):
        return cls(HTTPDate.now())


class Pragma(HTTPHeader):
    HEADER=b"Pragma"


class Trailer(HTTPHeader):
    HEADER=b"Trailer"

class TransferEncoding(HTTPHeaderWithParameters):
    HEADER=b"Transer-Encoding"

    def initialize(self, **kwargs):
        self.parameters = kwargs
        self._tencodings = []

    def _get_value(self):
        return ", ".join(self._tencodings)

    def _set_value(self, value):
        self._tencodings = [t for t in [t.strip() for t in value.split(",")] if t]

    value = property(_get_value, _set_value)

    def set_chunked(self):
        self._tencodings.append(b"chunked")

    def set_identity(self):
        self._tencodings.append(b"identity")

    def set_gzip(self):
        self._tencodings.append(b"gzip")

    def set_compress(self):
        self._tencodings.append(b"compress")

    def set_deflate(self):
        self._tencodings.append(b"deflate")


class Upgrade(HTTPHeader):
    HEADER=b"Upgrade"


class Via(HTTPHeader):
    HEADER=b"Via"


class Warning(HTTPHeader):
    HEADER=b"Warning"


### Entity headers

class Allow(HTTPHeader):
    HEADER=b"Allow"


class ContentEncoding(HTTPHeader):
    HEADER=b"Content-Encoding"


class ContentLanguage(HTTPHeader):
    HEADER=b"Content-Language"


class ContentLength(HTTPHeader):
    HEADER=b"Content-Length"


class ContentLocation(HTTPHeader):
    HEADER=b"Content-Location"


class ContentMD5(HTTPHeader):
    HEADER=b"Content-MD5"


class ContentRange(HTTPHeader):
    HEADER=b"Content-Range"


class ContentDisposition(HTTPHeaderWithParameters):
    HEADER=b"Content-Disposition"


class ContentType(HTTPHeaderWithParameters):
    HEADER=b"Content-Type"


class ETag(HTTPHeader):
    HEADER=b"ETag"


class Expires(HTTPHeader):
    HEADER=b"Expires"


class LastModified(HTTPHeader):
    HEADER=b"Last-Modified"


### Request headers

class Accept(HTTPHeader):
    HEADER=b"Accept"
    def initialize(self, media=None):
        if media:
            v = filter(lambda o: isinstance(o, MediaRange), media)
            if v:
                self.value = v
            else:
                self.value = [MediaRange()]
        else:
            self.value = [MediaRange()]

    def parse_value(self, data):
        rv = Media()
        for part in data.split(b","):
            m = MediaRange()
            m.parse(part.strip())
            rv.append(m)
        rv.sort()
        rv.reverse()
        return rv

    def __str__(self):
        return b"%s: %s" % (self._name, b",".join([str(o) for o in self.value]))

    def __iter__(self):
        return iter(self.value)

    def add_mediarange(self, type, subtype=b"*", q=1.0):
        self.data.append(MediaRange(type, subtype, q))

    # Select from accepted mime types one we support.
    # This isn't currently right, but it's what we support (XHTML)
    # (server is given choice preference)
    def select(self, supported):
        for mymedia in supported:
            for accepted in self.value: # Media ordered in decreasing preference
                maintype, subtype = mymedia.split(b"/", 1)
                if accepted.match(maintype, subtype):
                    return b"%s/%s" % (maintype, subtype)
        return None


class AcceptCharset(HTTPHeader):
    HEADER=b"Accept-Charset"


class AcceptEncoding(HTTPHeader):
    HEADER=b"Accept-Encoding"


class AcceptLanguage(HTTPHeader):
    HEADER=b"Accept-Language"


class Expect(HTTPHeaderWithParameters):
    HEADER=b"Expect"


class From(HTTPHeader):
    HEADER=b"From"


class Host(HTTPHeader):
    HEADER=b"Host"


class IfModifiedSince(HTTPHeader):
    HEADER=b"If-Modified-Since"


class IfMatch(HTTPHeader):
    HEADER=b"If-Match"


class IfNoneMatch(HTTPHeader):
    HEADER=b"If-None-Match"


class IfRange(HTTPHeader):
    HEADER=b"If-Range"


class IfUnmodifiedSince(HTTPHeader):
    HEADER=b"If-Unmodified-Since"


class MaxForwards(HTTPHeader):
    HEADER=b"Max-Forwards"


class ProxyAuthorization(HTTPHeader):
    HEADER=b"Proxy-Authorization"


class Range(HTTPHeader):
    HEADER=b"Range"


class Referer(HTTPHeader):
    HEADER=b"Referer"


class TE(HTTPHeader):
    HEADER=b"TE"


class Authorization(HTTPHeader):
    HEADER = b"Authorization"
    def __str__(self):
        val = self.encode()
        return b"%s: %s" % (self._name, val)

    def __repr__(self):
        return "%s(username=%r, password=%r, auth_scheme=%r)" % (
            self.__class__.__name__, self.username, self.password, self.auth_scheme)

    def initialize(self, username=None, password=None, auth_scheme="basic", token=None):
        self.auth_scheme = auth_scheme
        self.token = token
        self.username = username
        self.password = password
        if username and password:
            self.value = self.encode()

    def parse_value(self, s):
        self.value = s.lstrip()
        auth_scheme, auth_params = tuple(s.split(None, 2))
        self.auth_scheme = auth_scheme.lower()
        if self.auth_scheme == b"basic":
            self.username, self.password = tuple(base64.decodestring(auth_params).split(":"))
        elif self.auth_scheme == b"digest":
            raise NotImplementedError("TODO: digest parsing")
        else:
            self.token = auth_params

    def encode(self):
        if self.auth_scheme == b"basic":
            value = b"Basic " + base64.encodestring(b"%s:%s" % (self.username, self.password))[:-1] # and chop the added newline
        elif self.auth_scheme == b"digest":
            raise NotImplementedError("TODO: digest encoding")
        else:
            value = b"%s %s" % (self.auth_scheme, self.token)
        return value


# see: <http://www.mozilla.org/build/revised-user-agent-strings.html>
class UserAgent(HTTPHeader):
    """see: <http://www.mozilla.org/build/revised-user-agent-strings.html>
    default value: "Mozilla/5.0 (X11; U; Linux i686; en-US)"
    """
    HEADER = b"User-Agent"
    def initialize(self, product=None, comment=None):
        self.data = []
        if product:
            self.data.append(Product(product))
        if comment:
            self.data.append(Comment(comment))
    def __str__(self):
        if not self.value:
            return b"%s: %s" % (self._name, b" ".join([str(o) for o in filter(None, self.data)]))
        else:
            return b"%s: %s" % (self._name, self.value)
    def append(self, obj):
        self.data.append(obj)
    def add_product(self, vendor, version=None):
        self.data.append(Product(vendor, version))
    def add_comment(self, *args):
        self.data.append(Comment(*args))


### Response headers
class AcceptRanges(HTTPHeader):
    HEADER=b"Accept-Ranges"

class Age(HTTPHeader):
    HEADER=b"Age"


class ETag(HTTPHeader):
    HEADER=b"ETag"


class Location(HTTPHeader):
    HEADER=b"Location"


class ProxyAuthenticate(HTTPHeader):
    HEADER=b"Proxy-Authenticate"


class Public(HTTPHeader):
    HEADER=b"Public"


class RetryAfter(HTTPHeader):
    HEADER=b"Retry-After"


class Server(HTTPHeader):
    HEADER=b"Server"


class Vary(HTTPHeader):
    HEADER=b"Vary"


class WWWAuthenticate(HTTPHeader):
    HEADER=b"WWW-Authenticate"

# cookies!  Slightly different impementation from the stock Cookie module.

class SetCookie(HTTPHeaderWithParameters):
    HEADER = b"Set-Cookie"

    def parse_value(self, text):
        return parse_setcookie(text)

    def __str__(self):
        return b"%s: %s" % (self._name, self.value.get_setstring())

    def asWSGI(self):
        return (self._name, self.value.get_setstring())


class SetCookie2(HTTPHeaderWithParameters):
    HEADER = b"Set-Cookie2"

    def parse_value(self, text):
        return parse_setcookie(text)

    def __str__(self):
        return b"%s: %s" % (self._name, self.value.get_setstring())

    def asWSGI(self):
        return (self._name, self.value.get_setstring())


class Cookie(HTTPHeader):
    """A Cookie class. This actually holds a collection of RawCookies."""
    HEADER = b"Cookie"

    def __str__(self):
        return b"%s: %s" % (self._name, self.value_string())

    def value_string(self):
        return b"; ".join([str(o) for o in self.value])

    def asWSGI(self):
        return self._name, self.value_string()


## cookie handling

class CookieJar(object):
    """A collection of cookies. May be used in a client or server context."""
    def __init__(self, filename=None, defaultdomain=None):
        self._defaultdomain = defaultdomain
        self._cookies = {}
        if filename:
            self.from_file(filename)
        self._deleted = []

    def from_file(self, filename):
        text = open(filename).read()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            self.parse_mozilla_line(line)

    def add_cookie(self, name, value, comment=None, domain=None,
            max_age=None, path=None, secure=0, version=1, expires=None, httponly=False):
        if value:
            new = RawCookie(name, value, comment=comment, domain=domain,
                  max_age=max_age, path=path, secure=secure, version=version,
                  expires=expires, httponly=httponly)
            self._cookies[(new.name, new.path, new.domain)] = new
        else:
            self.delete_cookie(name, path, domain)

    def delete_cookie(self, name, path='/', domain=None):
        dom = domain or self._defaultdomain
        try:
            c = self._cookies[(name, path, dom)]
        except KeyError:
            pass
        else:
            del self._cookies[(name, path, dom)]
            c.max_age = 0
            self._deleted.append(c)

    def parse_SetCookie(self, text, url=None):
        c = get_header(text).value
        if url:
            c.domain = url.host[url.host.find("."):]
            if not c.path:
                c.path = url.path
        self._cookies[(c.name, c.path, c.domain)] = c

    def parse_mozilla_line(self, line):
        domain, domain_specified, path, secure, expires, name, value = line.split("\t")
        domain_specified = (domain_specified == b"TRUE")
        secure = (secure == b"TRUE")
        value = value.rstrip()
        new = RawCookie(name, value, domain=domain, expires=expires,
                        path=path, secure=secure)
        self._cookies[(new.name, new.path, new.domain)] = new

    # libcurl can give us one of these lists.
    def parse_mozilla_lines(self, l):
        for line in l:
            self.parse_mozilla_line(line)

    def __str__(self):
        s = []
        for cookie in self._cookies.values():
            s.append(cookie.as_mozilla_line())
        return b"\n".join(s)

    def writeFile(self, fileobject):
        fileobject.write(b"# Netscape HTTP Cookie File\n")
        fileobject.write(b"# http://wp.netscape.com/newsref/std/cookie_spec.html\n\n")
        fileobject.write(self.__str__())
        fileobject.write(b"\n")

    def clear(self):
        self._cookies.clear()

    def get_cookie(self, url):
        cl = self._extract_cookies(url)
        if cl:
            return Cookie(cl)
        else:
            return None

    def get_setcookies(self, headers=None):
        if headers is None:
            headers = Headers()
        for c in self._cookies.values():
            headers.append(SetCookie(c))
        while self._deleted:
            c = self._deleted.pop()
            headers.append(SetCookie(c))
        return headers

    # libcurl likes this format.
    def get_mozilla_list(self, url):
        cl = self._extract_cookies(url)
        return [o.as_mozilla_line() for o in cl]

    def __iter__(self):
        return self._cookies.itervalues()

    def _extract_cookies(self, url):
        rv = []
        desthost = url.host
        path = url.path
        for c in self._cookies.values():
            if desthost.rfind(c.domain) >= 0: # tail match
                if path.find(c.path) >= 0: # path match
                    if c.secure: # secure cookie on secure channel
                        if url.scheme.endswith(b"s"):
                            rv.append(c)
                    else:
                        rv.append(c)
        # most specific first, see: RawCookie.__cmp__
        rv.sort()
        return rv

    cookies = property(lambda s: s._cookies.values())


class RawCookie(object):
    """A single cookie. Merges Netscape and RFC styles. Used for local
    storage of a cookie. Use a CookieJar to store a collection.
    """

    def __init__(self, name, value, comment=None, domain=None,
            max_age=None, path=None, secure=0, version=1, expires=None, httponly=False):
        self.comment = self.domain = self.path = None
        self.name = name.encode("ascii")
        self.value = value.encode("ascii")
        self.set_comment(comment)
        self.set_domain(domain)
        self.set_max_age(max_age)
        self.set_path(path)
        self.set_version(version)
        self.set_secure(secure)
        self.set_httponly(httponly)
        self.set_expires(expires)

    def __repr__(self):
        s = []
        s.append(b"name=%r" % self.name)
        s.append(b"value=%r" % self.value)
        if self.comment:
            s.append(b"comment=%r" % self.comment)
        if self.domain:
            s.append(b"domain=%r" % self.domain)
        if self.max_age:
            s.append(b"max_age=%r" % self.max_age)
        if self.path:
            s.append(b"path=%r" % self.path)
        if self.secure:
            s.append(b"secure=%r" % self.secure)
        if self.version:
            s.append(b"version=%r" % self.version)
        if self.expires is not None:
            s.append(b"expires=%r" % self.expires)
        if self.httponly:
            s.append(b"httponly=True")
        return b"%s(%s)" % (self.__class__.__name__, b", ".join(s))

    def __str__(self):
        if self.value:
            return b'%s=%s' % (self.name, httpquote(self.value))
        else:
            return self.name

    def __cmp__(self, other):
        return cmp(len(other.path), len(self.path))

    def get_setstring(self):
        s = []
        s.append(b"%s=%s" % (self.name, self.value))
        if self.comment:
            s.append(b"Comment=%s" % httpquote(self.comment))
        if self.domain:
            s.append(b"Domain=%s" % httpquote(self.domain))
        if self.max_age is not None:
            s.append(b"Max-Age=%s" % self.max_age)
        if self.path:
            s.append(b"Path=%s" % self.path) # webkit can't deal with quoted path
        if self.secure:
            s.append(b"Secure")
        if self.httponly:
            s.append(b"HttpOnly")
        if self.version:
            s.append(b"Version=%s" % httpquote(str(self.version)))
        if self.expires is not None:
            s.append(b"Expires=%s" % HTTPDate.from_float(self.expires))
        return b";".join(s)

    def as_mozilla_line(self):
        domain_specified = b"TRUE" if self.domain.startswith(b".") else b"FALSE"
        secure = b"TRUE" if self.secure else b"FALSE"
        return b"\t".join([str(o) for o in (self.domain, domain_specified, self.path, secure,
                    self.expires, self.name, self.value)])

    def set_secure(self, val=1):
        """Optional. The Secure attribute (with no value) directs the user
        agent to use only (unspecified) secure means to contact the origin
        server whenever it sends back this cookie."""
        self.secure = bool(val)

    def set_httponly(self, val):
        """Optional. The HttpOnly attribute.  """
        self.httponly = bool(val)

    def set_comment(self, comment):
        """Optional. Because cookies can contain private information about a user,
        the Cookie attribute allows an origin server to document its intended use
        of a cookie. The user can inspect the information to decide whether to
        initiate or continue a session with this cookie."""
        if comment:
            self.comment = comment.encode("ascii")

    def set_domain(self, dom):
        """Optional. The Domain attribute specifies the domain for which the
        cookie is valid. An explicitly specified domain must always start with
        a dot."""
        if dom:
            if dom.count(b".") >= 1:
                self.domain = dom.encode("ascii")
                return
            raise ValueError("Cookie Domain %r must contain a dot" % (dom,))
        else:
            self.domain = b"local"

    def set_max_age(self, ma):
        """Optional. The Max-Age attribute defines the lifetime of the cookie,
        in seconds. The delta-seconds value is a decimal non- negative integer.
        After delta-seconds seconds elapse, the client should discard the
        cookie. A value of zero means the cookie should be discarded
        immediately."""
        try:
            self.max_age = int(ma) # assert maxage is an integer
        except (TypeError, ValueError):
            self.max_age = None

    def set_path(self, path):
        """Optional. The Path attribute specifies the subset of URLs to which
        this cookie applies."""
        if path:
            self.path = path.encode("ascii")

    def set_version(self, ver):
        """Required. The Version attribute, a decimal integer, identifies to
        which version of the state management specification the cookie
        conforms. For this specification, Version=1 applies."""
        self.version = ver

    def set_expires(self, expires):
        try:
            self.expires = float(expires)
        except (TypeError, ValueError):
            self.expires = None

    def set_byname(self, cname, val):
        f = _SETFUNCS.get(cname.lower(), None)
        if f is None:
            raise ValueError("No attribute named %r." % (cname,))
        f(self, val)


# method mapping by name -- must be last
_SETFUNCS = {  b"expires" : RawCookie.set_expires,
               b"path"    : RawCookie.set_path,
               b"comment" : RawCookie.set_comment,
               b"domain"  : RawCookie.set_domain,
               b"max-age" : RawCookie.set_max_age,
               b"secure"  : RawCookie.set_secure,
               b"httponly": RawCookie.set_httponly,
               b"version" : RawCookie.set_version,
               }


def parse_setcookie(rawstr):
    kwargs = {"secure":False}
    parts = rawstr.split(";")
    name, value = parts[0].strip().split(b"=", 1)
    for otherpart in parts[1:]:
        subparts = otherpart.strip().split(b"=", 1)
        try:
            n, v = subparts
        except ValueError:
            if subparts[0] == b"secure":
                kwargs["secure"] = True
            elif subparts[0] == b"HttpOnly":
                kwargs["httponly"] = True
            else:
                raise
        else:
            n = n.strip().lower()
            v = v.strip()
            if n.startswith(b"exp"):
                try:
                    t = timelib.strptime(v, b"%a, %d-%b-%Y %H:%M:%S %Z")
                except ValueError: # might get 2 digit year, so try again.
                    t = timelib.strptime(v, b"%a, %d-%b-%y %H:%M:%S %Z")
                kwargs[n] = calendar.timegm(t)
            else:
                kwargs[n] = v
    return RawCookie(name, value, **kwargs)


# stolen from Cookie module
_LegalCharsPatt  = br"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]"
_CookiePattern = re.compile(
    br"(?x)"                       # This is a Verbose pattern
    br"(?P<key>"                   # Start of group 'key'
    b""+ _LegalCharsPatt +"+?"     # Any word of at least one letter, nongreedy
    br")"                          # End of group 'key'
    br"\s*=\s*"                    # Equal Sign
    br"(?P<val>"                   # Start of group 'val'
    br'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    br"|"                            # or
    b""+ _LegalCharsPatt +"*"        # Any word or empty string
    br")"                          # End of group 'val'
    br"\s*;?"                      # Probably ending in a semi-colon
    )


def parse_cookie(rawstr, patt=_CookiePattern):
    i = 0
    n = len(rawstr)
    newcookie = None
    cookies = []

    while 0 <= i < n:
        # Start looking for a cookie
        match = patt.search(rawstr, i)
        if not match:
            break         # No more cookies

        K,V = match.group(b"key"), match.group(b"val")
        i = match.end(0)
        # Parse the key, value in case it's metainfo
        if K[0] == "$":
            # We ignore attributes which pertain to the cookie
            # mechanism as a whole.  See RFC 2109.
            # (Does anyone care?)
            if newcookie:
                newcookie.set_byname(K[1:], V)
        else:
            newcookie = RawCookie(K, httpunquote(V))
            cookies.append(newcookie)
    return cookies


# Header collecitions

class Headers(list):
    """Holder for a collection of headers. Should only contain HTTPHeader
    objects.
    Optionally initialize with a list of tuples (WSGI style headers).
    """
    def __init__(self, arg=None):
        super(Headers, self).__init__()
        if isinstance(arg, list):
           for name, value in arg:
                self.append(make_header(name, value))

    # returns string with IETF line endings.
    def __str__(self):
        return b"\r\n".join([str(o) for o in self])

    def asWSGI(self):
        """Return list as copy of self with WSGI style tuples as content."""
        return [o.asWSGI() for o in self]

    def asStrings(self):
        """Return list as copy of self with strings as content.
        The curl library likes this."""
        return [str(o) for o in self]

    def __getitem__(self, index):
        if type(index) is int:
            return list.__getitem__(self, index)
        else:
            try:
                i = self.index(index)
            except ValueError:
                raise IndexError("Header %r not found in list." % (index,))
            else:
                return list.__getitem__(self, i)

    def __delitem__(self, index):
        if type(index) is int:
            return list.__delitem__(self, index)
        else:
            try:
                i = self.index(index)
            except ValueError:
                raise IndexError("Header %r not found in list." % (index,))
            else:
                return list.__delitem__(self, i)

    def getall(self, key):
        """Return all occurences of `key` in a list."""
        rv = []
        i = -1
        while 1:
            try:
                i = self.index(key, i + 1)
            except ValueError:
                return rv
            else:
                rv.append(list.__getitem__(self, i))

    def add_header(self, obj, value=None):
        if isinstance(obj, basestring):
            if value is None:
                self.append(get_header(obj)) # a full header string
            else:
                self.append(make_header(obj, value)) # name and value separate.
        elif type(obj) is tuple: # WSGI style header
            self.append(make_header(obj[0], obj[1]))
        elif isinstance(obj, HTTPHeader):
            self.append(obj)
        else:
            raise ValueError("Invalid header: %r" % (obj,))

##### Utility functions

# These quoting routines conform to the RFC2109 specification, which in
# turn references the character definitions from RFC2068.  They provide
# a two-way quoting algorithm.  Any non-text character is translated
# into a 4 character sequence: a forward-slash followed by the
# three-digit octal equivalent of the character.  Any '\' or '"' is
# quoted with a preceeding '\' slash.
#
# These are taken from RFC2068 and RFC2109.
#       _LegalChars       is the list of chars which don't require "'s
#       _Translator       hash-table for fast quoting

_LegalChars = (
  b'abcdefghijklmnopqrstuvwxyz'
  b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  b'0123456789'
  b"!#$%&'*+-.^_`|~")


_Translator       = {
    b'\000' : b'\\000',  b'\001' : b'\\001',  b'\002' : b'\\002',
    b'\003' : b'\\003',  b'\004' : b'\\004',  b'\005' : b'\\005',
    b'\006' : b'\\006',  b'\007' : b'\\007',  b'\010' : b'\\010',
    b'\011' : b'\\011',  b'\012' : b'\\012',  b'\013' : b'\\013',
    b'\014' : b'\\014',  b'\015' : b'\\015',  b'\016' : b'\\016',
    b'\017' : b'\\017',  b'\020' : b'\\020',  b'\021' : b'\\021',
    b'\022' : b'\\022',  b'\023' : b'\\023',  b'\024' : b'\\024',
    b'\025' : b'\\025',  b'\026' : b'\\026',  b'\027' : b'\\027',
    b'\030' : b'\\030',  b'\031' : b'\\031',  b'\032' : b'\\032',
    b'\033' : b'\\033',  b'\034' : b'\\034',  b'\035' : b'\\035',
    b'\036' : b'\\036',  b'\037' : b'\\037',

    b'"' : b'\\"',       b'\\' : b'\\\\',

    b'\177' : b'\\177',  b'\200' : b'\\200',  b'\201' : b'\\201',
    b'\202' : b'\\202',  b'\203' : b'\\203',  b'\204' : b'\\204',
    b'\205' : b'\\205',  b'\206' : b'\\206',  b'\207' : b'\\207',
    b'\210' : b'\\210',  b'\211' : b'\\211',  b'\212' : b'\\212',
    b'\213' : b'\\213',  b'\214' : b'\\214',  b'\215' : b'\\215',
    b'\216' : b'\\216',  b'\217' : b'\\217',  b'\220' : b'\\220',
    b'\221' : b'\\221',  b'\222' : b'\\222',  b'\223' : b'\\223',
    b'\224' : b'\\224',  b'\225' : b'\\225',  b'\226' : b'\\226',
    b'\227' : b'\\227',  b'\230' : b'\\230',  b'\231' : b'\\231',
    b'\232' : b'\\232',  b'\233' : b'\\233',  b'\234' : b'\\234',
    b'\235' : b'\\235',  b'\236' : b'\\236',  b'\237' : b'\\237',
    b'\240' : b'\\240',  b'\241' : b'\\241',  b'\242' : b'\\242',
    b'\243' : b'\\243',  b'\244' : b'\\244',  b'\245' : b'\\245',
    b'\246' : b'\\246',  b'\247' : b'\\247',  b'\250' : b'\\250',
    b'\251' : b'\\251',  b'\252' : b'\\252',  b'\253' : b'\\253',
    b'\254' : b'\\254',  b'\255' : b'\\255',  b'\256' : b'\\256',
    b'\257' : b'\\257',  b'\260' : b'\\260',  b'\261' : b'\\261',
    b'\262' : b'\\262',  b'\263' : b'\\263',  b'\264' : b'\\264',
    b'\265' : b'\\265',  b'\266' : b'\\266',  b'\267' : b'\\267',
    b'\270' : b'\\270',  b'\271' : b'\\271',  b'\272' : b'\\272',
    b'\273' : b'\\273',  b'\274' : b'\\274',  b'\275' : b'\\275',
    b'\276' : b'\\276',  b'\277' : b'\\277',  b'\300' : b'\\300',
    b'\301' : b'\\301',  b'\302' : b'\\302',  b'\303' : b'\\303',
    b'\304' : b'\\304',  b'\305' : b'\\305',  b'\306' : b'\\306',
    b'\307' : b'\\307',  b'\310' : b'\\310',  b'\311' : b'\\311',
    b'\312' : b'\\312',  b'\313' : b'\\313',  b'\314' : b'\\314',
    b'\315' : b'\\315',  b'\316' : b'\\316',  b'\317' : b'\\317',
    b'\320' : b'\\320',  b'\321' : b'\\321',  b'\322' : b'\\322',
    b'\323' : b'\\323',  b'\324' : b'\\324',  b'\325' : b'\\325',
    b'\326' : b'\\326',  b'\327' : b'\\327',  b'\330' : b'\\330',
    b'\331' : b'\\331',  b'\332' : b'\\332',  b'\333' : b'\\333',
    b'\334' : b'\\334',  b'\335' : b'\\335',  b'\336' : b'\\336',
    b'\337' : b'\\337',  b'\340' : b'\\340',  b'\341' : b'\\341',
    b'\342' : b'\\342',  b'\343' : b'\\343',  b'\344' : b'\\344',
    b'\345' : b'\\345',  b'\346' : b'\\346',  b'\347' : b'\\347',
    b'\350' : b'\\350',  b'\351' : b'\\351',  b'\352' : b'\\352',
    b'\353' : b'\\353',  b'\354' : b'\\354',  b'\355' : b'\\355',
    b'\356' : b'\\356',  b'\357' : b'\\357',  b'\360' : b'\\360',
    b'\361' : b'\\361',  b'\362' : b'\\362',  b'\363' : b'\\363',
    b'\364' : b'\\364',  b'\365' : b'\\365',  b'\366' : b'\\366',
    b'\367' : b'\\367',  b'\370' : b'\\370',  b'\371' : b'\\371',
    b'\372' : b'\\372',  b'\373' : b'\\373',  b'\374' : b'\\374',
    b'\375' : b'\\375',  b'\376' : b'\\376',  b'\377' : b'\\377'
    }
_OctalPatt = re.compile(r"\\[0-3][0-7][0-7]")
_QuotePatt = re.compile(r"[\\].")

IDMAP = b''.join(map(chr, range(256)))

def httpquote(s, LegalChars=_LegalChars, idmap=IDMAP):
    #
    # If the string does not need to be double-quoted,
    # then just return the string.  Otherwise, surround
    # the string in doublequotes and precede quote (with a \)
    # special characters.
    #
    if b"" == s.translate(idmap, LegalChars):
        return s
    else:
        return b'"' + b"".join( map(_Translator.get, s, s)) + b'"'

def httpunquote(s):
    # If there aren't any doublequotes,
    # then there can't be any special characters.  See RFC 2109.
    if  len(s) < 2:
        return s
    if s[0] != b'"' or s[-1] != b'"':
        return s
    # We have to assume that we must decode this string.
    # Down to work.
    # Remove the "s
    s = s[1:-1]

    # Check for special sequences.  Examples:
    #   \012 --> \n
    #   \"   --> "
    #
    i = 0
    n = len(s)
    res = []
    while 0 <= i < n:
        Omatch = _OctalPatt.search(s, i)
        Qmatch = _QuotePatt.search(s, i)
        if not Omatch and not Qmatch:             # Neither matched
            res.append(s[i:])
            break
        # else:
        j = k = -1
        if Omatch: j = Omatch.start(0)
        if Qmatch: k = Qmatch.start(0)
        if Qmatch and ( not Omatch or k < j ):   # QuotePatt matched
            res.append(s[i:k])
            res.append(s[k+1])
            i = k+2
        else:                                     # OctalPatt matched
            res.append(s[i:j])
            res.append( chr( int(s[j+1:j+4], 8) ) )
            i = j+4
    return "".join(res)

### end copied code

# some convenient functions

_HEADERMAP = {}
def _init():
    global _HEADERMAP
    for obj in globals().values():
        if type(obj) is type and issubclass(obj, HTTPHeader):
            if obj.HEADER:
                _HEADERMAP[obj.HEADER.upper()] = obj
_init()

def get_header(line):
    """Factory for getting proper header object from text line."""
    if isinstance(line, basestring):
        parts = line.split(":", 1)
        name = parts[0].strip()
        try:
            value = parts[1]
        except IndexError:
            value = ""
        try:
            cls = _HEADERMAP[name.upper()]
            obj = cls(_value=value)
            return obj
        except KeyError:
            obj = HTTPHeader(_value=value)
            obj._name = name
            return obj
    elif isinstance(line, HTTPHeader):
        return line
    else:
        raise ValueError("Need string or HTTPHeader instance, not %r." % (type(line),))


def make_header(name, _value=None, **kwargs):
    try:
        cls = _HEADERMAP[name.encode("ascii").upper()]
        obj = cls(_value, **kwargs)
        return obj
    except KeyError:
        obj = HTTPHeader(_value, **kwargs)
        obj._name = name
        return obj


### form parsing

HTAB   = "\t"
SP     = "\x20"
CRLF   = "\r\n"
WSP    = SP+HTAB
MARKER = CRLF+CRLF

FOLDED   = re.compile(r'%s([%s]+)' % (CRLF, WSP))

def headerlines(bigstring):
    """
    Return list of unfolded header from a chunk of multipart text, and rest of
    text.
    """
    m = bigstring.find(MARKER)
    heads = FOLDED.sub(r"\1", (bigstring[0:m]))
    return heads.split(CRLF), bigstring[m+4:-2]

def get_headers_and_body(text):
    rv = Headers()
    headers, body = headerlines(text)
    for line in headers:
        if ":" not in line:
            continue
        rv.append(get_header(line))
    return rv, body


# self test
if __name__ == "__main__":
    from pycopia import autodebug
    print ("cookies:")
    cookie = RawCookie(name=b"somename", value=b'somevalue&this+plus"quotes"')
    print (cookie)
    print ("----------")
    auth = Authorization(username="myname", password="mypassword")
    print (auth)
    a = Accept(b'Accept: text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5')
    print (a.value)
    print ("---------- ContentType")
    ct = ContentType("text/html", charset="UTF-8")
    print (ct.asWSGI())

    print ("----------")
    setcookie = SetCookie(b'pycopia="somevalue&this+plus%22quotes"; path="/"')
    print (setcookie.asWSGI())
    print (setcookie.asWSGI()[1])
    print (CacheControl(no_cache=b"set-cookie2"))

    cj = CookieJar()
    cj.add_cookie(b"pycopia", b"AESFKAJS", max_age=24, path=b"/")
    print (httpquote(b"/"))
    print (cj.get_setcookies())

    hl = Headers()
    hl.add_header((b"Content-Length", b"222"))
    print(hl)
    h2 = Headers([(b"Content-Length", b"222"), (b"Host", b"www.example.com")])
    print(h2)

    d1 = HTTPDate(b"Sun, 06 Nov 1994 08:49:37 GMT")
    print(d1)
    d2 = HTTPDate(b"Sunday, 06-Nov-94 08:49:37 GMT")
    print(d2)
    d3 = HTTPDate(b"Sun Nov  6 08:49:37 1994")
    print(HTTPDate.now())
    print(Date.now())

    print(TransferEncoding(b"chunked"))
    te = TransferEncoding()
    print(te)
    te.set_gzip()
    print(te)
    te.set_chunked()
    print(te)

