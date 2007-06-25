#!/usr/bin/python2.4
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (c) 2002, 2003, 2005, 2006 Allan Saddi <allan@saddi.com>
# All rights reserved.
# 
# Modified for Pycopia (use subprocesses instead of threads) by
# Keith Dart <keith.dart@gmail.com>.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# $Id$

"""
fcgi - a FastCGI/WSGI gateway.

For more information about FastCGI, see <http://www.fastcgi.com/>.

For more information about the Web Server Gateway Interface, see
<http://www.python.org/peps/pep-0333.html>.

Example usage:

  #!/usr/bin/env python
  from myapplication import app # Assume app is your WSGI application object
  from pycopia.inet.fcgi import FCGIServer
  FCGIServer(app).run()

See the documentation for FCGIServer/Server for more information.

On most platforms, fcgi will fallback to regular CGI behavior if run in a
non-FastCGI context. If you want to force CGI behavior, set the environment
variable FCGI_FORCE_CGI to "Y" or "y".
"""

__version__ = '$Revision$'

__all__ = ['FCGIServer']

import sys
import os
import signal
import struct
import select
import errno
import traceback
import cgitb

from pycopia import socket
from pycopia.aid import systemcall, NULL

socket.SHUT_WR = 1

import resource
MAXCONNS = resource.getrlimit(resource.RLIMIT_NOFILE)[0]

# Constants from the spec.
FCGI_LISTENSOCK_FILENO = 0

FCGI_HEADER_LEN = 8

FCGI_VERSION_1 = 1

FCGI_BEGIN_REQUEST = 1
FCGI_ABORT_REQUEST = 2
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_DATA = 8
FCGI_GET_VALUES = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

FCGI_NULL_REQUEST_ID = 0

FCGI_KEEP_CONN = 1

FCGI_RESPONDER = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER = 3

FCGI_REQUEST_COMPLETE = 0
FCGI_CANT_MPX_CONN = 1
FCGI_OVERLOADED = 2
FCGI_UNKNOWN_ROLE = 3

FCGI_MAX_CONNS = 'FCGI_MAX_CONNS'
FCGI_MAX_REQS = 'FCGI_MAX_REQS'
FCGI_MPXS_CONNS = 'FCGI_MPXS_CONNS'

FCGI_Header = '!BBHHBx'
FCGI_BeginRequestBody = '!HB5x'
FCGI_EndRequestBody = '!LB3x'
FCGI_UnknownTypeBody = '!B7x'

FCGI_EndRequestBody_LEN = struct.calcsize(FCGI_EndRequestBody)
FCGI_UnknownTypeBody_LEN = struct.calcsize(FCGI_UnknownTypeBody)

if __debug__:
    import time

    # Set non-zero to write debug output to a file.
    DEBUG = 10
    DEBUGLOG = '/var/tmp/fcgi.log'

    def _debug(level, msg):
        if DEBUG < level:
            return

        try:
            f = open(DEBUGLOG, 'a')
            f.write('%sfcgi: %s\n' % (time.ctime()[4:-4], msg))
            f.close()
        except:
            pass

