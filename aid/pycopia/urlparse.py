#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


"""
Extends the standard urlparse module with some extra parsing functions.
Also provides encoding and generating functions.

Parts copied from the standard urlparse module.
"""

import sys
import sre as re

# A classification of schemes ('' means apply by default)
uses_relative = ['ftp', 'http', 'gopher', 'nntp', 'imap',
                               'wais', 'file', 'https', 'shttp', 'mms',
                               'prospero', 'rtsp', 'rtspu', '']
uses_netloc = ['ftp', 'http', 'gopher', 'nntp', 'telnet',
                             'imap', 'wais', 'file', 'mms', 'https', 'shttp',
                             'snews', 'prospero', 'rtsp', 'rtspu', 'rsync', '',
                             'svn', 'svn+ssh']
non_hierarchical = ['gopher', 'hdl', 'mailto', 'news',
                                  'telnet', 'wais', 'imap', 'snews', 'sip']
uses_params = ['ftp', 'hdl', 'prospero', 'http', 'imap',
                             'https', 'shttp', 'rtsp', 'rtspu', 'sip',
                             'mms', '']
uses_query = ['http', 'wais', 'imap', 'https', 'shttp', 'mms',
                            'gopher', 'rtsp', 'rtspu', 'sip', '']
uses_fragment = ['ftp', 'hdl', 'http', 'gopher', 'news',
                               'nntp', 'wais', 'https', 'shttp', 'snews',
                               'file', 'prospero', '']

# Characters valid in scheme names
scheme_chars = ('abcdefghijklmnopqrstuvwxyz'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                '0123456789'
                '+-.')

# Default service ports.
# Using getservbyname is unreliable across hosts (some say port 80 is
# "www")
SERVICES = {
  "ftp": 21,
  "ssh": 22,
  "telnet": 23,
  "smtp": 25,
  "gopher": 70,
  "http": 80,
  "nntp": 119,
  "imap": 143,
  "prospero": 191,
  "wais": 210,
  "https": 443,
  "rtsp": 554,
  "rsync": 873,
  "ftps": 990,
  "imaps": 993,
  "svn": 3690,
}
SERVICES_REVERSE = dict((v,k) for k,v in SERVICES.items())

MAX_CACHE_SIZE = 20
_parse_cache = {}

# End of urlparse module copy.

# from rfc2396 appendix B:
URI_RE_STRICT = r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"
URI_RE_STRICT = re.compile(URI_RE_STRICT)

# But, this is better for finding URL embedded in a string.
URI_RE =  r"((\w+)://){1}" \
          r"([^/?#]*)" \
          r"(/[;/:@&=+$,._%A-Za-z0-9]*)" \
          r"(\?([;/?:@&=+$,-_.!~*'()%A-Za-z0-9]*))?" \
          r"(#(\w*))?"
URI_RE = re.compile(URI_RE)

# char-classes:
# uric        = r";/?:@&=+$,-_.!~*'()A-Za-z0-9%"
# pchar       = r":@&=+$," # | unreserved | escaped
# reserved    = r";/?:@&=+$,"
# unreserved  = alphanum | mark
# mark        = r"-_.!~*'()"
# alphanum    = r"A-Za-z0-9"
# escaped     = r"%A-Fa-f0-9"

def uriparse(uri, strict=False):
    """Given a valid URI, return a 5-tuple of (scheme, authority, path,
    query, fragment). The query part is a URLQuery object, the rest are
    strings.
    Raises ValueError if URI is malformed.
    """
    key = uri, strict
    try:
        scheme, authority, path, q, fragment = _parse_cache[key]
        return (scheme, authority, path, q.copy(), fragment)
    except KeyError:
        pass
    if len(_parse_cache) >= MAX_CACHE_SIZE:
        _parse_cache.clear()
    if strict:
        mo = URI_RE_STRICT.search(uri)
        if mo:
            _, scheme, _, authority, path, _, query, _, fragment = mo.groups()
        else:
            raise ValueError("Invalid URI: %r" % (uri,))
    else:
        mo = URI_RE.search(uri)
        if mo:
            _, scheme, authority, path, _, query, _, fragment = mo.groups()
        else:
            raise ValueError("Invalid URI: %r" % (uri,))
    if query:
        q = queryparse(query)
    else:
        q = URLQuery()
    t = (scheme, authority, path, q, fragment)
    _parse_cache[key] = (scheme, authority, path, q.copy(), fragment)
    return (scheme, authority, path, q, fragment)

