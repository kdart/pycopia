#!/usr/bin/python
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

# Django BSD licences:
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
A lightweight, but flexible, web application framework.
"""



import sys, os
import sre as re
import sre_parse
from pprint import pformat
import itertools
import traceback

from pycopia import urlparse
from pycopia.inet import httputils
from pycopia.dictlib import ObjectCache

import email, email.Message

# external dependency
import simplejson

STATUSCODES = httputils.STATUSCODES

class Error(Exception):
  "Base framework error"

class InvalidPath(Error):
  """Raised if a URL is requested that can't be met by any registered
  handlers.
  """


class HTTPError(Error):
    pass

ELEMENTCACHE = ObjectCache()

# The following, until end marker:

# Copyright (c) 2005, the Lawrence Journal-World
# All rights reserved.
# from Django project (BSD license).
# Forked so I can separate HTTP functions from the database/ORM parts, and
# customize it (cherry picking the good parts...).
# It's so heavily modified it can hardly be recognized as such.

RESERVED_CHARS="!*'();:@&=+$,/?%#[]"

def parse_file_upload(header_dict, post_data):
    "Returns a tuple of (POST URLQuery, FILES URLQuery)"
    raw_message = '\r\n'.join(['%s:%s' % pair for pair in header_dict.items()])
    raw_message += '\r\n\r\n' + post_data
    msg = email.message_from_string(raw_message)
    POST = urlparse.URLQuery()
    FILES = urlparse.URLQuery()
    for submessage in msg.get_payload():
        if isinstance(submessage, email.Message.Message):
            cd = httputils.get_header(submessage['Content-Disposition'])

            if cd.parameters.has_key('filename'):
                assert type(submessage.get_payload()) is not list, \
                                   "Nested MIME messages are not supported"
                if not cd.parameters['filename'].strip():
                    continue
                # IE submits the full path, so trim everything but the basename.
                # (We can't use os.path.basename because it expects Linux paths.)
                filename = cd.parameters['filename'][cd.parameters['filename'].rfind("\\")+1:]
                FILES.appendlist(cd.parameters['name'], {
                    'filename': filename,
                    'content-type': (submessage.has_key('Content-Type') and submessage['Content-Type'] or None),
                    'content': submessage.get_payload(),
                })
            else:
                POST.appendlist(cd.parameters['name'], submessage.get_payload())
    return POST, FILES


class HttpResponse(object):
    "A basic HTTP response, with content and dictionary-accessed headers"
    status_code = 200
    def __init__(self, content='', mimetype=None):
        self._charset = sys.getdefaultencoding() # XXX
        if not mimetype:
            mimetype = "text/plain; charset=%s" % (self._charset,)
        if hasattr(content, '__iter__'):
            self._container = content
            self._is_string = False
        else:
            self._container = [content]
            self._is_string = True
        self.headers = httputils.Headers()
        self.headers.add_header(httputils.ContentType(mimetype))
        self.cookies = httputils.CookieJar()

    def __str__(self):
        "Full HTTP message, including headers"
        return '\n'.join(['%s: %s' % (key, value)
            for key, value in self.headers.items()]) \
            + '\n\n' + self.content

    def __setitem__(self, header, value):
        self.headers.add_header(header, value)

    def __delitem__(self, header):
        try:
            del self.headers[header]
        except IndexError:
            pass

    def __getitem__(self, header):
        return self.headers[header]

    def add_header(self, header, value=None):
        self.headers.add_header(header, value)

    def set_cookie(self, key, value='', max_age=None, expires=2119102976.0, path='/', 
            domain=None, secure=False):
        self.cookies.add_cookie(key, value, domain=domain, 
            max_age=max_age, path=path, secure=secure, expires=expires)

    def delete_cookie(self, key, path='/', domain=None):
        self.cookies.delete_cookie(key, path, domain)

    def get_response_headers(self):
        self.cookies.get_setcookies(self.headers)
        return self.headers.asWSGI()

    def _get_content(self):
        content = ''.join(self._container)
        if isinstance(content, unicode):
            content = content.encode(self._charset)
        return content

    def _set_content(self, value):
        self._container = [value]
        self._is_string = True

    content = property(_get_content, _set_content)

    def __iter__(self):
        self._iterator = self._container.__iter__()
        return self

    def next(self):
        chunk = self._iterator.next()
        if isinstance(chunk, unicode):
            chunk = chunk.encode(self._charset)
        return chunk

    def close(self):
        if hasattr(self._container, 'close'):
            self._container.close()

    # The remaining methods partially implement the file-like object interface.
    # See http://docs.python.org/lib/bltin-file-objects.html
    def write(self, content):
        if not self._is_string:
            raise Exception, "This %s instance is not writable" % self.__class__
        self._container.append(content)

    def flush(self):
        pass

    def tell(self):
        if not self._is_string:
            raise Exception, "This %s instance cannot tell its position" % self.__class__
        return sum([len(chunk) for chunk in self._container])

class HttpResponseRedirect(HttpResponse):
    status_code = 302
    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = urlparse.quote(redirect_to, safe=RESERVED_CHARS)

class HttpResponsePermanentRedirect(HttpResponse):
    status_code = 301
    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = urlparse.quote(redirect_to, safe=RESERVED_CHARS)

class HttpResponseNotModified(HttpResponse):
    status_code = 304
    def __init__(self):
        HttpResponse.__init__(self)

class HttpResponseNotFound(HttpResponse):
    status_code = 404
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)

class HttpResponseForbidden(HttpResponse):
    status_code = 403
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)

class HttpResponseNotAllowed(HttpResponse):
    status_code = 405
    def __init__(self, permitted_methods):
        HttpResponse.__init__(self)
        self['Allow'] = ', '.join(permitted_methods)

class HttpResponseGone(HttpResponse):
    status_code = 410
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)

class HttpResponseServerError(HttpResponse):
    status_code = 500
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)

def get_host(request):
    "Gets the HTTP host from the environment or request headers."
    host = request.META.get('HTTP_X_FORWARDED_HOST', '')
    if not host:
        host = request.META.get('HTTP_HOST', '')
    return host

def safe_copyfileobj(fsrc, fdst, length=16*1024, size=0):
    """
    A version of shutil.copyfileobj that will not read more than 'size' bytes.
    This makes it safe from clients sending more than CONTENT_LENGTH bytes of
    data in the body.
    """
    if not size:
        return
    while size > 0:
        buf = fsrc.read(min(length, size))
        if not buf:
            break
        fdst.write(buf)
        size -= len(buf)


class HTTPRequest(object):
    def __init__(self, environ):
        self.environ = environ
        self.META = environ
        self.method = environ['REQUEST_METHOD'].upper()
        self.path = environ['PATH_INFO']
        self.get_url = environ["framework.get_url"]

    def __repr__(self):
        # Since this is called as part of error handling, we need to be very
        # robust against potentially malformed input.
        try:
            get = pformat(self.GET)
        except:
            get = '<could not parse>'
        try:
            post = pformat(self.POST)
        except:
            post = '<could not parse>'
        try:
            cookies = pformat(self.COOKIES)
        except:
            cookies = '<could not parse>'
        try:
            meta = pformat(self.META)
        except:
            meta = '<could not parse>'
        return '<HTTPRequest\nGET:%s,\nPOST:%s,\nCOOKIES:%s,\nMETA:%s>' % \
            (get, post, cookies, meta)

    def get_full_path(self):
        qs =self.environ.get('QUERY_STRING')
        if qs:
            return '%s?%s' % (self.path, qs)
        else:
            return self.path

    def is_secure(self):
        return self.environ.get('HTTPS', "off") == "on"

    def _load_post_and_files(self):
        # Populates self._post and self._files
        if self.method == 'POST':
            if self.environ.get('CONTENT_TYPE', '').startswith('multipart'):
                header_dict = dict([(k, v) for k, v in self.environ.items() if k.startswith('HTTP_')])
                header_dict['Content-Type'] = self.environ.get('CONTENT_TYPE', '')
                self._post, self._files = parse_file_upload(header_dict, self.raw_post_data)
            else:
                self._post = urlparse.queryparse(self.raw_post_data)
                self._files = urlparse.URLQuery()
        else:
            self._post = urlparse.URLQuery()
            self._post = urlparse.URLQuery()

    def __getitem__(self, key):
        for d in (self.POST, self.GET):
            try:
                return d[key]
            except KeyError:
                pass
        raise KeyError, "%s not found in either POST or GET" % key

    def has_key(self, key):
        return self.GET.has_key(key) or self.POST.has_key(key)

    def _get_get(self):
        try:
            return self._get
        except AttributeError:
            # The WSGI spec says 'QUERY_STRING' may be absent.
            self._get = urlparse.queryparse(self.environ.get('QUERY_STRING', ''))
            return self._get

    def _get_post(self):
        try:
            return self._post
        except AttributeError:
            self._load_post_and_files()
            return self._post

    def _get_cookies(self):
        try:
            return self._cookies
        except AttributeError:
            self._cookies = httputils.parse_cookie(self.environ.get('HTTP_COOKIE', ''))
            return self._cookies

    def _get_files(self):
        try:
            return self._files
        except AttributeError:
            self._load_post_and_files()
            return self._files

    def _get_raw_post_data(self):
        try:
            return self._raw_post_data
        except AttributeError:
            buf = StringIO()
            try:
                # CONTENT_LENGTH might be absent if POST doesn't have content at all (lighttpd)
                content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            except ValueError: # if CONTENT_LENGTH was empty string or not an integer
                content_length = 0
            safe_copyfileobj(self.environ['wsgi.input'], buf, size=content_length)
            self._raw_post_data = buf.getvalue()
            buf.close()
            return self._raw_post_data

    GET = property(_get_get)
    POST = property(_get_post)
    COOKIES = property(_get_cookies)
    FILES = property(_get_files)
    raw_post_data = property(_get_raw_post_data)


### End (modified) code from Django. ###

# Constant responses.
ONLY_GET = HttpResponseNotAllowed(["GET"])
ONLY_POST = HttpResponseNotAllowed(["POST"])
ONLY_GET_AND_POST = HttpResponseNotAllowed(["GET", "POST"])



class URLMap(object):
    """From regexp to url, and back again. Patterns must use named groups.
    """
    def __init__(self, regexp, method):
        self._method = method
        self._regexp, self._format = _make_url_form(regexp)

    def __str__(self):
        return "%s => %s" % (self._regexp.pattern, self._method.func_name)

    def match(self, string):
        mo = self._regexp.match(string)
        if mo:
            return self._method, mo.groupdict()
        return None, None

    def get_url(self, **kwargs):
        path = self._format % kwargs
        # verify that args are allowed
        mo = self._regexp.match(path)
        if mo:
            return path
        else:
            raise InvalidPath("url args don't match path pattern.")


def _make_url_form(regexp):
    cre = re.compile(regexp, re.I)
    # Build reverse format from re parse tree.
    indexmap = dict([(v,k) for k,v in cre.groupindex.items()])
    collect = []
    for op, val in sre_parse.parse(regexp, re.I):
        if op is sre_parse.LITERAL:
            collect.append(chr(val))
        elif op is sre_parse.SUBPATTERN:
            name = indexmap[val[0]]
            collect.append(r'%%(%s)s' % name)
    return cre, "".join(collect)


class URLAlias(object):
    """Acts as an alias for static locations."""
    def __init__(self, regexp, method):
        self._name = method
        self._regexp, self._format = _make_url_form(regexp)
        self._method = URLRedirector(self._format)

    def __str__(self):
        return "%s => %s" % (self._name, self._method)

    def match(self, string):
        mo = self._regexp.match(string)
        if mo:
            return self._method, mo.groupdict()
        return None, None

    def get_url(self, **kwargs):
        return self._format % kwargs


class URLRedirector(object):
    def __init__(self, loc):
        self._loc = loc
    def __hash__(self):
        return hash(self._loc)
    def __repr__(self):
        return "URLRedirector(%r)" % self._loc
    def __call__(self, request, **kwargs):
        return HttpResponsePermanentRedirect(self._loc % kwargs)


class URLResolver(object):
    """Supports mapping URL paths to handler functions."""
    def __init__(self, mapconfig=None, urlbase=None):
        self._reverse = {}
        self._aliases = {}
        self._patterns = []
        if urlbase:
            self._urlbase = urlbase
        else:
            self._urlbase = ""
        if mapconfig:
            for pattern, methname in mapconfig:
                self.register(pattern, methname)

    def register(self, pattern, method):
        if type(method) is str:
            if method.find(".") >= 0:
                method = get_method(method)
            else:
                self._aliases[method] = URLAlias(pattern, method)
                return
        else:
            assert callable(method), "Must register a callable."
        urlmap = URLMap(pattern, method)
        self._patterns.append(urlmap)
        self._reverse[method] = urlmap

    def unregister(self, method):
        if type(method) is str:
            method = get_method(method)
        try:
            m = self._reverse[method]
        except KeyError:
            return # not registered anyway
        else:
            del self._reverse[method]
            i = 0
            for urlmap in self._patterns:
                if urlmap._method is m:
                    break
                else:
                    i += 1
            del self._patterns[i]

    def match(self, uri):
        for mapper in self._patterns:
            method, kwargs = mapper.match(uri)
            if method:
                return method, kwargs
        return None, None

    def dispatch(self, request):
        path = request.META["PATH_INFO"]
        for mapper in self._patterns:
            method, kwargs = mapper.match(path)
            if method:
                response = method(request, **kwargs)
                if response is None:
                    request.environ['wsgi.errors'].write(
                             "Handler %r returned none.\n" % (method,))
                    raise HTTPError((500, "handler returned None"))
                return response
        else:
            raise HTTPError((404, path))

    def get_url(self, method, **kwargs):
        """Reverse mapping. How do I call method with the given args from
        the URL mapping?
        """
        if type(method) is str:
            if method.find(".") >= 0:
                method = get_method(method)
            else:
                try:
                    urlmap = self._aliases[method]
                except KeyError:
                    raise InvalidPath("Alias not registered")
                return urlmap.get_url(**kwargs)
        try:
            urlmap = self._reverse[method]
        except KeyError:
            raise InvalidPath("Method %r not registered." % (method,))
        return self._urlbase + urlmap.get_url(**kwargs)

    def get_alias(self, name, **kwargs):
        try:
            urlmap = self._aliases[name]
        except KeyError:
            raise InvalidPath("Alias not registered")
        return urlmap.get_url(**kwargs)



class WebApplication(object):
    """Adapt a WSGI server to a framework style request handler. 
    """
    def __init__(self, config):
        self._config = config
        self._resolver = URLResolver(config.LOCATIONMAP, "/%s" % (config.SERVERNAME,))
        #self._cookiejar = httputils.CookieJar()

    def __call__(self, environ, start_response):
        environ['framework.get_url'] = self._resolver.get_url
        environ['framework.get_alias'] = self._resolver.get_alias
        environ['framework.config'] = self._config
        request = HTTPRequest(environ)
        response = self._resolver.dispatch(request)
        status = '%s %s' % (response.status_code, 
                      STATUSCODES.get(response.status_code, 'UNKNOWN STATUS CODE'))
        start_response(status, response.get_response_headers())
        return response



# You can subclass this and set and instance to be called by URL mapping.
class RequestHandler(object):
    METHODS = ["get", "head", "post", "put", "delete", "options", "trace"]
    def __init__(self, _constructor, **kwargs):
        self._methods = {}
        impl = []
        for name in self.METHODS:
            key = name.upper()
            if self.__class__.__dict__.has_key(name):
                impl.append(key)
                self._methods[key] = getattr(self, name)
            else:
                self._methods[key] = self._invalid
        self._implemented = impl
        self._constructor = _constructor
        # optional subclass initializer.
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        pass

    def get_response(self, request, **kwargs):
        return ResponseDocument(request, self._constructor, **kwargs)

    def __call__(self, request, **kwargs):
        meth = self._methods.get(request.method, self._invalid)
        try:
            return meth(request, **kwargs)
        except NotImplementedError:
            return HttpResponseNotAllowed(self._implemented)

    def _invalid(self, request, **kwargs):
        request.environ['wsgi.errors'].write("%r: invalid method: %r\n" % (self, request.method))
        return HttpResponseNotAllowed(self._implemented)

    # Override one or more of these in your handler subclass. Invalid
    # requests are automatically handled.
    def get(self, request, **kwargs):
        raise NotImplementedError

    def post(self, request, **kwargs):
        raise NotImplementedError

    def put(self, request, **kwargs):
        raise NotImplementedError

    def delete(self, request, **kwargs):
        raise NotImplementedError

    def head(self, request, **kwargs):
        raise NotImplementedError

    def options(self, request, **kwargs):
        raise NotImplementedError

    def trace(self, request, **kwargs):
        raise NotImplementedError

# for JSON servers.

class JSONResponse(HttpResponse):
    """Used for asynchronous interfaces needing JSON data returned."""
    def __init__(self, obj):
        json = simplejson.dumps(obj)
        HttpResponse.__init__(self, json, "application/json")


def JSONQuery(request):
    """Convert query term where values are JSON encoded strings."""
    rv = {}
    for key, value in itertools.chain(request.GET.items(), request.POST.items()):
        rv[key] = simplejson.loads(value)
    return rv


def JSON404():
    json = simplejson.dumps(None)
    return HttpResponseNotFound(json, mimetype="application/json")


def JSONServerError(ex, val, tblist):
    json = simplejson.dumps((str(ex), str(val), tblist))
    return HttpResponseServerError(json, mimetype="application/json")


class JSONRequestHandler(RequestHandler):
    """Sub-dispatcher for JSON requests. catches all exceptions and
    returns exception on error as JSON serialized objects (since async
    requests are not viewable on the client side).

    Supply a list of functions to handle. The names of which match the
    "function" field in the URL mapping.

    Your handler functions will get keyword arguments mapped from the
    request query or form. You return any Python primitive objects which
    get sent back to the client.
    """
    def __init__(self, flist, **kwargs):
      self._mapping = mapping = {}
      for func in flist:
          mapping[func.func_name] = func
      super(JSONRequestHandler, self).__init__(None, **kwargs)

    def get(self, request, function):
        try:
            handler = self._mapping[function]
        except KeyError:
            request.environ["wsgi.errors"].write("No JSON handler for %r.\n" % function)
            return JSON404()
        kwargs = JSONQuery(request)
        try:
            return JSONResponse(handler(request, **kwargs))
        except:
            ex, val, tb = sys.exc_info()
            tblist = traceback.extract_tb(tb)
            del tb
            request.environ["wsgi.errors"].write("JSON handler error: %s: %s\n" % (ex, val))
            return JSONServerError(ex, val, tblist)

    post = get # since JSONQuery also converts POST part.

    def get_response(self, request, **kwargs):
        return None # should not be used for JSON handlers.

    def get_url(self, function):
        return "../%s" % function.func_name # XXX assumes name is end of path.


def default_doc_constructor(request, **kwargs):
    from pycopia.WWW import XHTML
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


class ResponseDocument(object):
    """Wraps a text-creator document and supplies helper methods for
    accessing configuration.
    """
    def __init__(self, _request, _constructor=default_doc_constructor, **kwargs):
        self.get_url = _request.environ["framework.get_url"]
        self.get_alias = _request.environ["framework.get_alias"]
        self.config = _request.environ["framework.config"]
        self._doc = doc = _constructor(_request, **kwargs)
        self.NM = self._doc.nodemaker # nodemaker shortcut

    doc = property(lambda s: s._doc)

    def __getattr__(self, key):
        return getattr(self._doc, key)

    def get_object(self, key, ctor, **kwargs):
        return ELEMENTCACHE.get_object(key, ctor, **kwargs)

    def finalize(self):
        doc = self._doc
        self.NM = None
        self.get_url = None
        self.config = None
        self._doc = None
        resp = HttpResponse()
        resp.add_header(httputils.ContentType(doc.MIMETYPE))
        resp.add_header(httputils.CacheControl("no-cache"))
        doc.emit(resp)
        return resp

    def get_icon(self, name):
        try:
            namepair = self.config.ICONMAP[name]
        except KeyError:
            namepair = self.config.ICONMAP["default"]
        return self.NM("Img", {"src": self.get_url("images", name=namepair[1]), 
                       "alt":name, "width":"24", "height":"24"})

    def anchor2(self, path, text, **kwargs):
        return self.NM("A", {"href": self.get_url(path, **kwargs)}, text)



def get_method(name):
    """get a function from a module path."""
    dot = name.rfind(".")
    mod = _get_module(name[:dot])
    return getattr(mod, name[dot+1:])

def _get_module(name):
    try:
        return sys.modules[name]
    except KeyError:
        pass
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod




