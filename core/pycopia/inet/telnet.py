#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

"""TELNET client class.

Based on RFC 854: TELNET Protocol Specification, by J. Postel and
J. Reynolds

Example:

>>> from astelnetlib import Telnet
>>> tn = Telnet('www.python.org', 79)   # connect to finger port
>>> tn.write('guido\r\n')
>>> print tn.read_all()
Login       Name               TTY         Idle    When    Where
guido    Guido van Rossum      pts/2        <Dec  2 11:10> snag.cnri.reston..

>>>

Note that read_all() won't read until eof -- it just reads some data
-- but it guarantees to read at least one byte unless EOF is hit.

It is possible to pass a Telnet object to select.select() in order to
wait until more data is available.  Note that in this case,
read_eager() may return '' even if there was data on the socket,
because the protocol negotiation may have eaten the data.  This is why
EOFError is needed in some cases to distinguish between "no data" and
"connection closed" (since the socket also appears ready for reading
when it is closed).

Bugs:
- may hang when connection is slow in the middle of an IAC sequence

"""

# Forked from standard 'telnetlib' 
# TODO: fully convert to asyncio 


import sys

from pycopia import socket
import select

__all__ = ["Telnet", "get_telnet"]

# Tunable parameters
DEBUGLEVEL = 0

# Telnet protocol defaults
TELNET_PORT = 23

# Telnet protocol characters (don't change)
IAC  = chr(255) # "Interpret As Command"
DONT = chr(254)
DO   = chr(253)
WONT = chr(252)
WILL = chr(251)
SB   = chr(250) # sub negotiation
GA =    chr(249) # Go ahead
EL =    chr(248) # Erase Line
EC =    chr(247) # Erase character
AYT =   chr(246) # Are You There
AO =    chr(245) # Abort output
IP =    chr(244) # Interrupt Process
BREAK = chr(243) # NVT character BRK.
DM =    chr(242) # Data Mark. 
                 # The data stream portion of a Synch.
                 # This should always be accompanied by a 
                 # TCP Urgent notification.
NOP =   chr(241) #    No operation.
SE  =   chr(240) #    End of subnegotiation parameters.
IAC2 = IAC+IAC   # double IAC for escaping


# NVT special codes
NULL = chr(0)
BELL = chr(7)
BS  = chr(8)
HT = chr(9)
LF = chr(10)
VT = chr(11)
FF = chr(12)
CR = chr(13)
CRLF = CR+LF
CRNULL = CR+NULL


# Telnet protocol options code (don't change)
# These ones all come from arpa/telnet.h
BINARY = chr(0) # 8-bit data path
ECHO = chr(1) # echo
RCP = chr(2) # prepare to reconnect
SGA = chr(3) # suppress go ahead
NAMS = chr(4) # approximate message size
STATUS = chr(5) # give status
TM = chr(6) # timing mark
RCTE = chr(7) # remote controlled transmission and echo
NAOL = chr(8) # negotiate about output line width
NAOP = chr(9) # negotiate about output page size
NAOCRD = chr(10) # negotiate about CR disposition
NAOHTS = chr(11) # negotiate about horizontal tabstops
NAOHTD = chr(12) # negotiate about horizontal tab disposition
NAOFFD = chr(13) # negotiate about formfeed disposition
NAOVTS = chr(14) # negotiate about vertical tab stops
NAOVTD = chr(15) # negotiate about vertical tab disposition
NAOLFD = chr(16) # negotiate about output LF disposition
XASCII = chr(17) # extended ascii character set
LOGOUT = chr(18) # force logout
BM = chr(19) # byte macro
DET = chr(20) # data entry terminal
SUPDUP = chr(21) # supdup protocol
SUPDUPOUTPUT = chr(22) # supdup output
SNDLOC = chr(23) # send location
TTYPE = chr(24) # terminal type
EOR = chr(25) # end or record
TUID = chr(26) # TACACS user identification
OUTMRK = chr(27) # output marking
TTYLOC = chr(28) # terminal location number
VT3270REGIME = chr(29) # 3270 regime
X3PAD = chr(30) # X.3 PAD
NAWS = chr(31) # window size
TSPEED = chr(32) # terminal speed
LFLOW = chr(33) # remote flow control
LINEMODE = chr(34) # Linemode option
XDISPLOC = chr(35) # X Display Location
OLD_ENVIRON = chr(36) # Old - Environment variables
AUTHENTICATION = chr(37) # Authenticate
ENCRYPT = chr(38) # Encryption option
NEW_ENVIRON = chr(39) # New - Environment variables
# the following ones come from
# http://www.iana.org/assignments/telnet-options
# Unfortunately, that document does not assign identifiers
# to all of them, so we are making them up
TN3270E = chr(40) # TN3270E
XAUTH = chr(41) # XAUTH
CHARSET = chr(42) # CHARSET
RSP = chr(43) # Telnet Remote Serial Port
COM_PORT_OPTION = chr(44) # Com Port Control Option
SUPPRESS_LOCAL_ECHO = chr(45) # Telnet Suppress Local Echo
TLS = chr(46) # Telnet Start TLS
KERMIT = chr(47) # KERMIT
SEND_URL = chr(48) # SEND-URL
FORWARD_X = chr(49) # FORWARD_X
PRAGMA_LOGON = chr(138) # TELOPT PRAGMA LOGON
SSPI_LOGON = chr(139) # TELOPT SSPI LOGON
PRAGMA_HEARTBEAT = chr(140) # TELOPT PRAGMA HEARTBEAT
EXOPL = chr(255) # Extended-Options-List

