# python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: Python
"""HTTP/1.1 client library

This is the Pycopia HTTP library. It supports asynchronous sockets. It was forked
from the Python 2.2 standard module (httplib) due to the deep changes required
to support our asynchronous design, extra features, and bug fixes.

HTTPConnection go through a number of "states", which defines when a client
may legally make another request or fetch the response for a particular
request. This diagram details these state transitions:

    (null)
      |
      | HTTPConnection()
      v
    Idle
      |
      | putrequest()
      v
    Request-started
      |
      | ( putheader() )*  endheaders()
      v
    Request-sent
      |
      | response = getresponse()
      v
    Unread-response   [Response-headers-read]
      |\____________________
      |                  |
      | response.read()  | putrequest()
      v                  v
    Idle                  Req-started-unread-response
                     ______/|
                   /        |
   response.read() |        | ( putheader() )*  endheaders()
                   v        v
       Request-started  Req-sent-unread-response
                            |
                            | response.read()
                            v
                          Request-sent

This diagram presents the following rules:
  -- a second request may not be started until {response-headers-read}
  -- a response [object] cannot be retrieved until {request-sent}
  -- there is no differentiation between an unread response body and a
     partially read response body

Note: this enforcement is applied by the HTTPConnection class. The
      HTTPResponse class does not enforce this state machine, which
      implies sophisticated clients may accelerate the request/response
      pipeline. Caution should be taken, though: accelerating the states
      beyond the above pattern may imply knowledge of the server's
      connection-close behavior for certain requests. For example, it
      is impossible to tell whether the server will close the connection
      UNTIL the response headers have been read; this means that further
      requests cannot be placed into the pipeline until it is known that
      the server will NOT be closing the connection.

Logical State                 __state           __response
-------------                 -------           ----------
Idle                           _CS_IDLE        None
Request-started             _CS_REQ_STARTED None
Request-sent                   _CS_REQ_SENT    None
Unread-response             _CS_IDLE           <response_class>
Req-started-unread-response _CS_REQ_STARTED <response_class>
Req-sent-unread-response       _CS_REQ_SENT    <response_class>
"""

import errno

from pycopia import socket
from pycopia.urlparse import uriparse
from pycopia.inet import rfc2822


HTTP_PORT = 80
HTTPS_PORT = 443

_UNKNOWN = 'UNKNOWN'

# connection states
_CS_IDLE = 'Idle'
_CS_REQ_STARTED = 'Request-started'
_CS_REQ_SENT = 'Request-sent'

class HTTPException(Exception):
    pass

class NotConnected(HTTPException):
    pass

class UnknownProtocol(HTTPException):
    pass

class UnknownTransferEncoding(HTTPException):
    pass

class IllegalKeywordArgument(HTTPException):
    pass

class UnimplementedFileMode(HTTPException):
    pass

class IncompleteRead(HTTPException):
    pass

class ImproperConnectionState(HTTPException):
    pass

class CannotSendRequest(ImproperConnectionState):
    pass

class CannotSendHeader(ImproperConnectionState):
    pass

class ResponseNotReady(ImproperConnectionState):
    pass

class BadStatusLine(HTTPException):
    pass

# for backwards compatibility
error = HTTPException


