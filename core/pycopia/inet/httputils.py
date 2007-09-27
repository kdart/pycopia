#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Helpers and utilities for HTTP. Contains a set of classes for constructing HTTP
headers according to the syntax rules. See RFC 2068.

"""

import base64
import re
import calendar

from pycopia import timelib
from pycopia.aid import IF


# Some useful data!

HTTPMETHODS = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]

STATUSCODES = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Moved Temporarily",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Time-out",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out",
    505: "HTTP Version not supported",
 }


# some data for generating other user agents
#
# MozillaComment   ( Platform ;  Security ;  OS-or-CPU ;  
#                   Localization information  ?[; PrereleaseVersion] )  
#                   *[; Optional Other Comments] )

PLATFORMS = ["Windows", "Macintosh", "X11"]
SECURITY = ["U", "I", "N"]
# * N for no security
# * U for strong security (US export)
# * I for weak security (International)
MSWINDOWSLIST = [ "WinNT3.51", "WinNT4.0", "Windows NT 5.0", 
                    "Win95", "Win98", "Win3.11", "Win 9x 4.90", ]
MSIEVERSIONS = ["MSIE 3.0", "MSIE 4.0", "MSIE 5.0", "MSIE 5.01", "MSIE 5.5", "MSIE 6.0",]
# X11 is output of uname -sm
LINUXLIST = ["Linux i686", "Linux i586", "Linux i486", "Linux i386", "Linux ppc"]
SOLARISLIST = ["SunOS sun4u", "SunOS sun4m"]
OSORCPU = {"Windows": MSWINDOWSLIST,
        "Macintosh": ["68k", "PPC"],
        "X11": LINUXLIST + SOLARISLIST,
}


#### header components. These are various parts of some headers, for general use.
class QuotedString(object):
    """QuotedString(data)
    Represents an HTTP quoted string. Automatically encodes the value.
    """

    def __init__(self, val):
        self.data = val
    def __str__(self):
        return httpquote(str(self.data))
    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.data)
    def parse(self, data):
        self.data = httpunquote(data)


class Comment(object):
    """An http header comment. This is extended a little bit to support semi-colon
    delimited fields. """
    def __init__(self, *items):
        self.data = list(items)
    def __str__(self):
        return "( %s )" % ("; ".join(map(str, self.data)))
    def add_item(self, obj):
        self.data.append(obj)


class Product(object):
    """Product(vendor, [version]) 
    vendor is a vendor string. can contain a version, or not. If not, can
    supply version separately.  version is a version number, as a string."""
    def __init__(self, vendor="Mozilla/5.0", version=None):
        vl = vendor.split("/")
        if len(vl) == 2:
            self.vendor, self.version = tuple(vl)
        else:
            self.vendor = vendor
            self.version = version
    def __str__(self):
        return "%s%s" % (self.vendor, IF(self.version, "/%s" % (self.version), ""))


class EntityTag(object):
    """Entity tags are used for comparing two or more entities from the same
    requested resource. HTTP/1.1 uses entity tags in the ETag, If-Match,
    If-None-Match, and If-Range header fields.  """

    def __init__(self, data, weak=0):
        self.data = QuotedString(data)
        self.weak = not not weak # force to boolean
    def __str__(self):
        return "%s%s" % (IF(self.weak, "W/", ""), self.data)

class MediaRange(object):
    """MediaRange is an element in an Accept list. Here, a None values means
    ANY. These are essential MIME types."""

    def __init__(self, type="*", subtype="*", q=1.0, **kwargs):
        self.type = type
        self.subtype = subtype
        assert q >=0 and q <= 1.0
        self.q = q
        self.extensions = kwargs

    def __repr__(self):
        return "%s(type=%r, subtype=%r, q=%r, **%r)" % (self.__class__.__name__, 
            self.type, self.subtype, self.q, self.extensions)

    def __str__(self):
        if self.extensions:
            exts = []
            for extname, extval in self.extensions.items():
                exts.append("%s=%s" % (extname, httpquote(extval)))
            extstr = ";%s" % (";".join(exts))
        else:
            extstr = ""
        if self.q != 1.0: 
            "%s/%s;q=%1.1f%s" % (self.type, self.subtype, self.q, extstr)
        else:
            "%s/%s%s" % (self.type, self.subtype, extstr)

    def parse(self, text):
        if ";" in text:
            text, q = text.split(";", 1)
            q, v = q.split("=")
            if q == "q":
                self.q = float(v)
            else:
                self.extensions[q] = v
        self.type, self.subtype = text.split("/", 1)

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
        if self.type == "*":
            return True
        if type == self.type:
            if subtype == "*":
                return True
            else:
                return subtype == self.subtype
        else:
            return False


# Value object for Accept header.
class Media(list):
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ",".join(map(repr, self)))


### base class for all header objects

class HTTPHeader(object):
    """HTTPHeader. Abstract base class for all HTTP headers. """
    HEADER = None
    def __init__(self, _value=None, **kwargs):
        self._name = self.HEADER
        if _value:
            if type(_value) is str:
                self.value = self.parse_value(_value)
            else:
                self.value = _value # some object
        else:
            self.value = ""
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        """Override this to set the value attribute based on the keyword
        arguments."""
        pass

    def parse_value(self, text):
        return text.lstrip()

    def __str__(self):
        return "%s: %s" % (self._name, self.value)

    def value_string(self):
        return str(self.value)

    def asWSGI(self):
        return self._name, str(self.value)

    def parse(self, line):
        [name, val] = line.split(":", 1)
        self._name = name.strip()
        self.value = self.parse_value(val)

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

    def _normalize(self, other):
        if type(other) is str:
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

### General headers

class CacheControl(HTTPHeader):
    HEADER="Cache-Control"

class Connection(HTTPHeader):
    HEADER="Connection"

class Date(HTTPHeader):
    HEADER="Date"

class Pragma(HTTPHeader):
    HEADER="Pragma"

class TransferEncoding(HTTPHeader):
    HEADER="Transer-Encoding"

class Upgrade(HTTPHeader):
    HEADER="Upgrade"

class Via(HTTPHeader):
    HEADER="Via"


### Entity headers

class Allow(HTTPHeader):
    HEADER="Allow"

class ContentBase(HTTPHeader):
    HEADER="Content-Base"

class ContentEncoding(HTTPHeader):
    HEADER="Content-Encoding"

class ContentLanguage(HTTPHeader):
    HEADER="Content-Language"

class ContentLength(HTTPHeader):
    HEADER="Content-Length"

class ContentLocation(HTTPHeader):
    HEADER="Content-Location"

class ContentMD5(HTTPHeader):
    HEADER="Content-MD5"

class ContentRange(HTTPHeader):
    HEADER="Content-Range"

class ContentType(HTTPHeader):
    HEADER="Content-Type"
    def parse_value(self, text):
        parts = text.split(";")
        value = parts.pop(0).strip().lower()
        self.parameters = dict(map(lambda s: tuple(s.split("=",1)), 
                                        map(str.strip, parts)
                              ))
        return value

    def initialize(self, **kwargs):
        self.parameters = kwargs

    def __str__(self):
        if self.parameters:
            return "%s: %s; %s" % (self._name, self.value, 
                "; ".join(['%s="%s"' % t for t in self.parameters.iteritems()]))
        else:
            return "%s: %s" % (self._name, self.value)

class ETag(HTTPHeader):
    HEADER="ETag"

class Expires(HTTPHeader):
    HEADER="Expires"

class LastModified(HTTPHeader):
    HEADER="Last-Modified"


### Request headers

class Accept(HTTPHeader):
    HEADER="Accept"
    def initialize(self, media=None):
        if media:
            v = filter(lambda o: isinstance(o, MediaRange), media)
            if v:
                self.value = v

    def parse_value(self, data):
        rv = Media()
        for part in data.split(","):
            m = MediaRange()
            m.parse(part)
            rv.append(m)
        rv.sort()
        rv.reverse()
        return rv

    def __str__(self):
        return "%s: %s" % (self._name, ",".join(map(str, self.value)))

    def __iter__(self):
        return iter(self.value)

    def add_mediarange(self, type, subtype="*", q=1.0):
        self.data.append(MediaRange(type, subtype, q))

    # Supply a list of mimetypes that are supported.
    def select(self, mimetypes):
        media = [t.split("/", 1) for t in mimetypes]
        for accepted in self.value: # Media ordered in decreasing preference
            for maintype, subtype in media:
                if accepted.match(maintype, subtype):
                    return "%s/%s" % (maintype, subtype)
        return None


class AcceptCharset(HTTPHeader):
    HEADER="Accept-Charset"

class AcceptEncoding(HTTPHeader):
    HEADER="Accept-Encoding"

class AcceptLanguage(HTTPHeader):
    HEADER="Accept-Language"

class From(HTTPHeader):
    HEADER="From"

class Host(HTTPHeader):
    HEADER="Host"

class IfModifiedSince(HTTPHeader):
    HEADER="If-Modified-Since"

class IfMatch(HTTPHeader):
    HEADER="If-Match"

class IfNoneMatch(HTTPHeader):
    HEADER="If-None-Match"

class IfRange(HTTPHeader):
    HEADER="If-Range"

class IfUnmodifiedSince(HTTPHeader):
    HEADER="If-Unmodified-Since"

class MaxForwards(HTTPHeader):
    HEADER="Max-Forwards"

class ProxyAuthorization(HTTPHeader):
    HEADER="Proxy-Authorization"

class Range(HTTPHeader):
    HEADER="Range"

class Referer(HTTPHeader):
    HEADER="Referer"

class Authorization(HTTPHeader):
    HEADER = "Authorization"
    def __str__(self):
        if self.authtype == "basic":
            val = "Basic " + base64.encodestring("%s:%s" % (self.username, self.password))[:-1] # and chop the added newline
        else:
            raise ValueError, "unkwown authtype: %s" % (self.authtype,)
        return "%s: %s" % (self._name, val)

    def __repr__(self):
        return "%s(username=%r, password=%r, authtype=%r)" % (
            self.__class__.__name__, self.username, self.password, self.authtype)

    def initialize(self, username=None, password=None, authtype="basic"):
        self.authtype = authtype
        self.username = username
        self.password = password

    def parse_value(self, s):
        self.value = s.lstrip()
        authtype, b64part = tuple(s.split(None, 2))
        self.authtype = authtype.lower()
        self.username, self.password = tuple(base64.decodestring(b64part).split(":"))


# see: <http://www.mozilla.org/build/revised-user-agent-strings.html>
class UserAgent(HTTPHeader):
    """see: <http://www.mozilla.org/build/revised-user-agent-strings.html>
    default value: "Mozilla/5.0 (X11; U; Linux i686; en-US)"
    """
    HEADER = "User-Agent"
    def initialize(self, product=None, comment=None):
        self.data = []
        if product:
            self.data.append(Product(product))
        if comment:
            self.data.append(Comment(comment))
    def __str__(self):
        if not self.value:
            return "%s: %s" % (self._name, " ".join(map(str, filter(None, self.data))))
        else:
            return "%s: %s" % (self._name, self.value)
    def append(self, obj):
        self.data.append(obj)
    def add_product(self, vendor, version=None):
        self.data.append(Product(vendor, version))
    def add_comment(self, *args):
        self.data.append(Comment(*args))


### Response headers
class Age(HTTPHeader):
    HEADER="Age"

class Location(HTTPHeader):
    HEADER="Location"

class ProxyAuthenticate(HTTPHeader):
    HEADER="Proxy-Authenticate"

class Public(HTTPHeader):
    HEADER="Public"

class RetryAfter(HTTPHeader):
    HEADER="Retry-After"

class Server(HTTPHeader):
    HEADER="Server"

class Vary(HTTPHeader):
    HEADER="Vary"

class Warning(HTTPHeader):
    HEADER="Warning"

class WWWAuthenticate(HTTPHeader):
    HEADER="WWW-Authenticate"


# cookies!  Slightly different impementation from the stock Cookie module.

class SetCookie(HTTPHeader):
    HEADER = "Set-Cookie"

    def parse_value(self, text):
        return parse_setcookie(text)

    def __str__(self):
        return "%s: %s" % (self._name, self.value.get_setstring())

    def asWSGI(self):
        return (self._name, self.value.get_setstring())


class Cookie(HTTPHeader):
    """A Cookie class. This actually holds a collection of RawCookies."""
    HEADER = "Cookie"

    def __str__(self):
        return "%s: %s" % (self._name, self.value_string())

    def value_string(self):
        return "; ".join(map(str, self.value))

    def asWSGI(self):
        return self._name, self.value_string()



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
            max_age=0, path=None, secure=0, version=0, expires=0.0):
        if value:
            new = RawCookie(name, value, comment=comment, domain=domain, 
                  max_age=max_age, path=path, secure=secure, version=version, 
                  expires=expires)
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
            c.expires = 0.0
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
        domain, domain_specified, path, secure, expires, name, value = \
                        line.split("\t")
        domain_specified = (domain_specified == "TRUE")
        secure = (secure == "TRUE")
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
        return "\n".join(s)

    def writeFile(self, fileobject):
        fileobject.write("# Netscape HTTP Cookie File\n")
        fileobject.write("# http://wp.netscape.com/newsref/std/cookie_spec.html\n\n")
        fileobject.write(self.__str__())
        fileobject.write("\n")

    def clear(self):
        self._cookies.clear()

    def get_cookie(self, url):
        cl = self._extract_cookies(url)
        if cl:
            return Cookie(cl)
        else:
            return None

    def get_setcookies(self, headers=None):
        rv = headers or Headers()
        for c in self._cookies.values():
            rv.append(SetCookie(c))
        while self._deleted:
            c = self._deleted.pop()
            rv.append(SetCookie(c))
        return rv

    # libcurl likes this format.
    def get_mozilla_list(self, url):
        cl = self._extract_cookies(url)
        return map(lambda o: o.as_mozilla_line(), cl)

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
                        if url.scheme.endswith("s"):
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
            max_age=0, path=None, secure=0, version=0, expires=0.0):
        self.comment = self.domain = self.path = None
        self.name = name
        self.value = value
        self.set_comment(comment)
        self.set_domain(domain)
        self.set_max_age(max_age)
        self.set_path(path)
        self.set_version(version)
        self.set_secure(secure)
        self.expires = float(expires)

    def __repr__(self):
        s = []
        s.append("name=%r" % self.name)
        s.append("value=%r" % self.value)
        if self.comment:
            s.append("comment=%r" % self.comment)
        if self.domain:
            s.append("domain=%r" % self.domain)
        if self.max_age:
            s.append("max_age=%r" % self.max_age)
        if self.path:
            s.append("path=%r" % self.path)
        if self.secure:
            s.append("secure=%r" % self.secure)
        if self.version:
            s.append("version=%r" % self.version)
        if self.expires:
            s.append("expires=%r" % self.expires)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(s))

    def __str__(self):
        if self.value:
            return '%s=%s' % (self.name, httpquote(self.value))
        else:
            return self.name

    def __cmp__(self, other):
        return cmp(len(other.path), len(self.path))

    def get_setstring(self):
        s = []
        s.append("%s=%s" % (self.name, self.value))
        if self.comment:
            s.append("comment=%s" % httpquote(self.comment))
        if self.domain:
            s.append("domain=%s" % httpquote(self.domain))
        if self.max_age:
            s.append("max_age=%s" % httpquote(self.max_age))
        if self.path:
            s.append("path=%s" % httpquote(self.path))
        if self.secure:
            s.append("secure")
        if self.version:
            s.append("version=%s" % httpquote(str(self.version)))
        if self.expires:
            s.append("expires=%s" % timelib.strftime(
                 "%a, %d-%b-%Y %H:%M:%S GMT", timelib.gmtime(self.expires)))
        return "; ".join(s)

    def as_mozilla_line(self):
        domain_specified = IF(self.domain.startswith("."), "TRUE", "FALSE")
        secure = IF(self.secure, "TRUE", "FALSE")
        return "\t".join(map(str, [self.domain, domain_specified, 
                      self.path, secure, self.expires, 
                      self.name, self.value]))

    def set_secure(self, val=1):
        """Optional. The Secure attribute (with no value) directs the user
        agent to use only (unspecified) secure means to contact the origin
        server whenever it sends back this cookie."""
        if int(val):
            self.secure = True
        else:
            self.secure = False

    def set_comment(self, comment):
        """Optional. Because cookies can contain private information about a user,
        the Cookie attribute allows an origin server to document its intended use
        of a cookie. The user can inspect the information to decide whether to
        initiate or continue a session with this cookie."""
        self.comment = comment

    def set_domain(self, dom):
        """Optional. The Domain attribute specifies the domain for which the
        cookie is valid. An explicitly specified domain must always start with
        a dot."""
        if dom:
            if dom.count(".") >= 2:
                self.domain = dom
                return
            raise ValueError, "Cookie Domain must contain a dot"
        else:
            self.domain = "local"

    def set_max_age(self, ma):
        """Optional. The Max-Age attribute defines the lifetime of the cookie,
        in seconds. The delta-seconds value is a decimal non- negative integer.
        After delta-seconds seconds elapse, the client should discard the
        cookie. A value of zero means the cookie should be discarded
        immediately."""
        self.max_age = int(ma) # assert maxage is an integer

    def set_path(self, path):
        """Optional. The Path attribute specifies the subset of URLs to which
        this cookie applies."""
        self.path = path

    def set_version(self, ver):
        """Required. The Version attribute, a decimal integer, identifies to
        which version of the state management specification the cookie
        conforms. For this specification, Version=1 applies."""
        self.version = ver

    def set_expires(self, offset):
        self.expires = float(val)

    def set_byname(self, cname, val):
        f = _SETFUNCS.get(cname.lower(), None)
        if f is None:
            raise ValueError, "No attribute named %s." % (cname)
        f(self, val)


# method mapping by name -- must be last
_SETFUNCS = {  "expires" : RawCookie.set_expires,
               "path"    : RawCookie.set_path,
               "comment" : RawCookie.set_comment,
               "domain"  : RawCookie.set_domain,
               "max-age" : RawCookie.set_max_age,
               "secure"  : RawCookie.set_secure,
               "version" : RawCookie.set_version,
               }


def parse_setcookie(rawstr):
    kwargs = {"secure":False}
    parts = rawstr.split(";")
    name, value = parts[0].strip().split("=", 1)
    for otherpart in parts[1:]:
        subparts = otherpart.strip().split("=", 1)
        try:
            n, v = subparts
        except ValueError:
            if subparts[0].startswith("sec"):
                kwargs["secure"] = True
            else:
                raise
        else:
            n = n.strip().lower()
            v = v.strip()
            if n.startswith("exp"):
                try:
                    t = timelib.strptime(v, "%a, %d-%b-%Y %H:%M:%S %Z")
                except ValueError: # might get 2 digit year, so try again.
                    t = timelib.strptime(v, "%a, %d-%b-%y %H:%M:%S %Z")
                kwargs[n] = calendar.timegm(t)
            else:
                kwargs[n] = v
    return RawCookie(name, value, **kwargs)


# stolen from Cookie module
_LegalCharsPatt  = r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]"
_CookiePattern = re.compile(
    r"(?x)"                       # This is a Verbose pattern
    r"(?P<key>"                   # Start of group 'key'
    ""+ _LegalCharsPatt +"+?"     # Any word of at least one letter, nongreedy
    r")"                          # End of group 'key'
    r"\s*=\s*"                    # Equal Sign
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    r"|"                            # or
    ""+ _LegalCharsPatt +"*"        # Any word or empty string
    r")"                          # End of group 'val'
    r"\s*;?"                      # Probably ending in a semi-colon
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

        K,V = match.group("key"), match.group("val")
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


class Headers(list):
    """Holder for a collection of headers. Should only contain HTTPHeader
    objects."""
    # returns string with IETF line endings.
    def __str__(self):
        return "\r\n".join(map(str, self))

    def asWSGI(self):
        """Return list as copy of self with WSGI style tuples as content."""
        return map(lambda o: o.asWSGI(), self)

    def asStrings(self):
        """Return list as copy of self with strings as content.
        The curl library likes this."""
        return map(str, self)

    def __getitem__(self, index):
        if type(index) is int:
            return list.__getitem__(self, index)
        else:
            try:
                i = self.index(index)
            except ValueError:
                raise IndexError, "Header not found in list."
            else:
                return list.__getitem__(self, i)

    def __delitem__(self, index):
        if type(index) is int:
            return list.__delitem__(self, index)
        else:
            try:
                i = self.index(index)
            except ValueError:
                raise IndexError, "Header not found in list."
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
        if type(obj) is str:
            if value is None:
                self.append(get_header(obj)) # a full header string
            else:
                self.append(make_header(obj, value)) # name and value separate.
        elif type(obj) is tuple: # WSGI style header
            self.append(make_header(obj[0], obj[1]))
        elif isinstance(obj, HTTPHeader):
            self.append(obj)
        else:
            raise ValueError, "invalid header"

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

_LegalChars = \
  'abcdefghijklmnopqrstuvwxyz' + \
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + \
  '0123456789' + \
  "!#$%&'*+-.^_`|~"

_Translator       = {
    '\000' : '\\000',  '\001' : '\\001',  '\002' : '\\002',
    '\003' : '\\003',  '\004' : '\\004',  '\005' : '\\005',
    '\006' : '\\006',  '\007' : '\\007',  '\010' : '\\010',
    '\011' : '\\011',  '\012' : '\\012',  '\013' : '\\013',
    '\014' : '\\014',  '\015' : '\\015',  '\016' : '\\016',
    '\017' : '\\017',  '\020' : '\\020',  '\021' : '\\021',
    '\022' : '\\022',  '\023' : '\\023',  '\024' : '\\024',
    '\025' : '\\025',  '\026' : '\\026',  '\027' : '\\027',
    '\030' : '\\030',  '\031' : '\\031',  '\032' : '\\032',
    '\033' : '\\033',  '\034' : '\\034',  '\035' : '\\035',
    '\036' : '\\036',  '\037' : '\\037',

    '"' : '\\"',       '\\' : '\\\\',

    '\177' : '\\177',  '\200' : '\\200',  '\201' : '\\201',
    '\202' : '\\202',  '\203' : '\\203',  '\204' : '\\204',
    '\205' : '\\205',  '\206' : '\\206',  '\207' : '\\207',
    '\210' : '\\210',  '\211' : '\\211',  '\212' : '\\212',
    '\213' : '\\213',  '\214' : '\\214',  '\215' : '\\215',
    '\216' : '\\216',  '\217' : '\\217',  '\220' : '\\220',
    '\221' : '\\221',  '\222' : '\\222',  '\223' : '\\223',
    '\224' : '\\224',  '\225' : '\\225',  '\226' : '\\226',
    '\227' : '\\227',  '\230' : '\\230',  '\231' : '\\231',
    '\232' : '\\232',  '\233' : '\\233',  '\234' : '\\234',
    '\235' : '\\235',  '\236' : '\\236',  '\237' : '\\237',
    '\240' : '\\240',  '\241' : '\\241',  '\242' : '\\242',
    '\243' : '\\243',  '\244' : '\\244',  '\245' : '\\245',
    '\246' : '\\246',  '\247' : '\\247',  '\250' : '\\250',
    '\251' : '\\251',  '\252' : '\\252',  '\253' : '\\253',
    '\254' : '\\254',  '\255' : '\\255',  '\256' : '\\256',
    '\257' : '\\257',  '\260' : '\\260',  '\261' : '\\261',
    '\262' : '\\262',  '\263' : '\\263',  '\264' : '\\264',
    '\265' : '\\265',  '\266' : '\\266',  '\267' : '\\267',
    '\270' : '\\270',  '\271' : '\\271',  '\272' : '\\272',
    '\273' : '\\273',  '\274' : '\\274',  '\275' : '\\275',
    '\276' : '\\276',  '\277' : '\\277',  '\300' : '\\300',
    '\301' : '\\301',  '\302' : '\\302',  '\303' : '\\303',
    '\304' : '\\304',  '\305' : '\\305',  '\306' : '\\306',
    '\307' : '\\307',  '\310' : '\\310',  '\311' : '\\311',
    '\312' : '\\312',  '\313' : '\\313',  '\314' : '\\314',
    '\315' : '\\315',  '\316' : '\\316',  '\317' : '\\317',
    '\320' : '\\320',  '\321' : '\\321',  '\322' : '\\322',
    '\323' : '\\323',  '\324' : '\\324',  '\325' : '\\325',
    '\326' : '\\326',  '\327' : '\\327',  '\330' : '\\330',
    '\331' : '\\331',  '\332' : '\\332',  '\333' : '\\333',
    '\334' : '\\334',  '\335' : '\\335',  '\336' : '\\336',
    '\337' : '\\337',  '\340' : '\\340',  '\341' : '\\341',
    '\342' : '\\342',  '\343' : '\\343',  '\344' : '\\344',
    '\345' : '\\345',  '\346' : '\\346',  '\347' : '\\347',
    '\350' : '\\350',  '\351' : '\\351',  '\352' : '\\352',
    '\353' : '\\353',  '\354' : '\\354',  '\355' : '\\355',
    '\356' : '\\356',  '\357' : '\\357',  '\360' : '\\360',
    '\361' : '\\361',  '\362' : '\\362',  '\363' : '\\363',
    '\364' : '\\364',  '\365' : '\\365',  '\366' : '\\366',
    '\367' : '\\367',  '\370' : '\\370',  '\371' : '\\371',
    '\372' : '\\372',  '\373' : '\\373',  '\374' : '\\374',
    '\375' : '\\375',  '\376' : '\\376',  '\377' : '\\377'
    }
_OctalPatt = re.compile(r"\\[0-3][0-7][0-7]")
_QuotePatt = re.compile(r"[\\].")

IDMAP = str('').join(map(chr, xrange(256)))

def httpquote(s, LegalChars=_LegalChars, idmap=IDMAP):
    #
    # If the string does not need to be double-quoted,
    # then just return the string.  Otherwise, surround
    # the string in doublequotes and precede quote (with a \)
    # special characters.
    #
    if "" == s.translate(idmap, LegalChars):
        return s
    else:
        return '"' + "".join( map(_Translator.get, s, s)) + '"'

def httpunquote(s):
    # If there aren't any doublequotes,
    # then there can't be any special characters.  See RFC 2109.
    if  len(s) < 2:
        return s
    if s[0] != '"' or s[-1] != '"':
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

# end stolen code

# some convenient functions
def mozilla_comment(platform=None, security=None, os=None, localization=None):
    platform = platform or "X11"
    security = security or SECURITY[0]
    os = os or OSORCPU[platform][0]
    localization = localization or "en-US"
    return Comment(platform, security, os, localization)

def microsoft_comment(ieversion=None, os=None):
    ieversion = ieversion or MSIEVERSIONS[4]
    os = os or MSWINDOWSLIST[4]
    return Comment("compatible", ieversion, os)

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
    if isinstance(line, str):
        parts = line.split(":", 1)
        name = parts[0].strip()
        value = parts[1]
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
        raise ValueError("Need string or HTTPHeader instance.")


def make_header(name, _value=None, **kwargs):
    try:
        cls = _HEADERMAP[name.upper()]
        obj = cls(_value, **kwargs)
        return obj
    except KeyError:
        obj = HTTPHeader(_value, **kwargs)
        obj._name = name
        return obj


# self test
if __name__ == "__main__":
    print "cookies:"
    cookie = RawCookie(name="somename", value='somevalue&this+plus"quotes"')
    print cookie
    print "----------"
    auth = Authorization(username="myname", password="mypassword")
    print auth
    a = Accept('Accept: text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5')
    print a.value


