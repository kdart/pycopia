#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# Wrapper module for _socket, providing some additional facilities
# implemented in Python. 
# Forked and extended for Pycopia by Keith Dart. Also made python 3 compatible
# so you can use this module with either Python 2 or 3.

"""\
This module provides socket operations and some related functions.
On Unix, it supports IP (Internet Protocol) and Unix domain sockets.
On other systems, it only supports IP. Functions specific for a
socket are available as methods of the socket object.

Functions:

socket() -- create a new socket object
socketpair() -- create a pair of new socket objects [*]
fromfd() -- create a socket object from an open file descriptor [*]
gethostname() -- return the current hostname
gethostbyname() -- map a hostname to its IP number
gethostbyaddr() -- map an IP number or hostname to DNS info
getservbyname() -- map a service name and a protocol name to a port number
getprotobyname() -- map a protocol name (e.g. 'tcp') to a number
ntohs(), ntohl() -- convert 16, 32 bit int from network to host byte order
htons(), htonl() -- convert 16, 32 bit int from host to network byte order
inet_aton() -- convert IP addr string (123.45.67.89) to 32-bit packed format
inet_ntoa() -- convert 32-bit packed format IP to string (123.45.67.89)
ssl() -- secure socket layer support (only available if configured)
socket.getdefaulttimeout() -- get the default timeout value
socket.setdefaulttimeout() -- set the default timeout value
create_connection() -- connects to an address, with an optional timeout and
                       optional source address.

 [*] not available on all platforms!

Special objects:

SocketType -- type object for socket objects
error -- exception raised for I/O errors
has_ipv6 -- boolean value indicating if IPv6 is supported

Integer constants:

AF_INET, AF_UNIX -- socket domains (first argument to socket() call)
SOCK_STREAM, SOCK_DGRAM, SOCK_RAW -- socket types (second argument)

Many other constants may be defined; these may be used in calls to
the setsockopt() and getsockopt() methods.
"""

from __future__ import print_function

import os, sys
from io import StringIO
import _socket
from _socket import *
from errno import (EBADF, EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET,
     ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EADDRNOTAVAIL, EBADF)

from pycopia.aid import Enum, systemcall

SocketError = error

HostError = herror

GetAddressInfoError = gaierror

__all__ = ['SafeSocket', 'AsyncSocket', 'getfqdn', 'create_connection',
'opentcp', 'connect_inet', 'connect_tcp', 'connect_udp', 'connect_unix',
'connect_unix_datagram', 'unix_listener', 'unix_listener_datagram',
'udp_listener', 'tcp_listener', 'check_port', 'islocal']

__all__.extend(os._get_exports_list(_socket))


# socket states
CLOSED = Enum(0, "closed")
CONNECTED = Enum(1, "connected")
ACCEPTING = Enum(2, "accepting")

_realsocket = socket


def getfqdn(name=''):
    """Get fully qualified domain name from name.

    An empty argument is interpreted as meaning the local host.

    First the hostname returned by gethostbyaddr() is checked, then
    possibly existing aliases. In case no FQDN is available, hostname
    from gethostname() is returned.
    """
    name = name.strip()
    if not name or name == '0.0.0.0':
        name = gethostname()
    try:
        hostname, aliases, ipaddrs = gethostbyaddr(name)
    except error:
        pass
    else:
        aliases.insert(0, hostname)
        for name in aliases:
            if '.' in name:
                break
        else:
            name = hostname
    return name


# All the method names that must be delegated to either the real socket
# object or the _closedsocket object.
_delegate_methods = ("recv", "recvfrom", "recv_into", "recvfrom_into",
                     "send", "sendto")

class _closedsocket(object):
    __slots__ = []
    def _dummy(*args):
        raise error(EBADF, 'Bad file descriptor')
    # All _delegate_methods must also be initialized here.
    send = recv = recv_into = sendto = recvfrom = recvfrom_into = _dummy
    __getattr__ = _dummy