class HTTPResponse(object):
    def __init__(self, sock, debuglevel=0):
        self.fp = sock.makefile('rb', 0)
        self.debuglevel = debuglevel

        self.msg = None

        # from the Status-Line of the response
        self.version = _UNKNOWN # HTTP-Version
        self.status = _UNKNOWN  # Status-Code
        self.reason = _UNKNOWN  # Reason-Phrase

        self.chunked = _UNKNOWN      # is "chunked" being used?
        self.chunk_left = None    # bytes left to read in current chunk
        self._left = ''
        self.length = _UNKNOWN        # number of bytes left in response
        self.will_close = _UNKNOWN    # conn will close at end of response
        # for decoding content encoded messages
        self.cont_decoder = None

    def _parse_statuslist(self, line):
        try:
            [version, status, reason] = line.split(None, 2)
        except ValueError:
            try:
                [version, status] = line.split(None, 1)
                reason = ""
            except ValueError:
                version = "HTTP/0.9"
                status = "200"
                reason = ""
        if version[:5] != 'HTTP/':
            self.close()
            raise BadStatusLine(line)
        # The status code is a three-digit number
        try:
            self.status = status = int(status)
            if status < 100 or status > 999:
                raise BadStatusLine(line)
        except ValueError:
            raise BadStatusLine(line)
        self.reason = reason.strip()

        if version == 'HTTP/1.0':
            self.version = 10
        elif version.startswith('HTTP/1.'):
            self.version = 11   # use HTTP/1.1 code for HTTP/1.x where x>=1
        elif version == 'HTTP/0.9':
            self.version = 9
        else:
            raise UnknownProtocol(version)


    def begin(self):
        if self.msg is not None:
            # we've already started reading the response
            return
        
        line = self.fp.readline().strip()
        if self.debuglevel > 0:
            print "reply:", repr(line)
        self._parse_statuslist(line)
        while self.status == 100: # ignore any Continue status lines
            line = self.fp.readline().strip()
            if self.debuglevel > 0:
                print "reply:", repr(line)
            if not line:
                continue
            self._parse_statuslist(line)

        if self.version == 9:
            raise UnknownProtocol, "version 9 not supported"

        self.msg, self._left = rfc2822.get_headers_dict(self.fp)

        # are we using the chunked-style of transfer encoding?
        tr_enc = self.msg['transfer-encoding']
        if tr_enc:
            if tr_enc.lower() != 'chunked':
                raise UnknownTransferEncoding()
            self.chunked = 1
            self.chunk_left = None
        else:
            self.chunked = 0

        # will the connection close at the end of the response?
        conn = self.msg['connection']
        if conn:
            conn = conn.lower()
            # a "Connection: close" will always close the connection. if we
            # don't see that and this is not HTTP/1.1, then the connection will
            # close unless we see a Keep-Alive header.
            self.will_close = conn.find('close') != -1 or \
                              ( self.version != 11 and \
                                not self.msg['keep-alive'] )
        else:
            # for HTTP/1.1, the connection will always remain open
            # otherwise, it will remain open IFF we see a Keep-Alive header
            self.will_close = self.version != 11 and \
                              not self.msg['keep-alive']

        # do we have a Content-Length?
        # NOTE: RFC 2616, S4.4, #3 says we ignore this if tr_enc is "chunked"
        length = self.msg['content-length']
        if length and not self.chunked:
            try:
                self.length = int(length)
            except ValueError:
                self.length = None
        else:
            self.length = None

        # does the body have a fixed length? (of zero)
        if (self.status == 204 or           # No Content
            self.status == 304 or           # Not Modified
            100 <= self.status < 200):     # 1xx codes
            self.length = 0

        # if the connection remains open, and we aren't using chunked, and
        # a content-length was not provided, then assume that the connection
        # WILL close.
        if not self.will_close and \
           not self.chunked and \
           self.length is None:
            self.will_close = 1
        # content encoded?
        ce = self.msg['content-encoding']
        if ce and ce in ["gzip", "x-gzip"]:
            import x_gzip
            self.fp = x_gzip.GzipFile(self.fp, "r")
            self.length = None # cant use content-length when reading the uncompressed data
#       else:
#           self.cont_decoder = None

    def close(self):
        if self.fp:
            self.fp.close()
            self.fp = None

    def isclosed(self):
        # NOTE: it is possible that we will not ever call self.close(). This
        #      case occurs when will_close is TRUE, length is None, and we
        #      read up to the last byte, but NOT past it.
        #
        # IMPLIES: if will_close is FALSE, then self.close() will ALWAYS be
        #         called, meaning self.isclosed() is meaningful.
        return self.fp is None


#   def read(self, amt=None):
#       if self.cont_decoder:


#       if self.content_encoding in ["gzip", "x-gzip"]:
#           return self._read_gzip(amt)
#       else:
#           return self._read(amt)
#
#   def _read_gzip(self, amt=None):
#       if amt is None:
#           if self.will_close:
#               s = self.fp.read()
#           else:
#               s = self._safe_read(self.length)
#           self.close()
#           # hm, have to read this into a StringIO buffer because socket files cannot seek.
#           sfo = gzip.GzipFile(fileobj=StringIO(s)) 
#           return sfo.read()
#       else: # XXX
#           raise RuntimeError, "reading gzip data with amt not implemented."