class InputStream(object):
    """
    File-like object representing FastCGI input streams (FCGI_STDIN and
    FCGI_DATA). Supports the minimum methods required by WSGI spec.
    """
    def __init__(self, conn):
        self._conn = conn

        # See Server.
        self._shrinkThreshold = conn.server.inputStreamShrinkThreshold

        self._buf = ''
        self._bufList = []
        self._pos = 0 # Current read position.
        self._avail = 0 # Number of bytes currently available.

        self._eof = False # True when server has sent EOF notification.

    def _shrinkBuffer(self):
        """Gets rid of already read data (since we can't rewind)."""
        if self._pos >= self._shrinkThreshold:
            self._buf = self._buf[self._pos:]
            self._avail -= self._pos
            self._pos = 0

            assert self._avail >= 0

    def _waitForData(self):
        """Waits for more data to become available."""
        self._conn.process_input()

    def read(self, n=-1):
        if self._pos == self._avail and self._eof:
            return ''
        while True:
            if n < 0 or (self._avail - self._pos) < n:
                # Not enough data available.
                if self._eof:
                    # And there's no more coming.
                    newPos = self._avail
                    break
                else:
                    # Wait for more data.
                    self._waitForData()
                    continue
            else:
                newPos = self._pos + n
                break
        # Merge buffer list, if necessary.
        if self._bufList:
            self._buf += ''.join(self._bufList)
            self._bufList = []
        r = self._buf[self._pos:newPos]
        self._pos = newPos
        self._shrinkBuffer()
        return r

    def readline(self, length=None):
        if self._pos == self._avail and self._eof:
            return ''
        while True:
            # Unfortunately, we need to merge the buffer list early.
            if self._bufList:
                self._buf += ''.join(self._bufList)
                self._bufList = []
            # Find newline.
            i = self._buf.find('\n', self._pos)
            if i < 0:
                # Not found?
                if self._eof:
                    # No more data coming.
                    newPos = self._avail
                    break
                else:
                    # Wait for more to come.
                    self._waitForData()
                    continue
            else:
                newPos = i + 1
                break
        if length is not None:
            if self._pos + length < newPos:
                newPos = self._pos + length
        r = self._buf[self._pos:newPos]
        self._pos = newPos
        self._shrinkBuffer()
        return r

    def readlines(self, sizehint=0):
        total = 0
        lines = []
        line = self.readline()
        while line:
            lines.append(line)
            total += len(line)
            if 0 < sizehint <= total:
                break
            line = self.readline()
        return lines

    def __iter__(self):
        return self

    def next(self):
        r = self.readline()
        if not r:
            raise StopIteration
        return r

    def add_data(self, data):
        if not data:
            self._eof = True
        else:
            self._bufList.append(data)
            self._avail += len(data)


class OutputStream(object):
    """
    FastCGI output stream (FCGI_STDOUT/FCGI_STDERR). By default, calls to
    write() or writelines() immediately result in Records being sent back
    to the server. Buffering should be done in a higher level!
    """
    def __init__(self, conn, req, type, buffered=False):
        self._conn = conn
        self._req = req
        self._type = type
        self._buffered = buffered
        self._bufList = [] # Used if buffered is True
        self.dataWritten = False
        self.closed = False

    def _write(self, data):
        length = len(data)
        while length:
            toWrite = min(length, self._req.server.maxwrite - FCGI_HEADER_LEN)

            rec = Record(self._type, self._req.requestId)
            rec.contentLength = toWrite
            rec.contentData = data[:toWrite]
            self._conn.writeRecord(rec)

            data = data[toWrite:]
            length -= toWrite

    def write(self, data):
        assert not self.closed

        if not data:
            return

        self.dataWritten = True

        if self._buffered:
            self._bufList.append(data)
        else:
            self._write(data)

    def writelines(self, lines):
        assert not self.closed

        for line in lines:
            self.write(line)

    def flush(self):
        # Only need to flush if this OutputStream is actually buffered.
        if self._buffered:
            data = ''.join(self._bufList)
            self._bufList = []
            self._write(data)

    # Though available, the following should NOT be called by WSGI apps.
    def close(self):
        """Sends end-of-stream notification, if necessary."""
        if not self.closed and self.dataWritten:
            self.flush()
            rec = Record(self._type, self._req.requestId)
            self._conn.writeRecord(rec)
            self.closed = True

class TeeOutputStream(object):
    """
    Simple wrapper around two or more output file-like objects that copies
    written data to all streams.
    """
    def __init__(self, streamList):
        self._streamList = streamList

    def write(self, data):
        for f in self._streamList:
            f.write(data)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        for f in self._streamList:
            f.flush()

class StdoutWrapper(object):
    """
    Wrapper for sys.stdout so we know if data has actually been written.
    """
    def __init__(self, stdout):
        self._file = stdout
        self.dataWritten = False

    def write(self, data):
        if data:
            self.dataWritten = True
        self._file.write(data)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def __getattr__(self, name):
        return getattr(self._file, name)

def decode_pair(s, pos=0):
    """
    Decodes a name/value pair.

    The number of bytes decoded as well as the name/value pair
    are returned.
    """
    nameLength = ord(s[pos])
    if nameLength & 128:
        nameLength = struct.unpack('!L', s[pos:pos+4])[0] & 0x7fffffff
        pos += 4
    else:
        pos += 1

    valueLength = ord(s[pos])
    if valueLength & 128:
        valueLength = struct.unpack('!L', s[pos:pos+4])[0] & 0x7fffffff
        pos += 4
    else:
        pos += 1

    name = s[pos:pos+nameLength]
    pos += nameLength
    value = s[pos:pos+valueLength]
    pos += valueLength

    return (pos, (name, value))