# Wrapper around platform socket objects. This implements
# a platform-independent dup() functionality. The
# implementation currently relies on reference counting
# to close the underlying socket object.
class _socketobject(object):

    __doc__ = _realsocket.__doc__

    __slots__ = ["_sock", "__weakref__"] + list(_delegate_methods)

    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None):
        if _sock is None:
            _sock = _realsocket(family, type, proto)
        self._sock = _sock
        for method in _delegate_methods:
            setattr(self, method, getattr(_sock, method))

    def close(self, _closedsocket=_closedsocket,
              _delegate_methods=_delegate_methods, setattr=setattr):
        # This function should not reference any globals. See issue #808164.
        self._sock = _closedsocket()
        dummy = self._sock._dummy
        for method in _delegate_methods:
            setattr(self, method, dummy)
    close.__doc__ = _realsocket.close.__doc__

    def accept(self):
        sock, addr = self._sock.accept()
        return _socketobject(_sock=sock), addr

    # TODO fixme, I don't think this is correct. They can't be independently closed.
    def dup(self):
        """dup() -> socket object

        Return a new socket object connected to the same system resource."""
        return _socketobject(_sock=self._sock)

    def makefile(self, mode='r', bufsize=-1):
        """makefile([mode[, bufsize]]) -> file object

        Return a regular file object corresponding to the socket.  The mode
        and bufsize arguments are as for the built-in open() function."""
        return _fileobject(self._sock, mode, bufsize)

    family = property(lambda self: self._sock.family, doc="the socket family")
    type = property(lambda self: self._sock.type, doc="the socket type")
    proto = property(lambda self: self._sock.proto, doc="the socket protocol")


if sys.version_info.major == 2:
### monkey patch new class delagates on py2
    def _meth(name, self, *args):
        return getattr(self._sock,name)(*args)

    from functools import partial
    from types import MethodType

    _socketmethods = (
        'bind', 'connect', 'connect_ex', 'fileno', 'listen',
        'getpeername', 'getsockname', 'getsockopt', 'setsockopt',
        'sendall', 'setblocking', 'settimeout', 'gettimeout', 'shutdown')

    if sys.platform == "riscos":
        _socketmethods = _socketmethods + ('sleeptaskw',)

    for _m in _socketmethods:
        p = partial(_meth, _m)
        p.__name__ = _m
        p.__doc__ = getattr(_realsocket, _m).__doc__
        m = MethodType(p, None, _socketobject)
        setattr(_socketobject, _m, m)

    del partial, MethodType, p, _m, _socketmethods
### end new class delegates

socket = SocketType = _socketobject