#   def _read(self, amt=None):
    def read(self, amt=None):
        if self.fp is None:
            return ''
        if self.chunked:
            chunk_left = self.chunk_left
            #value = ''
            while 1:
                if chunk_left is None:
                    if self._left:
                        line, value = self._left.split("\n", 1)
                        self._left = ''
                    else:
                        line = self.fp.readline()
                        value = ''
                    i = line.find(';')
                    if i >= 0:
                        line = line[:i] # strip chunk-extensions
                    #line = self.fp.readline()
                    #if not line:
                    #   raise EOFError, "EOF while reading"
                    #i = line.find(';')
                    #if i >= 0:
                    #   line = line[:i] # strip chunk-extensions
                    chunk_left = int(line, 16)
                    if chunk_left == 0:
                        break
                if amt is None:
                    value = value + self._safe_read(chunk_left)
                elif amt < chunk_left:
                    value = value + self._safe_read(amt)
                    self.chunk_left = chunk_left - amt
                    return value
                elif amt == chunk_left:
                    value = value + self._safe_read(amt)
                    self._safe_read(2)  # toss the CRLF at the end of the chunk
                    self.chunk_left = None
                    return value
                else:
                    value = value + self._safe_read(chunk_left)
                    amt = amt - chunk_left

                # we read the whole chunk, get another
                self._safe_read(2)    # toss the CRLF at the end of the chunk
                chunk_left = None

            # read and discard trailer up to the CRLF terminator
            ### note: we shouldn't have any trailers!
            while 1:
                line = self.fp.readline()
                if line == '\r\n':
                    break

            # we read everything; close the "file"
            self.close()

            return value

        elif amt is None:
            # unbounded read
            if self.will_close:
                s = self._left + self.fp.read()
            else:
                s = self._left + self._safe_read(self.length-len(self._left))
            self.close()        # we read everything
            return s

        if self.length is not None:
            if amt > self.length:
                # clip the read to the "end of response"
                amt = self.length
            self.length = self.length - amt

        # we do not use _safe_read() here because this may be a .will_close
        # connection, and the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        s = self.fp.read(amt - len(self._left))
        return self._left + s

    def _safe_read(self, amt):
        """Read the number of bytes requested, compensating for partial reads.

        Note that we cannot distinguish between EOF and an interrupt when zero
        bytes have been read. IncompleteRead() will be raised in this
        situation.

        This function should be used when <amt> bytes "should" be present for
        reading. If the bytes are truly not available (due to EOF), then the
        IncompleteRead exception can be used to detect the problem.
        """
        s = ''
        while amt > 0:
            chunk = self.fp.read(amt)
            if not chunk:
                raise IncompleteRead(s)
            s += chunk
            amt -= len(chunk)
        return s

    def _new_safe_read(self, amt):
        return self.fp.read(amt)
#
#       s = ''
#       while amt > 0:
#           chunk = self.fp.read(amt)
#           if not chunk:
#               break
#           s = s + chunk
#           amt = amt - len(chunk)
#       return s

    def getheader(self, name, default=None):
        if self.msg is None:
            raise ResponseNotReady()
        return self.msg.get(name, default)