class Telnet(object):

    """Telnet interface class.

    An instance of this class represents a connection to a telnet
    server.  The instance is initially not connected; the open()
    method must be used to establish a connection.  Alternatively, the
    host name and optional port number can be passed to the
    constructor, too.

    This class has many read_*() methods.  Note that some of them
    raise EOFError when the end of the connection is read, because
    they can return an empty string for other reasons.  See the
    individual doc strings.

    read_all()
        Read all data until EOF; may block.

    read_some()
        Read at least one byte or EOF; may block.

    read_very_eager()
        Read all data available already queued or on the socket,
        without blocking.

    read_eager()
        Read either data already queued or some data available on the
        socket, without blocking.

    read_lazy()
        Read all data in the raw queue (processing it first), without
        doing any socket I/O.

    read_very_lazy()
        Reads all data in the cooked queue, without doing any socket
        I/O.

    """

    def __init__(self, host=None, port=TELNET_PORT, nvt=None, async=0):
        """Constructor.

        When called without arguments, create an unconnected instance.
        With a hostname argument, it connects the instance; a port
        number is optional.

        """
        self.debuglevel = DEBUGLEVEL
        self.sock = None
        self._logfile = None
        self.rawq = ''
        self.irawq = 0
        self.cookedq = ''
        self._rawq = [] # async reads fill this
        self._buf = '' # read() buffer
        self.eof = 0
        self._nvt = nvt or NVT()
        self.death_callback = None
        if host:
            self.open(host, port)

    def open(self, host, port=TELNET_PORT):
        """Connect to a host.

        The optional second argument is the port number, which
        defaults to the standard telnet port (23).

        Don't try to reopen an already connected instance.
        """
        self.eof = 0
        self.host = str(host)
        self.port = int(port)
        self.sock = socket.connect_tcp(self.host, self.port)
        self._nvt.initialize(self)

    def __del__(self):
        """Destructor -- close the connection."""
        self.close()

    def set_logfile(self, lf):
        """Sets the logfile."""
        self._logfile = lf

    def msg(self, msg, *args):
        """Print a debug message, when the debug level is > 0.

        If extra arguments are present, they are substituted in the
        message using the standard string formatting operator.

        """
        if self.debuglevel > 0:
            sew = sys.stderr.write
            sew('Telnet(%s, %d): ' % (self.host, self.port))
            if args:
                sew( msg % args)
            else:
                sew(msg)
            sew("\n")

    def set_debuglevel(self, debuglevel):
        """Set the debug level.
        The higher it is, the more debug output you get (in your logfile).
        """
        self.debuglevel = debuglevel

    def close(self):
        """Close the connection."""
        if self._nvt:
            self._nvt.close()
            self._nvt = None
        if self.sock:
            self.sock.close()
            self.sock = None
        if self.death_callback:
            self.death_callback()
        self.eof = 1

    def interrupt(self):
        self.sock.sendall(IAC+IP)

    def sync(self):
        self.sock.sendall(IAC+DM, socket.MSG_OOB)

    def send_command(self, cmd):
        self.sock.sendall(IAC+cmd)

    def send_option(self, disp, opt):
        self.sock.sendall(IAC+disp+opt)

    def get_socket(self):
        """Return the socket object used internally."""
        return self.sock

    def fileno(self):
        """Return the fileno() of the socket object used internally."""
        return self.sock.fileno()

    def write(self, text):
        """Write a string to the socket, doubling any IAC characters.

        Can block if the connection is blocked.  May raise
        socket.error if the connection is closed.

        """
        if IAC in text:
            text = text.replace(IAC, IAC2)
        if CR in text:
            text = text.replace(CR, CRNULL)
        if LF in text:
            text = text.replace(LF, CRLF)
        self.msg("send %r", text)
        self.sock.sendall(text)

    def read(self, amt=2147483646):
        bs = len(self._buf)
        try:
            while bs < amt:
                if self._rawq:
                    c = self._rawq.pop(0)
                else:
                    c = self.read_some()
                if not c:
                    break
                self._buf += c
                bs = len(self._buf)
        except EOFError:
            pass # let it ruturn rest of buffer
        data = self._buf[:amt]
        self._buf = self._buf[amt:]
        return data

    def read_all(self):
        """Read all data until EOF; block until connection closed."""
        self.process_rawq()
        while not self.eof:
            self.fill_rawq()
            self.process_rawq()
        buf = self.cookedq
        self.cookedq = ''
        return buf

    def read_some(self):
        """Read at least one byte of cooked data unless EOF is hit.

        Return '' if EOF is hit.  Block if no data is immediately
        available.

        """
        self.process_rawq()
        while not self.cookedq and not self.eof:
            self.fill_rawq()
            self.process_rawq()
        buf = self.cookedq
        self.cookedq = ''
        return buf

    def read_very_eager(self):
        """Read everything that's possible without blocking in I/O (eager).

        Raise EOFError if connection closed and no cooked data
        available.  Return '' if no cooked data available otherwise.
        Don't block unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        while not self.eof and self.sock_avail():
            self.fill_rawq()
            self.process_rawq()
        return self.read_very_lazy()

    def read_eager(self):
        """Read readily available data.

        Raise EOFError if connection closed and no cooked data
        available.  Return '' if no cooked data available otherwise.
        Don't block unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        while not self.cookedq and not self.eof and self.sock_avail():
            self.fill_rawq()
            self.process_rawq()
        return self.read_very_lazy()

    def read_lazy(self):
        """Process and return data that's already in the queues (lazy).

        Raise EOFError if connection closed and no data available.
        Return '' if no cooked data available otherwise.  Don't block
        unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        return self.read_very_lazy()

    def read_very_lazy(self):
        """Return any data available in the cooked queue (very lazy).

        Raise EOFError if connection closed and no data available.
        Return '' if no cooked data available otherwise.  Don't block.

        """
        buf = self.cookedq
        self.cookedq = ''
        if not buf and self.eof and not self.rawq:
            raise EOFError, 'telnet connection closed'
        return buf

    def set_nvt(self, nvt):
        self._nvt = nvt

    def set_death_callback(self, callback):
        """Provide a callback function called after each receipt of a telnet option."""
        self.death_callback = callback

    def process_rawq(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.

        """
        buf = ''
        try:
            while self.rawq:
                c = self.rawq_getchar()
                if c in (VT, NULL):
                    continue
                if c != IAC:
                    buf = buf + c
                    continue
                c = self.rawq_getchar()
                if c == IAC:
                    buf = buf + c
                elif c in (DO, DONT, WILL, WONT):
                    opt = self.rawq_getchar()
                    self._nvt.do_option(self, c, opt)
                else:
                    self._nvt.do_command(self, c)
        except EOFError: # raised by self.rawq_getchar()
            pass
        self.cookedq = self.cookedq + buf

    def rawq_getchar(self):
        """Get next char from raw queue.

        Block if no data is immediately available.  Raise EOFError
        when connection is closed.

        """
        if not self.rawq:
            self.fill_rawq()
            if self.eof:
                raise EOFError
        c = self.rawq[self.irawq]
        self.irawq = self.irawq + 1
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        return c

    def fill_rawq(self):
        """Fill raw queue from exactly one recv() system call.

        Block if no data is immediately available.  Set self.eof when
        connection is closed.

        """
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        # The buffer size should be fairly small so as to avoid quadratic
        # behavior in process_rawq() above
        buf = self.sock.recv(50)
        if self._logfile:
            self._logfile.write(buf)
        self.msg("recv %s", `buf`)
        self.eof = (not buf)
        self.rawq = self.rawq + buf

    def sock_avail(self):
        """Test whether data is available on the socket."""
        return select.select([self], [], [], 0) == ([self], [], [])

    def interact(self):
        self._nvt.interact(self)