class _fileobject(object):
    """Faux file object attached to a socket object."""

    default_bufsize = 8192
    name = "<socket>"

    __slots__ = ["mode", "bufsize", "softspace",
                 # "closed" is a property, see below
                 "_sock", "_rbufsize", "_wbufsize", "_rbuf", "_wbuf", "_wbuf_len",
                 "_close"]

    def __init__(self, sock, mode='rb', bufsize=-1, close=False):
        self._sock = sock
        self.mode = mode # Not actually used in this version
        if bufsize < 0:
            bufsize = self.default_bufsize
        self.bufsize = bufsize
        self.softspace = False
        # _rbufsize is the suggested recv buffer size.  It is *strictly*
        # obeyed within readline() for recv calls.  If it is larger than
        # default_bufsize it will be used for recv calls within read().
        if bufsize == 0:
            self._rbufsize = 1
        elif bufsize == 1:
            self._rbufsize = self.default_bufsize
        else:
            self._rbufsize = bufsize
        self._wbufsize = bufsize
        # We use StringIO for the read buffer to avoid holding a list
        # of variously sized string objects which have been known to
        # fragment the heap due to how they are malloc()ed and often
        # realloc()ed down much smaller than their original allocation.
        self._rbuf = StringIO()
        self._wbuf = [] # A list of strings
        self._wbuf_len = 0
        self._close = close

    def _getclosed(self):
        return self._sock is None
    closed = property(_getclosed, doc="True if the file is closed")

    def close(self):
        try:
            if self._sock:
                self.flush()
        finally:
            if self._close:
                self._sock.close()
            self._sock = None

    def __del__(self):
        try:
            self.close()
        except:
            # close() may fail if __init__ didn't complete
            pass

    def flush(self):
        if self._wbuf:
            data = "".join(self._wbuf)
            self._wbuf = []
            self._wbuf_len = 0
            buffer_size = max(self._rbufsize, self.default_bufsize)
            data_size = len(data)
            write_offset = 0
            view = memoryview(data)
            try:
                while write_offset < data_size:
                    self._sock.sendall(view[write_offset:write_offset+buffer_size])
                    write_offset += buffer_size
            finally:
                if write_offset < data_size:
                    remainder = data[write_offset:]
                    del view, data  # explicit free
                    self._wbuf.append(remainder)
                    self._wbuf_len = len(remainder)

    def fileno(self):
        return self._sock.fileno()

    def write(self, data):
        data = str(data) # XXX Should really reject non-string non-buffers
        if not data:
            return
        self._wbuf.append(data)
        self._wbuf_len += len(data)
        if (self._wbufsize == 0 or
            self._wbufsize == 1 and '\n' in data or
            self._wbuf_len >= self._wbufsize):
            self.flush()

    def writelines(self, list):
        # XXX We could do better here for very long lists
        # XXX Should really reject non-string non-buffers
        lines = [_f for _f in map(str, list) if _f]
        self._wbuf_len += sum(map(len, lines))
        self._wbuf.extend(lines)
        if (self._wbufsize <= 1 or
            self._wbuf_len >= self._wbufsize):
            self.flush()

    def read(self, size=-1):
        # Use max, disallow tiny reads in a loop as they are very inefficient.
        # We never leave read() with any leftover data from a new recv() call
        # in our internal buffer.
        rbufsize = max(self._rbufsize, self.default_bufsize)
        # Our use of StringIO rather than lists of string objects returned by
        # recv() minimizes memory usage and fragmentation that occurs when
        # rbufsize is large compared to the typical return value of recv().
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        if size < 0:
            # Read until EOF
            self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
            while True:
                try:
                    data = self._sock.recv(rbufsize)
                except error as e:
                    if e.args[0] == EINTR:
                        continue
                    raise
                if not data:
                    break
                buf.write(data)
            return buf.getvalue()
        else:
            # Read until size bytes or EOF seen, whichever comes first
            buf_len = buf.tell()
            if buf_len >= size:
                # Already have size bytes in our buffer?  Extract and return.
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return rv

            self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
            while True:
                left = size - buf_len
                # recv() will malloc the amount of memory given as its
                # parameter even though it often returns much less data
                # than that.  The returned data string is short lived
                # as we copy it into a StringIO and free it.  This avoids
                # fragmentation issues on many platforms.
                try:
                    data = self._sock.recv(left)
                except error as e:
                    if e.args[0] == EINTR:
                        continue
                    raise
                if not data:
                    break
                n = len(data)
                if n == size and not buf_len:
                    # Shortcut.  Avoid buffer data copies when:
                    # - We have no data in our buffer.
                    # AND
                    # - Our call to recv returned exactly the
                    #   number of bytes we were asked to read.
                    return data
                if n == left:
                    buf.write(data)
                    del data  # explicit free
                    break
                assert n <= left, "recv(%d) returned %d bytes" % (left, n)
                buf.write(data)
                buf_len += n
                del data  # explicit free
                #assert buf_len == buf.tell()
            return buf.getvalue()

    def readline(self, size=-1):
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        if buf.tell() > 0:
            # check if we already have it in our buffer
            buf.seek(0)
            bline = buf.readline(size)
            if bline.endswith('\n') or len(bline) == size:
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return bline
            del bline
        if size < 0:
            # Read until \n or EOF, whichever comes first
            if self._rbufsize <= 1:
                # Speed up unbuffered case
                buf.seek(0)
                buffers = [buf.read()]
                self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
                data = None
                recv = self._sock.recv
                while True:
                    try:
                        while data != "\n":
                            data = recv(1)
                            if not data:
                                break
                            buffers.append(data)
                    except error as e:
                        # The try..except to catch EINTR was moved outside the
                        # recv loop to avoid the per byte overhead.
                        if e.args[0] == EINTR:
                            continue
                        raise
                    break
                return "".join(buffers)

            buf.seek(0, 2)  # seek end
            self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
            while True:
                try:
                    data = self._sock.recv(self._rbufsize)
                except error as e:
                    if e.args[0] == EINTR:
                        continue
                    raise
                if not data:
                    break
                nl = data.find('\n')
                if nl >= 0:
                    nl += 1
                    buf.write(data[:nl])
                    self._rbuf.write(data[nl:])
                    del data
                    break
                buf.write(data)
            return buf.getvalue()
        else:
            # Read until size bytes or \n or EOF seen, whichever comes first
            buf.seek(0, 2)  # seek end
            buf_len = buf.tell()
            if buf_len >= size:
                buf.seek(0)
                rv = buf.read(size)
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return rv
            self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
            while True:
                try:
                    data = self._sock.recv(self._rbufsize)
                except error as e:
                    if e.args[0] == EINTR:
                        continue
                    raise
                if not data:
                    break
                left = size - buf_len
                # did we just receive a newline?
                nl = data.find('\n', 0, left)
                if nl >= 0:
                    nl += 1
                    # save the excess data to _rbuf
                    self._rbuf.write(data[nl:])
                    if buf_len:
                        buf.write(data[:nl])
                        break
                    else:
                        # Shortcut.  Avoid data copy through buf when returning
                        # a substring of our first recv().
                        return data[:nl]
                n = len(data)
                if n == size and not buf_len:
                    # Shortcut.  Avoid data copy through buf when
                    # returning exactly all of our first recv().
                    return data
                if n >= left:
                    buf.write(data[:left])
                    self._rbuf.write(data[left:])
                    break
                buf.write(data)
                buf_len += n
                #assert buf_len == buf.tell()
            return buf.getvalue()

    def readlines(self, sizehint=0):
        total = 0
        list = []
        while True:
            line = self.readline()
            if not line:
                break
            list.append(line)
            total += len(line)
            if sizehint and total >= sizehint:
                break
        return list

    # Iterator protocols

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