urlparse = uriparse

# Return a re.MatchObject (or None) depending on where the string matches
# the URI pattern.
def urimatch(uri, strict=False):
    if strict:
        return URI_RE_STRICT.match(uri)
    else:
        return URI_RE.search(uri)


def serverparse(server):
    """serverparse(serverpart)
    Parses a server part and returns a 4-tuple (user, password, host, port). """
    user = password = host = port = None
    server = server.split("@", 1)
    if len(server) == 2:
        userinfo, hostport = server
        userinfo = userinfo.split(":",1)
        if len(userinfo) == 2:
            user, password = userinfo
        else:
            user = userinfo[0]
        server = server[1]
    else:
        server = server[0]
    server = server.split(":", 1)
    if len(server) == 2:
        host, port = server
    else:
        host = server[0]
    return user, password, host, port

def paramparse(params):
    return params.split(";")


def queryparse(query):
    q = URLQuery()
    parts = query.split("&")
    for part in parts:
        if part:
            try:
                l, r = part.split("=", 1)
            except ValueError:
                l, r = part, ""
            key = unquote_plus(l)
            val = unquote_plus(r)
            q[key] = val
    return q

# URL queries can have names repeated
# This is a dictionary that manages multiple values in a list.
# getting the string value is urlencoded form.
class URLQuery(dict):
    def __init__(self, init=()):
        if isinstance(init, basestring):
            init = queryparse(init)
        dict.__init__(self, init)

    def __str__(self):
        return urlencode(self, 1)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.items())

    # This setitem enforces the "contract" that values are strings or list
    # of strings.
    def __setitem__(self, key, val):
        if key in self:
            kv = dict.__getitem__(self, key)
            if type(kv) is list:
                if type(val) is list:
                    kv.extend(map(str, val))
                else:
                    kv.append(str(val))
            else:
                dict.__setitem__(self, key, [kv, str(val)])
        else:
            if type(val) is list:
                dict.__setitem__(self, key, map(str, val))
            else:
                dict.__setitem__(self, key, str(val))

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        if type(val) is list:
            return val[:]
        else:
            return val # XXX perhaps this should always return a list?

    def __delitem__(self, key):
        val = dict.__getitem__(self, key)
        if type(val) is list:
            del val[-1]
            if not val:
                dict.__delitem__(self, key)
            if len(val) == 1:
                v = val[0]
                dict.__setitem__(self, key, v)
            return
        dict.__delitem__(self, key)

    def getlist(self, key):
        try:
            val = dict.__getitem__(self, key)
        except KeyError:
            return []
        if type(val) is list:
            return val
        else:
            return [val]

    def update(self, other):
        if isinstance(other, basestring):
            other = queryparse(other)
        dict.update(self, other)

    # semi-deep copy since the values here will only be strings, or a list
    # of strings (only). A complete deepcopy implementation is not
    # necessary.
    def copy(self):
        new = self.__class__()
        for k, v in self.iteritems():
            if type(v) is list:
                new[k] = v[:]
            else:
                new[k] = v
        return new


##########################################################################
# copied from urllib module so we don't have to also import all the other
# kruft in there.

# quote and unquote URL strings.

_hextochr = dict(('%02x' % i, chr(i)) for i in range(256))
_hextochr.update(('%02X' % i, chr(i)) for i in range(256))

def unquote(s):
    """unquote('abc%20def') -> 'abc def'."""
    res = s.split('%')
    for i in xrange(1, len(res)):
        item = res[i]
        try:
            res[i] = _hextochr[item[:2]] + item[2:]
        except KeyError:
            res[i] = '%' + item
    return "".join(res)

