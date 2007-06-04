#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

"""\
This module provides socket operations and some related functions.
On Unix, it supports IP (Internet Protocol) and Unix domain sockets.
On other systems, it only supports IP. Functions specific for a
socket are available as methods of the socket object.

Functions:

socket() -- create a new socket object
fromfd() -- create a socket object from an open file descriptor [*]
gethostname() -- return the current hostname
gethostbyname() -- map a hostname to its IP number
gethostbyaddr() -- map an IP number or hostname to DNS info
getservbyname() -- map a service name and a protocol name to a port number
getprotobyname() -- mape a protocol name (e.g. 'tcp') to a number
ntohs(), ntohl() -- convert 16, 32 bit int from network to host byte order
htons(), htonl() -- convert 16, 32 bit int from host to network byte order
inet_aton() -- convert IP addr string (123.45.67.89) to 32-bit packed format
inet_ntoa() -- convert 32-bit packed format IP to string (123.45.67.89)
ssl() -- secure socket layer support (only available if configured)
socket.getdefaulttimeout() -- get the default timeout value
socket.setdefaulttimeout() -- set the default timeout value

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

import os, sys
from _socket import *
from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, \
     ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EADDRNOTAVAIL, EBADF

from pycopia.aid import Enum, systemcall

__all__ = ['SafeSocket', 'AsyncSocket', 'makefile', 'getfqdn', 'get_myaddress',
'opentcp', 'connect_inet', 'connect_tcp', 'connect_udp', 'connect_unix',
'connect_unix_datagram', 'unix_listener', 'udp_listener', 'tcp_listener',
'check_port', 'islocal', 'wait_for_port']

import _socket
__all__.extend([n for n in dir(_socket) if n[0] != '_'])
del _socket



# make the silly name 'error' into global exception 'SocketError'
SocketError = error

HostError = herror

GetAddressInfoError = gaierror

# socket states
CLOSED = Enum(0, "closed")
CONNECTED = Enum(1, "connected")
ACCEPTING = Enum(2, "accepting")


_have_ssl = False
try:
    import _ssl
    from _ssl import *
    _have_ssl = True
except ImportError:
    pass

if _have_ssl:
    __all__.extend([n for n in dir(_ssl) if n[0] != '_'])

_realsocket = socket

if _have_ssl:
    _realssl = ssl
    def ssl(sock, keyfile=None, certfile=None):
        if hasattr(sock, "_sock"):
            sock = sock._sock
        return _realssl(sock, keyfile, certfile)

# WSA error codes
if sys.platform.lower().startswith("win"):
    errorTab = {}
    errorTab[10004] = "The operation was interrupted."
    errorTab[10009] = "A bad file handle was passed."
    errorTab[10013] = "Permission denied."
    errorTab[10014] = "A fault occurred on the network??" # WSAEFAULT
    errorTab[10022] = "An invalid operation was attempted."
    errorTab[10035] = "The socket operation would block"
    errorTab[10036] = "A blocking operation is already in progress."
    errorTab[10048] = "The network address is in use."
    errorTab[10054] = "The connection has been reset."
    errorTab[10058] = "The network has been shut down."
    errorTab[10060] = "The operation timed out."
    errorTab[10061] = "Connection refused."
    errorTab[10063] = "The name is too long."
    errorTab[10064] = "The host is down."
    errorTab[10065] = "The host is unreachable."
    __all__.append("errorTab")


#
# These classes are used by the socket() defined on Windows and BeOS
# platforms to provide a best-effort implementation of the cleanup
# semantics needed when sockets can't be dup()ed.
#
# These are not actually used on other platforms.
#

_socketmethods = (
    'bind', 'connect', 'connect_ex', 'fileno', 'listen',
    'getpeername', 'getsockname', 'getsockopt', 'setsockopt',
    'sendall', 'setblocking',
    'settimeout', 'gettimeout', 'shutdown')

if sys.platform == "riscos":
    _socketmethods = _socketmethods + ('sleeptaskw',)

class _closedsocket(object):
    __slots__ = []
    def _dummy(*args):
        raise error(EBADF, 'Bad file descriptor')
    send = recv = sendto = recvfrom = __getattr__ = _dummy

class _socketobject(object):

    __doc__ = _realsocket.__doc__

#    __slots__ = ["_sock", "send", "recv", "sendto", "recvfrom"]

    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None):
        if _sock is None:
            _sock = _realsocket(family, type, proto)
        self._sock = _sock
        self.send = self._sock.send
        self.recv = self._sock.recv
        self.sendto = self._sock.sendto
        self.recvfrom = self._sock.recvfrom

    def close(self):
        self._sock = _closedsocket()
        self.send = self.recv = self.sendto = self.recvfrom = self._sock._dummy
    close.__doc__ = _realsocket.close.__doc__

    def accept(self):
        sock, addr = self._sock.accept()
        return _socketobject(_sock=sock), addr
    accept.__doc__ = _realsocket.accept.__doc__

    def dup(self):
        """dup() -> socket object

        Return a new socket object connected to the same system resource."""
        return _socketobject(_sock=self._sock)

    def makefile(self, mode='r', bufsize=-1):
        """makefile([mode[, bufsize]]) -> file object

        Return a regular file object corresponding to the socket.  The mode
        and bufsize arguments are as for the built-in open() function."""
        return _fileobject(self._sock, mode, bufsize)

    _s = ("def %s(self, *args): return self._sock.%s(*args)\n\n"
          "%s.__doc__ = _realsocket.%s.__doc__\n")
    for _m in _socketmethods:
        exec _s % (_m, _m, _m, _m)
    del _m, _s

socket = SocketType = _socketobject

class _fileobject(object):
    """Faux file object attached to a socket object."""

    default_bufsize = 8192
    name = "<socket>"

    __slots__ = ["mode", "bufsize", "softspace",
                 # "closed" is a property, see below
                 "_sock", "_rbufsize", "_wbufsize", "_rbuf", "_wbuf"]

    def __init__(self, sock, mode='rb', bufsize=-1):
        self._sock = sock
        self.mode = mode # Not actually used in this version
        if bufsize < 0:
            bufsize = self.default_bufsize
        self.bufsize = bufsize
        self.softspace = False
        if bufsize == 0:
            self._rbufsize = 1
        elif bufsize == 1:
            self._rbufsize = self.default_bufsize
        else:
            self._rbufsize = bufsize
        self._wbufsize = bufsize
        self._rbuf = "" # A string
        self._wbuf = [] # A list of strings

    def _getclosed(self):
        return self._sock is not None
    closed = property(_getclosed, doc="True if the file is closed")

    def close(self):
        try:
            if self._sock:
                self.flush()
        finally:
            self._sock = None

    def __del__(self):
        try:
            self.close()
        except:
            # close() may fail if __init__ didn't complete
            pass

    def flush(self):
        if self._wbuf:
            buffer = "".join(self._wbuf)
            self._wbuf = []
            self._sock.sendall(buffer)

    def fileno(self):
        return self._sock.fileno()

    def write(self, data):
        data = str(data) # XXX Should really reject non-string non-buffers
        if not data:
            return
        self._wbuf.append(data)
        if (self._wbufsize == 0 or
            self._wbufsize == 1 and '\n' in data or
            self._get_wbuf_len() >= self._wbufsize):
            self.flush()

    def writelines(self, list):
        # XXX We could do better here for very long lists
        # XXX Should really reject non-string non-buffers
        self._wbuf.extend(filter(None, map(str, list)))
        if (self._wbufsize <= 1 or
            self._get_wbuf_len() >= self._wbufsize):
            self.flush()

    def _get_wbuf_len(self):
        buf_len = 0
        for x in self._wbuf:
            buf_len += len(x)
        return buf_len

    def read(self, size=-1):
        data = self._rbuf
        if size < 0:
            # Read until EOF
            buffers = []
            if data:
                buffers.append(data)
            self._rbuf = ""
            if self._rbufsize <= 1:
                recv_size = self.default_bufsize
            else:
                recv_size = self._rbufsize
            while True:
                data = self._sock.recv(recv_size)
                if not data:
                    break
                buffers.append(data)
            return "".join(buffers)
        else:
            # Read until size bytes or EOF seen, whichever comes first
            buf_len = len(data)
            if buf_len >= size:
                self._rbuf = data[size:]
                return data[:size]
            buffers = []
            if data:
                buffers.append(data)
            self._rbuf = ""
            while True:
                left = size - buf_len
                recv_size = max(self._rbufsize, left)
                data = self._sock.recv(recv_size)
                if not data:
                    break
                buffers.append(data)
                n = len(data)
                if n >= left:
                    self._rbuf = data[left:]
                    buffers[-1] = data[:left]
                    break
                buf_len += n
            return "".join(buffers)

    def readline(self, size=-1):
        data = self._rbuf
        if size < 0:
            # Read until \n or EOF, whichever comes first
            if self._rbufsize <= 1:
                # Speed up unbuffered case
                assert data == ""
                buffers = []
                recv = self._sock.recv
                while data != "\n":
                    data = recv(1)
                    if not data:
                        break
                    buffers.append(data)
                return "".join(buffers)
            nl = data.find('\n')
            if nl >= 0:
                nl += 1
                self._rbuf = data[nl:]
                return data[:nl]
            buffers = []
            if data:
                buffers.append(data)
            self._rbuf = ""
            while True:
                data = self._sock.recv(self._rbufsize)
                if not data:
                    break
                buffers.append(data)
                nl = data.find('\n')
                if nl >= 0:
                    nl += 1
                    self._rbuf = data[nl:]
                    buffers[-1] = data[:nl]
                    break
            return "".join(buffers)
        else:
            # Read until size bytes or \n or EOF seen, whichever comes first
            nl = data.find('\n', 0, size)
            if nl >= 0:
                nl += 1
                self._rbuf = data[nl:]
                return data[:nl]
            buf_len = len(data)
            if buf_len >= size:
                self._rbuf = data[size:]
                return data[:size]
            buffers = []
            if data:
                buffers.append(data)
            self._rbuf = ""
            while True:
                data = self._sock.recv(self._rbufsize)
                if not data:
                    break
                buffers.append(data)
                left = size - buf_len
                nl = data.find('\n', 0, left)
                if nl >= 0:
                    nl += 1
                    self._rbuf = data[nl:]
                    buffers[-1] = data[:nl]
                    break
                n = len(data)
                if n >= left:
                    self._rbuf = data[left:]
                    buffers[-1] = data[:left]
                    break
                buf_len += n
            return "".join(buffers)

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

    def next(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line


class SafeSocket(_realsocket):
    """A socket protected from interrupted system calls."""
    accept = systemcall(_realsocket.accept)
    recv = systemcall(_realsocket.recv)
    send = systemcall(_realsocket.send)
    sendall = systemcall(_realsocket.sendall)
    connect = systemcall(_realsocket.connect)
    listen = systemcall(_realsocket.listen)
    bind = systemcall(_realsocket.bind)
    # make the socket a bit file-like by itself
    read = systemcall(_realsocket.recv)
    write = systemcall(_realsocket.send)


class AsyncSocket(_realsocket):
    def __init__(self, family, type, proto=0):
        super(AsyncSocket, self).__init__(family, type, proto)
        self._state = CLOSED
        self._buf = ""

    # asyncio interface
    def readable(self):
        return True
        #return self._state == CONNECTED

    def writable(self):
        return (self._state == CONNECTED) and bool(self._buf)

    def priority(self):
        return False

    def handle_read(self):
        if __debug__:
            print >>sys.stderr, "unhandled read"

    def handle_accept(self):
        if __debug__:
            print >>sys.stderr, "unhandled accept"

    def handle_connect(self):
        if __debug__:
            print >>sys.stderr, "unhandled connect"
    
    def handle_hangup(self):
        if __debug__:
            print >>sys.stderr, "unhandled hangup"

    def handle_priority(self):
        if __debug__:
            print >>sys.stderr, "unhandled priority"

    def handle_error(self, ex, val, tb):
        if __debug__:
            print >>sys.stderr, "unhandled error: %s (%s)"  % (ex, val)
        
    # async poller interface
    def handle_read_event(self):
        if self._state == ACCEPTING:
            # for an accepting socket, getting a read implies
            # that we are connected
            self._state = CONNECTED
            self.handle_accept()
        elif self._state == CLOSED:
            self.handle_connect()
            self._state = CONNECTED
            self.handle_read()
        else:
            self.handle_read()

    def handle_write_event(self):
        self._send()

    def handle_priority_event(self):
        if __debug__:
            print >>sys.stderr, "unhandled priority event"

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
            raise SocketError, err

    def accept(self):
        try:
            sa = super(AsyncSocket, self).accept()
        except SocketError, why:
            if why[0] == EWOULDBLOCK:
                pass
            else:
                raise SocketError, why
        return sa

    def recv(self, amt, flags=0):
        while 1:
            try:
                next = super(AsyncSocket, self).recv(amt, flags)
            except SocketError, why:
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
            except SocketError, why:
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


def makefile(sock, mode="r", bufsize=-1):
    fd = os.dup(sock.fileno())
    return os.fdopen(fd, mode, bufsize)



def getfqdn(name=''):
    """Get fully qualified domain name from name.
    An empty argument is interpreted as meaning the local host.

    First the hostname returned by gethostbyaddr() is checked, then
    possibly existing aliases. In case no FQDN is available, hostname
    is returned.
    """
    name = str(name).strip()
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

# probably not the best way to get this info
def get_myaddress():
    """Return my primary IP address."""
    hostname, aliases, ipaddrs = gethostbyaddr(gethostname())
    return ipaddrs[0]

def opentcp(host, port, sobject=SafeSocket):
    msg = "getaddrinfo returns an empty list"
    for res in getaddrinfo(str(host), int(port), 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            sock = sobject(af, socktype, proto)
            sock.connect(sa)
        except error, msg:
            if sock:
                sock.close()
            continue
        break
    if not sock:
        raise error, msg
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
    raise SocketError, "could not connect, no connections found."

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
    except error, err:
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
    except error, err:
        if err[0] == EADDRNOTAVAIL:
            return 0
        else:
            raise
    else:
        s.close()
        return 1

