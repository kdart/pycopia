#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# Wrapper module for _socket, providing some additional facilities
# implemented in Python.
# Forked and extended for Pycopia by Keith Dart. Base module backported from Python 3
# so you can use these methods with either Python 2 or 3.

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
socket.getdefaulttimeout() -- get the default timeout value
socket.setdefaulttimeout() -- set the default timeout value
create_connection() -- connects to an address, with an optional timeout and optional source address.

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

import _socket
from _socket import *

import os, sys, io
import fcntl, struct

from errno import (EBADF, EAGAIN, EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET,
     ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EADDRNOTAVAIL, EBADF)

__all__ = ['socket', 'SocketIO', 'SafeSocket', 'AsyncSocket', 'getfqdn',
'create_connection', 'opentcp', 'connect_inet', 'connect_tcp', 'connect_udp',
'connect_unix', 'connect_unix_datagram', 'unix_listener',
'unix_listener_datagram', 'udp_listener', 'tcp_listener', 'check_port',
'islocal', 'inq', 'outq']
__all__.extend(os._get_exports_list(_socket))

from pycopia.aid import systemcall

# Aliases for more Python style exceptions
SocketError = error
HostError = herror
GetAddressInfoError = gaierror

# extra ioctl numbers
SIOCINQ = 0x541B
SIOCOUTQ = 0x5411

import sys

# enables this module to work with either python 2.x or 3.x
if sys.version_info.major == 2:
    _compatsocket = lambda self, family, type, proto, fileno: _socket.socket.__init__(self, family, type, proto)
else:
    _compatsocket = _socket.socket.__init__


class socket(_socket.socket):
    """A subclass of _socket.socket adding the makefile() method."""

    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None):
        _compatsocket(self, family, type, proto, fileno)
        self._io_refs = 0
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self._closed:
            self.close()

    def __repr__(self):
        """Wrap __repr__() to reveal the real class name."""
        s = _socket.socket.__repr__(self)
        if s.startswith("<socket object"):
            s = "<%s.%s%s%s" % (self.__class__.__module__,
                                self.__class__.__name__,
                                getattr(self, '_closed', False) and " [closed] " or "",
                                s[7:])
        return s

    def inq(self):
        return inq(self)

    def outq(self):
        return outq(self)

    # for python 3.x  compatibility
    if sys.version_info.major == 3:
        def accept(self):
            """accept() -> (socket object, address info)
            """
            fd, addr = self._accept()
            sock = socket(self.family, self.type, self.proto, fileno=fd)
            return sock, addr

    def makefile(self, mode="rwb", buffering=None, encoding=None, errors=None, newline=None):
        """makefile(...) -> an I/O stream connected to the socket

        The arguments are as for io.open() after the filename,
        """
        writing = "w" in mode or "+" in mode
        reading = "r" in mode or (writing and "+" in mode) or not writing
        assert reading or writing, "Must either read or write, or both."
        binary = "b" in mode
        rawmode = ""
        if reading:
            rawmode += "r"
        if writing:
            rawmode += "w"
        raw = SocketIO(self, rawmode)
        self._io_refs += 1
        if buffering is None:
            buffering = -1
        if buffering < 0:
            buffering = io.DEFAULT_BUFFER_SIZE
        if buffering == 0:
            if not binary:
                raise ValueError("unbuffered streams must be binary")
            return raw
        if reading and writing:
            buffer = io.BufferedRWPair(raw, raw, buffering)
        elif reading:
            buffer = io.BufferedReader(raw, buffering)
        else:
            assert writing
            buffer = io.BufferedWriter(raw, buffering)
        if binary:
            return buffer
        text = io.TextIOWrapper(buffer, encoding, errors, newline)
        text.mode = mode
        return text

    def _decref_socketios(self):
        if self._io_refs > 0:
            self._io_refs -= 1
        if self._closed:
            self.close()

    def _real_close(self, _ss=_socket.socket):
        # This function should not reference any globals. See issue #808164.
        _ss.close(self)

    def close(self):
        # This function should not reference any globals. See issue #808164.
        self._closed = True
        if self._io_refs <= 0:
            self._real_close()


if hasattr(_socket, "socketpair"):

    def socketpair(family=None, type=SOCK_STREAM, proto=0):
        """socketpair([family[, type[, proto]]]) -> (socket object, socket object)

        Create a pair of socket objects from the sockets returned by the platform
        socketpair() function.
        The arguments are the same as for socket() except the default family is
        AF_UNIX if defined on the platform; otherwise, the default is AF_INET.
        """
        if family is None:
            try:
                family = AF_UNIX
            except NameError:
                family = AF_INET
        a, b = _socket.socketpair(family, type, proto)
        a = socket(family, type, proto, a.detach())
        b = socket(family, type, proto, b.detach())
        return a, b