def unquote_plus(s):
    """unquote('%7e/abc+def') -> '~/abc def'"""
    s = s.replace('+', ' ')
    return unquote(s)

always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
_safemaps = {}

def quote(s, safe = '/'):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted.

    RFC 2396 Uniform Resource Identifiers (URI): Generic Syntax lists
    the following reserved characters.

    reserved    = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
                  "$" | ","

    Each of these characters is reserved in some component of a URL,
    but not necessarily in all of them.

    By default, the quote function is intended for quoting the path
    section of a URL.  Thus, it will not encode '/'.  This character
    is reserved, but in typical usage the quote function is being
    called on a path where the existing slash characters are used as
    reserved characters.
    """
    # per RFC 3986 section 2.5
    if type(s) is unicode:
        s = s.encode("utf8")
    cachekey = (safe, always_safe)
    try:
        safe_map = _safemaps[cachekey]
    except KeyError:
        safe += always_safe
        safe_map = {}
        for i in range(256):
            c = chr(i)
            safe_map[c] = (c in safe) and c or ('%%%02X' % i)
        _safemaps[cachekey] = safe_map
    res = map(safe_map.__getitem__, s)
    return ''.join(res)

def quote_plus(s, safe = ''):
    """Quote the query fragment of a URL; replacing ' ' with '+'"""
    if ' ' in s:
        s = quote(s, safe + ' ')
        return s.replace(' ', '+')
    return quote(s, safe)

def urlencode(query, doseq=0):
    """Encode a sequence of two-element tuples or dictionary into a URL
    query string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError, "not a valid non-string sequence or mapping object", tb

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = quote_plus(str(k))
            v = quote_plus(v)
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = quote_plus(str(k))
            if isinstance(v, basestring):
                if v:
                    v = quote_plus(v)
                    l.append("%s=%s" % (k, v))
                else:
                    l.append(k)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    x = len(v)
                except TypeError:
                    # not a sequence
                    v = quote_plus(v)
                    if v:
                        l.append("%s=%s" % (k, v))
                    else:
                        l.append(k)
                else:
                    # loop over the sequence
                    for elt in v:
                        if elt:
                            l.append(k + '=' + quote_plus(elt))
                        else:
                            l.append(k)
    return '&'.join(l)