def encode_pair(name, value):
    """
    Encodes a name/value pair.

    The encoded string is returned.
    """
    nameLength = len(name)
    if nameLength < 128:
        s = chr(nameLength)
    else:
        s = struct.pack('!L', nameLength | 0x80000000L)

    valueLength = len(value)
    if valueLength < 128:
        s += chr(valueLength)
    else:
        s += struct.pack('!L', valueLength | 0x80000000L)

    return s + name + value
    
class Record(object):
    """
    A FastCGI Record.

    Used for encoding/decoding records.
    """
    def __init__(self, type=FCGI_UNKNOWN_TYPE, requestId=FCGI_NULL_REQUEST_ID):
        self.version = FCGI_VERSION_1
        self.type = type
        self.requestId = requestId
        self.contentLength = 0
        self.paddingLength = 0
        self.contentData = ''

    def _recvall(sock, length):
        """
        Attempts to receive length bytes from a socket, blocking if necessary.
        (Socket may be blocking or non-blocking.)
        """
        dataList = []
        recvLen = 0
        while length:
            try:
                data = sock.recv(length)
            except socket.error, e:
                if e[0] == errno.EAGAIN:
                    select.select([sock], [], [])
                    continue
                elif e[0] == errno.EINTR:
                    continue
                else:
                    raise
            if not data: # EOF
                break
            dataList.append(data)
            dataLen = len(data)
            recvLen += dataLen
            length -= dataLen
        return ''.join(dataList), recvLen
    _recvall = staticmethod(_recvall)

    def read(self, sock):
        """Read and decode a Record from a socket."""
        try:
            header, length = self._recvall(sock, FCGI_HEADER_LEN)
        except:
            raise EOFError

        if length < FCGI_HEADER_LEN:
            raise EOFError
        
        self.version, self.type, self.requestId, self.contentLength, \
                      self.paddingLength = struct.unpack(FCGI_Header, header)

        if __debug__: _debug(9, 'read: fd = %d, type = %d, requestId = %d, '
                             'contentLength = %d' %
                             (sock.fileno(), self.type, self.requestId,
                              self.contentLength))
        
        if self.contentLength:
            try:
                self.contentData, length = self._recvall(sock,
                                                         self.contentLength)
            except:
                raise EOFError

            if length < self.contentLength:
                raise EOFError

        if self.paddingLength:
            try:
                self._recvall(sock, self.paddingLength)
            except:
                raise EOFError

    def _sendall(sock, data):
        """
        Writes data to a socket and does not return until all the data is sent.
        """
        length = len(data)
        while length:
            try:
                sent = sock.send(data)
            except socket.error, e:
                if e[0] == errno.EAGAIN:
                    select.select([], [sock], [])
                    continue
                else:
                    raise
            data = data[sent:]
            length -= sent
    _sendall = staticmethod(_sendall)

    def write(self, sock):
        """Encode and write a Record to a socket."""
        self.paddingLength = -self.contentLength & 7

        if __debug__: _debug(9, 'write: fd = %d, type = %d, requestId = %d, '
                             'contentLength = %d' %
                             (sock.fileno(), self.type, self.requestId,
                              self.contentLength))

        header = struct.pack(FCGI_Header, self.version, self.type,
                             self.requestId, self.contentLength,
                             self.paddingLength)
        self._sendall(sock, header)
        if self.contentLength:
            self._sendall(sock, self.contentData)
        if self.paddingLength:
            self._sendall(sock, '\x00'*self.paddingLength)