class HTTPConnection(object):

    _http_vsn = 11
    _http_vsn_str = 'HTTP/1.1'

    response_class = HTTPResponse
    default_port = HTTP_PORT
    auto_open = 1
    debuglevel = 0

    def __init__(self, host, port=None):
        self.sock = None
        self.__response = None
        self.__state = _CS_IDLE

        self._set_hostport(host, port)

    def _set_hostport(self, host, port):
        if port is None:
            i = host.find(':')
            if i >= 0:
                port = int(host[i+1:])
                host = host[:i]
            else:
                port = self.default_port
        self.host = host
        self.port = port

    def set_debuglevel(self, level):
        self.debuglevel = level

    def connect(self):
        """Connect to the host and port specified in __init__."""
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
#               self.sock = asyncio.SocketDispatcher()
#               self.sock.create_socket(af, socktype, proto)
                if self.debuglevel > 0:
                    print "connect: (%s, %s)" % (self.host, self.port)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.debuglevel > 0:
                    print 'connect fail:', (self.host, self.port)
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg

    def close(self):
        """Close the connection to the HTTP server."""
        if self.sock:
            self.sock.close()   # close it manually... there may be other refs
            self.sock = None
        if self.__response:
            self.__response.close()
            self.__response = None
        self.__state = _CS_IDLE

    def send(self, str):
        """Send `str' to the server."""
        if self.sock is None:
            if self.auto_open:
                self.connect()
            else:
                raise NotConnected()

        # send the data to the server. if we get a broken pipe, then close
        # the socket. we want to reconnect when somebody tries to send again.
        #
        # NOTE: we DO propagate the error, though, because we cannot simply
        #      ignore the error... the caller will know if they can retry.
        if self.debuglevel > 0:
            print "send:", repr(str)
        try:
            self.sock.send(str)
        except socket.error, v:
            if v[0] == 32:    # Broken pipe
                self.close()
            raise

    def putrequest(self, method, url, skip_host=0, use_gzip=0):
        """Send a request to the server.

        `method' specifies an HTTP request method, e.g. 'GET'.
        `url' specifies the object being requested, e.g. '/index.html'.
        """

        # check if a prior response has been completed
        if self.__response and self.__response.isclosed():
            self.__response = None

        #
        # in certain cases, we cannot issue another request on this connection.
        # this occurs when:
        #   1) we are in the process of sending a request.   (_CS_REQ_STARTED)
        #   2) a response to a previous request has signalled that it is going
        #     to close the connection upon completion.
        #   3) the headers for the previous response have not been read, thus
        #     we cannot determine whether point (2) is true.   (_CS_REQ_SENT)
        #
        # if there is no prior response, then we can request at will.
        #
        # if point (2) is true, then we will have passed the socket to the
        # response (effectively meaning, "there is no prior response"), and
        # will open a new one when a new request is made.
        #
        # Note: if a prior response exists, then we *can* start a new request.
        #      We are not allowed to begin fetching the response to this new
        #      request, however, until that prior response is complete.
        #
        if self.__state == _CS_IDLE:
            self.__state = _CS_REQ_STARTED
        else:
            raise CannotSendRequest()

        if not url:
            url = '/'
        str = '%s %s %s\r\n' % (method, url, self._http_vsn_str)

        try:
            self.send(str)
        except socket.error, v:
            # trap 'Broken pipe' if we're allowed to automatically reconnect
            if v[0] != 32 or not self.auto_open:
                raise
            # try one more time (the socket was closed; this will reopen)
            self.send(str)

        if self._http_vsn == 11:
            # Issue some standard headers for better HTTP/1.1 compliance

            if not skip_host:
                # this header is issued *only* for HTTP/1.1
                # connections. more specifically, this means it is
                # only issued when the client uses the new
                # HTTPConnection() class. backwards-compat clients
                # will be using HTTP/1.0 and those clients may be
                # issuing this header themselves. we should NOT issue
                # it twice; some web servers (such as Apache) barf
                # when they see two Host: headers

                # If we need a non-standard port,include it in the
                # header.  If the request is going through a proxy,
                # but the host of the actual URL, not the host of the
                # proxy.

                netloc = ''
                if url.startswith('http'):
                    nil, netloc, nil, nil, nil = uriparse(url)

                if netloc:
                    self.putheader('Host', netloc)
                elif self.port == HTTP_PORT:
                    self.putheader('Host', self.host)
                else:
                    self.putheader('Host', "%s:%s" % (self.host, self.port))

            # note: we are assuming that clients will not attempt to set these
            #      headers since *this* library must deal with the
            #      consequences. this also means that when the supporting
            #      libraries are updated to recognize other forms, then this
            #      code should be changed (removed or updated).

            # we only want a Content-Encoding of "identity" since we don't
            # support encodings such as x-gzip or x-deflate.
            # gzip added to ashttplib - kwd
            if use_gzip:
                ae = 'gzip, identity'
            else:
                ae = 'identity'
            self.putheader('Accept-Encoding', ae)

            # we can accept "chunked" Transfer-Encodings, but no others
            # NOTE: no TE header implies *only* "chunked"
            #self.putheader('TE', 'chunked')

            # if TE is supplied in the header, then it must appear in a
            # Connection header.
            #self.putheader('Connection', 'TE')

        else:
            # For HTTP/1.0, the server will assume "not chunked"
            pass

    def putheader(self, header, value):
        """Send a request header line to the server.

        For example: h.putheader('Accept', 'text/html')
        """
        if self.__state != _CS_REQ_STARTED:
            raise CannotSendHeader()

        str = '%s: %s\r\n' % (header, value)
        self.send(str)

    def endheaders(self):
        """Indicate that the last header line has been sent to the server."""

        if self.__state == _CS_REQ_STARTED:
            self.__state = _CS_REQ_SENT
        else:
            raise CannotSendHeader()

        self.send('\r\n')

    def request(self, method, url, body=None, headers={}, use_gzip=0):
        """Send a complete request to the server."""

        try:
            self._send_request(method, url, body, headers, use_gzip)
        except socket.error, v:
            # trap 'Broken pipe' if we're allowed to automatically reconnect
            if v[0] != 32 or not self.auto_open:
                raise
            # try one more time
            self._send_request(method, url, body, headers, use_gzip)

    def _send_request(self, method, url, body, headers, use_gzip):
        # If headers already contains a host header, then define the
        # optional skip_host argument to putrequest().  The check is
        # harder because field names are case insensitive.
        if (headers.has_key('Host')
            or [k for k in headers.iterkeys() if k.lower() == "host"]):
            self.putrequest(method, url, skip_host=1, use_gzip=use_gzip)
        else:
            self.putrequest(method, url, skip_host=0, use_gzip=use_gzip)

        if body:
            self.putheader('Content-Length', str(len(body)))
        for hdr, value in headers.items():
            self.putheader(hdr, value)
        self.endheaders()

        if body:
            self.send(body)

    def getresponse(self):
        "Get the response from the server."

        # check if a prior response has been completed
        if self.__response and self.__response.isclosed():
            self.__response = None

        #
        # if a prior response exists, then it must be completed (otherwise, we
        # cannot read this response's header to determine the connection-close
        # behavior)
        #
        # note: if a prior response existed, but was connection-close, then the
        # socket and response were made independent of this HTTPConnection
        # object since a new request requires that we open a whole new
        # connection
        #
        # this means the prior response had one of two states:
        #   1) will_close: this connection was reset and the prior socket and
        #                 response operate independently
        #   2) persistent: the response was retained and we await its
        #                 isclosed() status to become true.
        #
        if self.__state != _CS_REQ_SENT or self.__response:
            raise ResponseNotReady()

        if self.debuglevel > 0:
            response = self.response_class(self.sock, self.debuglevel)
        else:
            response = self.response_class(self.sock)

        response.begin()
        self.__state = _CS_IDLE

        if response.will_close:
            # this effectively passes the connection to the response
            self.close()
        else:
            # remember this, so we can tell when it is complete
            self.__response = response

        return response