_blocking_errnos = ( EAGAIN, EWOULDBLOCK )

class SocketIO(io.RawIOBase):

    """Raw I/O implementation for stream sockets.

    This class supports the makefile() method on sockets.  It provides
    the raw I/O interface on top of a socket object.
    """

    # One might wonder why not let FileIO do the job instead.  There are two
    # main reasons why FileIO is not adapted:
    # - it wouldn't work under Windows (where you can't used read() and
    #   write() on a socket handle)
    # - it wouldn't work with socket timeouts (FileIO would ignore the
    #   timeout and consider the socket non-blocking)

    # XXX More docs

    def __init__(self, sock, mode):
        if mode not in ("r", "w", "rw", "rb", "wb", "rwb"):
            raise ValueError("invalid mode: %r" % mode)
        io.RawIOBase.__init__(self)
        self._sock = sock
        if "b" not in mode:
            mode += "b"
        self._mode = mode
        self._reading = "r" in mode
        self._writing = "w" in mode
        self._timeout_occurred = False

    def readinto(self, b):
        """Read up to len(b) bytes into the writable buffer *b* and return
        the number of bytes read.  If the socket is non-blocking and no bytes
        are available, None is returned.

        If *b* is non-empty, a 0 return value indicates that the connection
        was shutdown at the other end.
        """
        self._checkClosed()
        self._checkReadable()
        if self._timeout_occurred:
            raise IOError("cannot read from timed out object")
        while True:
            try:
                return self._sock.recv_into(b)
            except timeout:
                self._timeout_occurred = True
                raise
            except error as e:
                n = e.args[0]
                if n == EINTR:
                    continue
                if n in _blocking_errnos:
                    return None
                raise

    def write(self, b):
        """Write the given bytes or bytearray object *b* to the socket
        and return the number of bytes written.  This can be less than
        len(b) if not all data could be written.  If the socket is
        non-blocking and no bytes could be written None is returned.
        """
        self._checkClosed()
        self._checkWritable()
        while 1:
            try:
                return self._sock.send(b)
            except error as e:
                if e.args[0] == EINTR:
                    continue
                if e.args[0] in _blocking_errnos:
                    return None
                raise

    def readable(self):
        """True if the SocketIO is open for reading.
        """
        return self._reading and not self.closed

    def writable(self):
        """True if the SocketIO is open for writing.
        """
        return self._writing and not self.closed

    def fileno(self):
        """Return the file descriptor of the underlying socket.
        """
        self._checkClosed()
        return self._sock.fileno()

    @property
    def name(self):
        if not self.closed:
            return self.fileno()
        else:
            return -1

    @property
    def mode(self):
        return self._mode

    def close(self):
        """Close the SocketIO object.  This doesn't close the underlying
        socket, except if all references to it have disappeared.
        """
        if self.closed:
            return
        io.RawIOBase.close(self)
        self._sock._decref_socketios()
        self._sock = None


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

get_fqdn = getfqdn # alias

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



class SafeSocket(socket):
    """A socket protected from interrupted system calls."""
    #accept = systemcall(socket.accept)
    recv = systemcall(socket.recv)
    send = systemcall(socket.send)
    sendall = systemcall(socket.sendall)
    connect = systemcall(socket.connect)
    listen = systemcall(socket.listen)
    bind = systemcall(socket.bind)

CLOSED = 0
CONNECTED = 1
ACCEPTING = 2

class AsyncSocket(socket):
    """Socket with the asyncio modules's async interface."""
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
    """General client connections."""
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
    """Make a TCP client connection."""
    return connect_inet(host, port, SOCK_STREAM, sobject)

def connect_udp(host, port, sobject=SafeSocket):
    """Make a UDP client connection."""
    return connect_inet(host, port, SOCK_DGRAM, sobject)

def connect_unix(path, sobject=SafeSocket):
    """Make a Unix socket stream client connection."""
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
    """return a bound UDP socket."""
    s = sobject(AF_INET, SOCK_DGRAM)
    s.bind(addr)
    return s

def tcp_listener(addr, num=5, sobject=SafeSocket):
    """return a TCP socket, bound and listening."""
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

def inq(sock):
    """How many bytes are still in the kernel's input buffer?"""
    return struct.unpack("I", fcntl.ioctl(sock.fileno(), SIOCINQ, '\0\0\0\0'))[0]

def outq(sock):
    """How many bytes are still in the kernel's output buffer?"""
    return struct.unpack("I", fcntl.ioctl(sock.fileno(), SIOCOUTQ, '\0\0\0\0'))[0]