class Request(object):
    """
    Represents a single FastCGI request.

    These objects are passed to your handler and is the main interface
    between your handler and the fcgi module. The methods should not
    be called by your handler. However, server, params, stdin, stdout,
    stderr, and data are free for your handler's use.
    """
    def __init__(self, conn, inputStreamClass):
        self._conn = conn

        self.server = conn.server
        self.params = {}
        self.stdin = inputStreamClass(conn)
        self.stdout = OutputStream(conn, self, FCGI_STDOUT)
        self.stderr = OutputStream(conn, self, FCGI_STDERR, buffered=True)
        self.data = inputStreamClass(conn)

    def run(self):
        """Runs the handler, flushes the streams, and ends the request."""
        try:
            protocolStatus, appStatus = self.server.handler(self)
        except:
            try:
                etype, value, tb = sys.exc_info()
                traceback.print_exception(etype, value, tb, None, self.stderr)
                self.stderr.flush()
                if not self.stdout.dataWritten:
                    self.server.error(etype, value, tb, self.stdout)
            finally:
                etype = value = tb = None
            protocolStatus = FCGI_REQUEST_COMPLETE
            appStatus = 0

        if __debug__: _debug(1, 'protocolStatus = %d, appStatus = %d' %
                             (protocolStatus, appStatus))
        self._flush()
        self._end(appStatus, protocolStatus)

    def _end(self, appStatus=0L, protocolStatus=FCGI_REQUEST_COMPLETE):
        self._conn.end_request(self, appStatus, protocolStatus)

    def _flush(self):
        self.stdout.close()
        self.stderr.close()


class Connection(object):
    """
    A Connection with the web server.

    Each Connection is associated with a single socket (which is
    connected to the web server) and is responsible for handling all
    the FastCGI message processing for that socket.
    """
    _multiplexed = False
    _inputStreamClass = InputStream

    def __init__(self, sock, addr, server):
        self._sock = sock
        self._addr = addr
        self.server = server

        # Active Requests for this Connection, mapped by request ID.
        self._requests = {}

    def _cleanupSocket(self):
        """Close the Connection's socket."""
        try:
            self._sock.shutdown(socket.SHUT_WR)
        except:
            return
        try:
            while True:
                r, w, e = select.select([self._sock], [], [])
                if not r or not self._sock.recv(1024):
                    break
        except:
            pass
        self._sock.close()

    def run(self):
        """Begin processing data from the socket."""
        self._keepGoing = True
        while self._keepGoing:
            try:
                self.process_input()
            except EOFError:
                break
            except (select.error, socket.error), e:
                if e[0] == errno.EBADF: # Socket was closed by Request.
                    break
                raise
        self._cleanupSocket()

    @systemcall
    def process_input(self):
        """Attempt to read a single Record from the socket and process it."""
        # Currently, any children Request process notify this Connection
        # that it is no longer needed by closing the Connection's socket.
        # We need to put a timeout on select, otherwise we might get
        # stuck in it indefinitely... (I don't like this solution.)
        while self._keepGoing:
            try:
                r, w, e = select.select([self._sock], [], [], 1.0)
            except ValueError:
                # Sigh. ValueError gets thrown sometimes when passing select
                # a closed socket.
                raise EOFError
            if r: 
                break
        if not self._keepGoing:
            return
        rec = Record()
        rec.read(self._sock)

        if rec.type == FCGI_GET_VALUES:
            self._do_get_values(rec)
        elif rec.type == FCGI_BEGIN_REQUEST:
            self._do_begin_request(rec)
        elif rec.type == FCGI_ABORT_REQUEST:
            self._do_abort_request(rec)
        elif rec.type == FCGI_PARAMS:
            self._do_params(rec)
        elif rec.type == FCGI_STDIN:
            self._do_stdin(rec)
        elif rec.type == FCGI_DATA:
            self._do_data(rec)
        elif rec.requestId == FCGI_NULL_REQUEST_ID:
            self._do_unknown_type(rec)
        else:
            # Need to complain about this.
            pass

    def writeRecord(self, rec):
        """
        Write a Record to the socket.
        """
        rec.write(self._sock)

    def end_request(self, req, appStatus=0L,
                    protocolStatus=FCGI_REQUEST_COMPLETE, remove=True):
        """
        End a Request.

        Called by Request objects. An FCGI_END_REQUEST Record is
        sent to the web server. If the web server no longer requires
        the connection, the socket is closed, thereby ending this
        Connection (run() returns).
        """
        rec = Record(FCGI_END_REQUEST, req.requestId)
        rec.contentData = struct.pack(FCGI_EndRequestBody, appStatus,
                                      protocolStatus)
        rec.contentLength = FCGI_EndRequestBody_LEN
        self.writeRecord(rec)

        if remove:
            del self._requests[req.requestId]

        if __debug__: _debug(2, 'end_request: flags = %d' % req.flags)

        if not (req.flags & FCGI_KEEP_CONN) and not self._requests:
            self._cleanupSocket()
            self._keepGoing = False

    def _do_get_values(self, inrec):
        """Handle an FCGI_GET_VALUES request from the web server."""
        outrec = Record(FCGI_GET_VALUES_RESULT)

        pos = 0
        while pos < inrec.contentLength:
            pos, (name, value) = decode_pair(inrec.contentData, pos)
            cap = self.server.capability.get(name)
            if cap is not None:
                outrec.contentData += encode_pair(name, str(cap))

        outrec.contentLength = len(outrec.contentData)
        self.writeRecord(outrec)

    def _do_begin_request(self, inrec):
        """Handle an FCGI_BEGIN_REQUEST from the web server."""
        role, flags = struct.unpack(FCGI_BeginRequestBody, inrec.contentData)

        req = Request(self, self._inputStreamClass)
        req.requestId, req.role, req.flags = inrec.requestId, role, flags
        req.aborted = False

        if not self._multiplexed and self._requests:
            # Can't multiplex requests.
            self.end_request(req, 0L, FCGI_CANT_MPX_CONN, remove=False)
        else:
            self._requests[inrec.requestId] = req

    def _do_abort_request(self, inrec):
        """
        Handle an FCGI_ABORT_REQUEST from the web server.

        We just mark a flag in the associated Request.
        """
        req = self._requests.get(inrec.requestId)
        if req is not None:
            req.aborted = True

    def _start_request(self, req):
        """Run the request."""
        req.run()

    def _do_params(self, inrec):
        """
        Handle an FCGI_PARAMS Record.

        If the last FCGI_PARAMS Record is received, start the request.
        """
        req = self._requests.get(inrec.requestId)
        if req is not None:
            if inrec.contentLength:
                pos = 0
                while pos < inrec.contentLength:
                    pos, (name, value) = decode_pair(inrec.contentData, pos)
                    req.params[name] = value
            else:
                self._start_request(req)

    def _do_stdin(self, inrec):
        """Handle the FCGI_STDIN stream."""
        req = self._requests.get(inrec.requestId)
        if req is not None:
            req.stdin.add_data(inrec.contentData)

    def _do_data(self, inrec):
        """Handle the FCGI_DATA stream."""
        req = self._requests.get(inrec.requestId)
        if req is not None:
            req.data.add_data(inrec.contentData)

    def _do_unknown_type(self, inrec):
        """Handle an unknown request type. Respond accordingly."""
        outrec = Record(FCGI_UNKNOWN_TYPE)
        outrec.contentData = struct.pack(FCGI_UnknownTypeBody, inrec.type)
        outrec.contentLength = FCGI_UnknownTypeBody_LEN
        self.writeRecord(rec)