class FakeSocket(object):
    def __init__(self, sock, ssl):
        self.__sock = sock
        self.__ssl = ssl

    def makefile(self, mode, bufsize=None):
        """Return a readable file-like object with data from socket.

        This method offers only partial support for the makefile
        interface of a real socket.  It only supports modes 'r' and
        'rb' and the bufsize argument is ignored.

        The returned object contains *all* of the file data
        """
        from cStringIO import StringIO
        if mode != 'r' and mode != 'rb':
            raise UnimplementedFileMode()

        msgbuf = []
        while 1:
            try:
                buf = self.__ssl.read()
            except socket.sslerror, err:
                if (err[0] == socket.SSL_ERROR_WANT_READ
                    or err[0] == socket.SSL_ERROR_WANT_WRITE
                    or 0):
                    continue
                if err[0] == socket.SSL_ERROR_ZERO_RETURN:
                    break
                raise
            except socket.error, err:
                if err[0] == errno.EINTR:
                    continue
                raise
            if buf == '':
                break
            msgbuf.append(buf)
        return StringIO("".join(msgbuf))

    def send(self, stuff, flags = 0):
        return self.__ssl.write(stuff)

    def sendall(self, stuff, flags = 0):
        return self.__ssl.write(stuff)

    def recv(self, len = 1024, flags = 0):
        return self.__ssl.read(len)

    def __getattr__(self, attr):
        return getattr(self.__sock, attr)


class HTTPSConnection(HTTPConnection):
    "This class allows communication via SSL."

    default_port = HTTPS_PORT

    def __init__(self, host, port=None, **x509):
        keys = x509.keys()
        try:
            keys.remove('key_file')
        except ValueError:
            pass
        try:
            keys.remove('cert_file')
        except ValueError:
            pass
        if keys:
            raise IllegalKeywordArgument()
        HTTPConnection.__init__(self, host, port)
        self.key_file = x509.get('key_file')
        self.cert_file = x509.get('cert_file')

    def connect(self):
        "Connect to a host on a given (SSL) port."

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        realsock = sock
        if hasattr(sock, "_sock"):
            realsock = sock._sock
        ssl = socket.ssl(realsock, self.key_file, self.cert_file)
        self.sock = FakeSocket(sock, ssl)




def _test():
    cl = HTTPConnection("localhost:8080")



if __name__ == '__main__':
    _test()