_GLOBAL_DEFAULT_TIMEOUT = object()

def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    """Connect to *address* and return the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used.  If *source_address* is set it must be a tuple of (host, port)
    for the socket to bind as a source address before making the connection.
    An host of '' or port 0 tells the OS to use the default.
    """

    host, port = address
    err = None
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            return sock

        except error as _:
            err = _
            if sock is not None:
                sock.close()

    if err is not None:
        raise err
    else:
        raise error("getaddrinfo returns an empty list")


get_fqdn = getfqdn # alias

class SafeSocket(_realsocket):
    """A socket protected from interrupted system calls."""
    #accept = systemcall(_realsocket.accept)
    recv = systemcall(_realsocket.recv)
    send = systemcall(_realsocket.send)
    sendall = systemcall(_realsocket.sendall)
    connect = systemcall(_realsocket.connect)
    listen = systemcall(_realsocket.listen)
    bind = systemcall(_realsocket.bind)
    # make the socket a little bit file-like by itself
    read = systemcall(_realsocket.recv)
    write = systemcall(_realsocket.send)


class AsyncSocket(_realsocket):
    def __init__(self, family, type, proto=0):
        super(AsyncSocket, self).__init__(family, type, proto)
        self._state = CLOSED
        self._buf = ""

    def read(self, n=4096):
        return self.recv(n)

    # asyncio interface
    def readable(self):
        return True
        #return self._state == CONNECTED

    def writable(self):
        return (self._state == CONNECTED) and bool(self._buf)

    def priority(self):
        return False

    def socket_read(self):
        if __debug__:
            print("unhandled read", file=sys.stderr)

    def write_handler(self):
        self._send()
        if __debug__:
            print("unhandled read", file=sys.stderr)

    def hangup_handler(self):
        if __debug__:
            print("unhandled hangup", file=sys.stderr)

    def pri_handler(self):
        if __debug__:
            print("unhandled priority", file=sys.stderr)

    def error_handler(self, ex, val, tb):
        if __debug__:
            print("unhandled error: %s (%s)"  % (ex, val), file=sys.stderr)

    def handle_accept(self):
        if __debug__:
            print("unhandled accept", file=sys.stderr)

    def handle_connect(self):
        if __debug__:
            print("unhandled connect", file=sys.stderr)

    def read_handler(self):
        if self._state == ACCEPTING:
            # for an accepting socket, getting a read implies
            # that we are connected
            self._state = CONNECTED
            self.handle_accept()
        elif self._state == CLOSED:
            self.handle_connect()
            self._state = CONNECTED
            self.read()
        else:
            self.read()

    # socket methods
    def listen(self, num):
        self._state = ACCEPTING
        return super(AsyncSocket, self).listen(num)

    def bind(self, addr=INADDR_ANY):
        self.addr = addr
        return super(AsyncSocket, self).bind(addr)

    def connect(self, address):
        err = self.connect_ex(address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
            return
        if err in (0, EISCONN):
            self.addr = address
            self._state = CONNECTED
            self.handle_connect()
        else:
            raise SocketError(err)

    def accept(self):
        try:
            sa = super(AsyncSocket, self).accept()
        except SocketError as why:
            if why[0] == EWOULDBLOCK:
                pass
            else:
                raise SocketError(why)
        return sa

    def recv(self, amt, flags=0):
        while 1:
            try:
                next = super(AsyncSocket, self).recv(amt, flags)
            except SocketError as why:
                if why[0] == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return next

    def _send(self, flags=0):
        while 1:
            try:
                sent = super(AsyncSocket, self).send(self._buf[:4096], self._sendflags)
            except SocketError as why:
                if why[0] == EINTR:
                    continue
                else:
                    raise
            else:
                self._buf = self._buf[sent:]
                break
        return sent

    # fake the send and let the asyncio handler deal with it
    def send(self, data, flags=0):
        self._buf += data
        self._sendflags = flags
        return len(data)

    def makefile(self, mode='rb', bufsize=-1):
        return _fileobject(self, mode, bufsize)


def opentcp(host, port, sobject=SafeSocket):
    msg = "getaddrinfo returns an empty list"
    for res in getaddrinfo(str(host), int(port), 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            sock = sobject(af, socktype, proto)
            sock.connect(sa)
        except error as msg:
            if sock:
                sock.close()
            continue
        break
    if not sock:
        raise error(msg)
    return sock

# client connections:
def connect_inet(host, port, socktype, sobject=SafeSocket):
    args = getaddrinfo(str(host), int(port), AF_INET, socktype)
    for family, socktype, proto, canonname, sockaddr in args:
        try:
            s = sobject(family, socktype, proto)
            s.connect(sockaddr)
        except:
            continue
        else:
            return s
    raise

def connect_tcp(host, port, sobject=SafeSocket):
    return connect_inet(host, port, SOCK_STREAM, sobject)

def connect_udp(host, port, sobject=SafeSocket):
    return connect_inet(host, port, SOCK_DGRAM, sobject)

def connect_unix(path, sobject=SafeSocket):
    s = sobject(AF_UNIX, SOCK_STREAM)
    s.connect(path)
    return s

def connect_unix_datagram(path, sobject=SafeSocket):
    s = sobject(AF_UNIX, SOCK_DGRAM)
    s.connect(path)
    return s


# server (listener) functions:

def unix_listener(path, num=5, sobject=SafeSocket):
    try:
        os.unlink(path)
    except:
        pass
    s = sobject(AF_UNIX, SOCK_STREAM)
    s.bind(path)
    s.listen(num)
    return s

# The num parameter is not used with the following functions, but is
# retained for consistency with the other listener functions.

def unix_listener_datagram(path, num=5, sobject=SafeSocket):
    s = sobject(AF_UNIX, SOCK_DGRAM)
    s.bind(path)
    return s

def udp_listener(addr, num=5, sobject=SafeSocket):
    s = sobject(AF_INET, SOCK_DGRAM)
    s.bind(addr)
    return s

def tcp_listener(addr, num=5, sobject=SafeSocket):
    s = sobject(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(num)
    return s

# utility functions:

def check_port(host, port):
    """Checks a TCP port on a remote host for a listener. Returns true if a
    connection is possible, false otherwise."""
    try:
        s = connect_tcp(host, port)
    except error:
        return 0
    s.close()
    return 1

def islocal(host):
    """islocal(host) tests if the given host is ourself, or not."""
    # try to bind to the address, if successful it is local...
    ip = gethostbyname(getfqdn(host))
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.bind((ip, IPPORT_USERRESERVED+1))
    except error as err:
        if err[0] == EADDRNOTAVAIL:
            return 0
        else:
            raise
    else:
        s.close()
        return 1