class UniversalResourceLocator(object):
    """A general purpose URL object. Parse and generate URLs.
    Provided for read-modify-write operations.
    """
    def __init__(self, url=None, strict=True):
        if url:
            self.set(url, strict)
        else:
            self.clear(strict)

    def clear(self, strict=True):
        self._strict = strict
        self._urlstr = ""
        self._badurl = True
        # URL components
        self._scheme = None
        self._user = self._password = self._host = None
        self._port = 0
        self._path = None
        self._params = []
        self._query = URLQuery()
        self._fragment = None

    def __nonzero__(self):
        return bool(self._scheme) # valid url has scheme.

    def set(self, url, strict=True):
        if isinstance(url, basestring):
            self.clear(strict)
            try:
                self._parse(url, strict)
            except ValueError:
                self.clear(strict)
                raise
            else:
                self._urlstr = url
                self._badurl = False
        elif isinstance(url, self.__class__):
            self._set_from_instance(url)
        else:
            raise ValueError("Invalid initializer: %r" % (url,))

    def _parse(self, url, strict):
        self._scheme, netloc, self._path, self._query, self._fragment = \
                            uriparse(url, strict)
        self._user, self._password, self._host, port = serverparse(netloc)
        if port is not None:
            self._port = int(port)
        else:
            self._port = SERVICES[self._scheme]

    def _set_from_instance(self, other):
        self.__dict__.update(other.__dict__)
        self._params = other._params[:]
        self._query = other._query.copy()
        self._badurl = True

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.__str__(), 
                               self._strict)

    def __str__(self):
        if not self._badurl:
            return self._urlstr
        if self._scheme is None:
            return ""
        s = [self._scheme, "://"]
        if self._host:
            s.append(self._host)
            if self._user:
                if self._password:
                    s.insert(2, "%s:%s" % (self._user, self._password))
                else:
                    s.insert(2, self._user)
                s.insert(3, "@")
            if SERVICES_REVERSE.get(self._port, "") != self._scheme:
                s.append(":")
                s.append(str(self._port))
        if self._path:
            s.append(self._path)
        if self._params:
            s.append(";")
            s.append(";".join(self._params))
        if self._query:
            s.append("?")
            s.append(urlencode(self._query, True))
        if self._fragment:
            s.append("#")
            s.append(self._fragment)
        url = "".join(s)
        self._urlstr = url
        self._badurl = False
        return url

    def __iter__(self):
        return iter(self.__str__())

    def __add__(self, other):
        my_s = self.__str__()
        new_s = my_s + str(other)
        return self.__class__(new_s)

    def __iadd__(self, other):
        my_s = self.__str__()
        new_s = my_s + str(other)
        self.set(new_s, self._strict)
        return self

    def __mod__(self, params):
        new = self.__class__(self)
        new.path = new.path % params # other parts?
        return new

    def copy(self):
        return self.__class__(self)

    def _set_URL(self, url):
        self.set(url, self._strict)

    def set_scheme(self, name):
        self._badurl = True
        self._scheme = name

    def set_user(self, name):
        self._badurl = True
        self._user = name

    def del_user(self):
        if self._user:
            self._badurl = True
            self._user = None

    def set_password(self, name):
        self._badurl = True
        self._password = name

    def del_password(self):
        if self._password:
            self._badurl = True
            self._password = None

    def set_host(self, name):
        self._badurl = True
        self._host = name

    def del_host(self):
        self._badurl = True
        self._host = None

    def set_port(self, name):
        self._badurl = True
        self._port = int(name)

    def del_port(self):
        if self._port:
            self._badurl = True
            self._port = SERVICES[self._scheme] # set to default

    def set_path(self, name):
        self._badurl = True
        self._path = name

    def del_path(self):
        self._badurl = True
        self._path = None

    def get_query(self):
        self._badurl = True # assume you are going to change it.
        return self._query

    def set_query(self, data, update=True):
        self._badurl = True
        if data is None:
            self._query.clear()
        else:
            if update:
                self._query.update(data)
            else:
                self._query = URLQuery(data)

    def del_query(self):
        self._badurl = True
        self._query.clear()

    def set_fragment(self, data):
        self._badurl = True
        self._fragment = str(data)

    def del_fragment(self):
        if self._fragment:
            self._badurl = True
            self._fragment = None

    def set_params(self, params):
        assert type(params) is list
        self._badurl = True
        self._params = params

    def del_params(self):
        if self._params:
            self._badurl = True
            self._params = []

    def get_address(self):
        """Return address suitable for a socket."""
        return (self._host, self._port)

    URL   =    property(__str__, _set_URL, None, 
               "Full URL")
    scheme   = property(lambda s: s._scheme, set_scheme, None, 
               "Scheme part")
    user     = property(lambda s: s._user, set_user, del_user, 
               "User part")
    password = property(lambda s: s._password, set_password, del_password, 
               "Password part")
    host     = property(lambda s: s._host, set_host, del_host, 
               "Host part ")
    port     = property(lambda s: s._port, set_port, del_port, 
               "Port part ")
    path     = property(lambda s: s._path, set_path, del_path, 
               "Path part ")
    params   = property(lambda s: s._params, set_params, del_params, 
               "Params part")
    query    = property(get_query, set_query, del_query, 
               "URLQuery object")
    fragment = property(lambda s: s._fragment, set_fragment, del_fragment, 
               "Fragment part")
    address = property(get_address)



if __name__ == "__main__":
    URL = "http://name:pass@www.host.com:8080/cgi?qr=arg1&qr=arg2&arg3=val3"
    url = UniversalResourceLocator(URL)
    print url.scheme
    print url.user
    print url.password
    print url.host
    print url.port
    print url.path
    print url.params
    print url.query
    print url.fragment
    assert str(url) == URL
    url.scheme = "https"
    url.query["arg4"] = "val4"
    print url
    url2 = UniversalResourceLocator(url)
    print url2