# A FCGI process manager is responsible for calling the connection's run
# method in some way.
class ProcessManager(object):
    def __init__(self):
        from pycopia import proctools
        self._procmanager = proctools.get_procmanager()

    def __call__(self, func):
        self._procmanager.subprocess(func)


def DefaultErrorHandler(ex, val, tb, stream):
    stream.write('Content-Type: text/html\r\n\r\n' +
                     cgitb.html((ex, val, tb)))


class FCGIServer(object):
    """
    FastCGI server that supports the Web Server Gateway Interface. See
    <http://www.python.org/peps/pep-0333.html>.

    The FastCGI server.

    Waits for connections from the web server, processing each
    request.
    """
    # Limits the size of the InputStream's string buffer to this size + the
    # server's maximum Record size. Since the InputStream is not seekable,
    # we throw away already-read data once this certain amount has been read.
    inputStreamShrinkThreshold = 102400 - 8192

    def __init__(self, application, procmanager=None, errorhandler=None, 
            environ=None, maxwrite=8192, bindAddress=None, umask=None, 
            idle=NULL, debug=False):
        """

        environ, if present, must be a dictionary-like object. Its
        contents will be copied into application's environ. Useful
        for passing application-specific variables.

        maxwrite is the maximum number of bytes (per Record) to write
        to the server. I've noticed mod_fastcgi has a relatively small
        receive buffer (8K or so).

        bindAddress, if present, must either be a string or a 2-tuple. If
        present, run() will open its own listening socket. You would use
        this if you wanted to run your application as an 'external' FastCGI
        app. (i.e. the webserver would no longer be responsible for starting
        your app) If a string, it will be interpreted as a filename and a UNIX
        socket will be opened. If a tuple, the first element, a string,
        is the interface name/IP to bind to, and the second element (an int)
        is the port number.

        """
        self.application = application # the WSGI application
        self.error = errorhandler or DefaultErrorHandler # error handler
        self._procmanager = procmanager or ProcessManager()
        self._idle_cb = idle # called in select loop when idle
        self.environ = environ or {}
        self.maxwrite = maxwrite
        self._bindAddress = bindAddress
        self._umask = umask
        self._debug = debug
        self.capability = {
            FCGI_MAX_CONNS: MAXCONNS,
            FCGI_MAX_REQS: MAXCONNS,
            FCGI_MPXS_CONNS: 0
            }

    def _setupSocket(self):
        if self._bindAddress is None: # Run as a normal FastCGI?

            sock = socket.fromfd(FCGI_LISTENSOCK_FILENO, socket.AF_INET,
                                 socket.SOCK_STREAM)
            try:
                sock.getpeername()
            except socket.error, e:
                if e[0] != errno.ENOTCONN:
                    raise
        else:
            # Run as a server
            oldUmask = None
            if type(self._bindAddress) is str:
                # Unix socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    os.unlink(self._bindAddress)
                except OSError:
                    pass
                if self._umask is not None:
                    oldUmask = os.umask(self._umask)
            else:
                # INET socket
                assert type(self._bindAddress) is tuple
                assert len(self._bindAddress) == 2
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock.bind(self._bindAddress)
            sock.listen(socket.SOMAXCONN)

            if oldUmask is not None:
                os.umask(oldUmask)
        return sock

    def _cleanupSocket(self, sock):
        """Closes the main socket."""
        sock.close()
        try:
            os.unlink(self._bindAddress)
        except:
            pass

    def _installSignalHandlers(self):
        self._oldSIGs = [(x,signal.getsignal(x)) for x in
                         (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)]
        signal.signal(signal.SIGHUP, self._hupHandler)
        signal.signal(signal.SIGINT, self._intHandler)
        signal.signal(signal.SIGTERM, self._intHandler)

    def _restoreSignalHandlers(self):
        for signum,handler in self._oldSIGs:
            signal.signal(signum, handler)

    def _hupHandler(self, signum, frame):
        self._hupReceived = True
        self._keepGoing = False

    def _intHandler(self, signum, frame):
        self._keepGoing = False

    def run(self, timeout=1.0):
        """
        The main loop. Exits on SIGHUP, SIGINT, SIGTERM. Returns True if
        SIGHUP was received, False otherwise.
        """
        web_server_addrs = os.environ.get('FCGI_WEB_SERVER_ADDRS')
        if web_server_addrs is not None:
            web_server_addrs = map(lambda x: x.strip(),
                                   web_server_addrs.split(','))

        sock = self._setupSocket()

        self._keepGoing = True
        self._hupReceived = False

        # Install signal handlers.
        self._installSignalHandlers()

        while self._keepGoing:
            try:
                r, w, e = select.select([sock], [], [], timeout)
            except select.error, e:
                if e[0] == errno.EINTR:
                    continue
                raise

            if r:
                try:
                    clientSock, addr = sock.accept()
                except socket.error, e:
                    if e[0] in (errno.EINTR, errno.EAGAIN):
                        continue
                    raise

                if web_server_addrs and \
                       (len(addr) != 2 or addr[0] not in web_server_addrs):
                    clientSock.close()
                    continue

                conn = Connection(clientSock, addr, self)
                if self._debug:
                    conn.run() # bypass process manager
                else:
                    self._procmanager(conn.run)

            self._idle_cb()
        # Restore signal handlers.
        self._restoreSignalHandlers()
        self._cleanupSocket(sock)
        return self._hupReceived

    def _exit(self, reload=False):
        """
        Protected convenience method for subclasses to force an exit.
        """
        if self._keepGoing:
            self._keepGoing = False
            self._hupReceived = reload

    def handler(self, req):
        """Handles WSGI request."""
        if req.role != FCGI_RESPONDER:
            return FCGI_UNKNOWN_ROLE, 0

        environ = req.params
        environ.update(self.environ)

        environ['wsgi.version'] = (1,0)
        environ['wsgi.input'] = req.stdin
        if self._bindAddress is None:
            stderr = req.stderr
        else:
            stderr = TeeOutputStream((sys.stderr, req.stderr))
        environ['wsgi.errors'] = stderr
        environ['wsgi.multithread'] = False
        environ['wsgi.run_once'] = False
        environ['wsgi.multiprocess'] = not self._debug

        if environ.get('HTTPS', 'off') in ('on', '1'):
            environ['wsgi.url_scheme'] = 'https'
        else:
            environ['wsgi.url_scheme'] = 'http'

        self._sanitizeEnv(environ)

        headers_set = []
        headers_sent = []
        result = None

        def write(data):
            assert type(data) is str, 'write() argument must be string'
            assert headers_set, 'write() before start_response()'

            if not headers_sent:
                status, responseHeaders = headers_sent[:] = headers_set
                found = False
                for header,value in responseHeaders:
                    if header.lower() == 'content-length':
                        found = True
                        break
                if not found and result is not None:
                    try:
                        if len(result) == 1:
                            responseHeaders.append(('Content-Length',
                                                    str(len(data))))
                    except:
                        if __debug__: 
                            ex, val, tb = sys.exc_info()
                            _debug(1, "write: %s: %s" % (ex, val))
                req.stdout.write('Status: %s\r\n' % status)
                for header in responseHeaders:
                    req.stdout.write('%s: %s\r\n' % header)
                req.stdout.write('\r\n')

            req.stdout.write(data)
            req.stdout.flush()

        def start_response(status, response_headers, exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        # Re-raise if too late
                        raise exc_info[0], exc_info[1], exc_info[2]
                finally:
                    exc_info = None # avoid dangling circular ref
            else:
                assert not headers_set, 'Headers already set!'

            assert type(status) is str, 'Status must be a string'
            assert len(status) >= 4, 'Status must be at least 4 characters'
            assert int(status[:3]), 'Status must begin with 3-digit code'
            assert status[3] == ' ', 'Status must have a space after code'
            assert type(response_headers) is list, 'Headers must be a list'
            for name,val in response_headers:
                assert type(name) is str, 'Header names must be strings'
                assert type(val) is str, 'Header values must be strings'

            headers_set[:] = [status, response_headers]
            return write

        try:
            result = self.application(environ, start_response)
            try:
                for data in result:
                    if data:
                        write(data)
                if not headers_sent:
                    write('') # in case body was empty
            finally:
                if hasattr(result, 'close'):
                    result.close()
        except socket.error, e:
            if e[0] != errno.EPIPE:
                raise # Don't let EPIPE propagate beyond server

        return FCGI_REQUEST_COMPLETE, 0


    def _sanitizeEnv(self, environ):
        """Ensure certain values are present, if required by WSGI."""
        if not environ.has_key('SCRIPT_NAME'):
            environ['SCRIPT_NAME'] = ''
        if not environ.has_key('PATH_INFO'):
            environ['PATH_INFO'] = ''

        # If any of these are missing, it probably signifies a broken
        # server...
        for name,default in [('REQUEST_METHOD', 'GET'),
                             ('SERVER_NAME', 'localhost'),
                             ('SERVER_PORT', '80'),
                             ('SERVER_PROTOCOL', 'HTTP/1.0')]:
            if not environ.has_key(name):
                environ['wsgi.errors'].write('%s: missing FastCGI param %s '
                                             'required by WSGI!\n' %
                                             (self.__class__.__name__, name))
                environ[name] = default

if __name__ == '__main__':
    def test_app(environ, start_response):
        """Probably not the most efficient example."""
        import cgi
        start_response('200 OK', [('Content-Type', 'text/html')])
        yield '<html><head><title>Hello World!</title></head>\n' \
              '<body>\n' \
              '<p>Hello World!</p>\n' \
              '<table border="1">'
        names = environ.keys()
        names.sort()
        for name in names:
            yield '<tr><td>%s</td><td>%s</td></tr>\n' % (
                name, cgi.escape(`environ[name]`))

        form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ,
                                keep_blank_values=1)
        if form.list:
            yield '<tr><th colspan="2">Form data</th></tr>'

        for field in form.list:
            yield '<tr><td>%s</td><td>%s</td></tr>\n' % (
                field.name, field.value)

        yield '</table>\n' \
              '</body></html>\n'

    FCGIServer(test_app).run()