class NVT(object):
    """Base class for TELNET terminals. Implements the basic
NVT. May be subclassed if more elaborate terminals are required. Defines the
available TELNET options. The instance must be callable, as it is called by
the Telnet object for option negotiation.  """
    OPTIONS = {
        SGA: WILL,
        LINEMODE: WILL,
    }

    def __init__(self, inf=None, outf=None):
        self._inf = inf or sys.stdin
        self._outf = outf or sys.stdout
        self._commands = {IP: self._do_IP,
                }

    def initialize(self, tn):
        """Called when telnet session first opened."""
        for opt, disp in self.OPTIONS.items():
            tn.send_option(DO, opt)

    def do_option(self, tn, c, opt):
        """Called for each option negotiation."""
        if c in (DO, DONT):
            resp = self.OPTIONS.get(opt, WONT)
            tn.sock.sendall(IAC + resp + opt)
        elif c in (WILL, WONT):
            resp = self.OPTIONS.get(opt, DONT)
            tn.sock.sendall(IAC + resp + opt)

    def do_command(self, tn, c):
        """Called when receiving a telnet command."""
        meth = self._commands.get(c, self._do_default)
        meth(tn)

    def _do_default(self, tn):
        tn.msg("unhandled command recieved.")

    def _do_IP(self, tn):
        tn.close()
        sys.exit(1)

    def close(self):
        self._inf = None
        self._outf = None

    def interact(self, tn):
        """Interaction function, emulates a very dumb telnet client."""
        tnfd = tn.fileno()
        inffd = self._inf.fileno()
        while 1:
            rfd, wfd, xfd = select.select([tnfd, inffd], [], [])
            if tnfd in rfd:
                try:
                    text = tn.read_eager()
                except EOFError:
                    print '*** Connection closed by remote host ***'
                    break
                if text:
                    self._outf.write(text)
                    self._outf.flush()
            if inffd in rfd:
                line = self._inf.readline()
                if not line:
                    break
                tn.write(line)


def get_telnet(host, port=TELNET_PORT, nvt=None, async=0):
    return Telnet(host, port, nvt, async)

def test():
    debuglevel = 0
    while sys.argv[1:] and sys.argv[1] == '-d':
        debuglevel = debuglevel+1
        del sys.argv[1]
    host = 'localhost'
    if sys.argv[1:]:
        host = sys.argv[1]
    port = TELNET_PORT
    if sys.argv[2:]:
        portstr = sys.argv[2]
        try:
            port = int(portstr)
        except ValueError:
            port = socket.getservbyname(portstr, 'tcp')
    tn = Telnet()
    tn.set_debuglevel(debuglevel)
    tn.open(host, port)
    tn.interact()
    tn.close()

if __name__ == '__main__':
    #test()
    host = "localhost"
    prompt = "%s>" % (host)
    sess = Telnet()
    sess.set_debuglevel(9)
    sess.open(host)
    pass


