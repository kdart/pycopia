#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""TELNET client module.

Forked from telnetlib and modified to better fit into Pycopia framework, such
as having an API that works with an Expect object, and common logging.

These days telnet is mainly used for serial console server access. So this code
adds some features for that purpose. It adds some RFC 2217 features for serial
port control and monitoring.

This module also supports in-band file uploads by use of the ZMODEM protocol.
This requires the software package named "lrzsz" to be installed on both ends.
"""


import sys
import os
import struct

from pycopia import logging
from pycopia import socket
from pycopia.OS.exitstatus import ExitStatus


__all__ = ["Telnet", "get_telnet"]

# Telnet protocol defaults
TELNET_PORT = 23

# Telnet protocol characters (don't change)
IAC   = chr(255) # "Interpret As Command"
DONT  = chr(254) # 0xfe
DO    = chr(253) # 0xfd
WONT  = chr(252) # 0xfc
WILL  = chr(251) # 0xfb
SB    = chr(250) # sub negotiation 0xfa
GA    = chr(249) # Go ahead
EL    = chr(248) # Erase Line
EC    = chr(247) # Erase character
AYT   = chr(246) # Are You There
AO    = chr(245) # Abort output
IP    = chr(244) # Interrupt Process
BREAK = chr(243) # NVT character BRK.
DM    = chr(242) # Data Mark.
                 # The data stream portion of a Synch.
                 # This should always be accompanied by a TCP Urgent notification.
NOP   = chr(241) # No operation.
SE    = chr(240) # End of subnegotiation parameters.

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
NOOPT = chr(0)


# COM control sub commands, RFC 2217
SET_BAUDRATE        =  chr(1)
SET_DATASIZE        =  chr(2)
SET_PARITY          =  chr(3)
SET_STOPSIZE        =  chr(4)
SET_CONTROL         =  chr(5)
NOTIFY_LINESTATE    =  chr(6)
NOTIFY_MODEMSTATE   =  chr(7)
FLOWCONTROL_SUSPEND =  chr(8)
FLOWCONTROL_RESUME  =  chr(9)
SET_LINESTATE_MASK  =  chr(10)
SET_MODEMSTATE_MASK =  chr(11)
PURGE_DATA          =  chr(12)

RESP_SET_BAUDRATE        =  chr(101)
RESP_SET_DATASIZE        =  chr(102)
RESP_SET_PARITY          =  chr(103)
RESP_SET_STOPSIZE        =  chr(104)
RESP_SET_CONTROL         =  chr(105)
RESP_NOTIFY_LINESTATE    =  chr(106)
RESP_NOTIFY_MODEMSTATE   =  chr(107)
RESP_FLOWCONTROL_SUSPEND =  chr(108)
RESP_FLOWCONTROL_RESUME  =  chr(109)
RESP_SET_LINESTATE_MASK  =  chr(110)
RESP_SET_MODEMSTATE_MASK =  chr(111)
RESP_PURGE_DATA          =  chr(112)


class TelnetError(Exception):
    pass

class BadConnectionError(TelnetError):
    pass


class Telnet(object):

    def __init__(self, host=None, port=TELNET_PORT, logfile=None):
        """A telnet connection.
        """
        self._logfile = logfile
        self.reset()
        if host:
            self.open(host, port)

    def __enter__(self):
        return self

    def __exit__(self, extype, exvalue, traceback):
        self.close()
        return False

    def __str__(self):
        return "Telnet({!r:s}, {:d}): {} ({})".format(self.host, self.port,
                "open" if not self.eof else "closed",
                "binary" if self._binary else "nonbinary",
                )

    def open(self, host, port=TELNET_PORT):
        """Open a conneciton to a host.
        """
        if not self.sock:
            self.host = str(host)
            self.port = int(port)
            self.sock = socket.connect_tcp(self.host, self.port, socket.socket) # interruptable socket
            self._sendall(
                        IAC + DO + BINARY +
                        IAC + DO + SGA +
                        IAC + DONT + ECHO +
                        IAC + WILL + COM_PORT_OPTION
                        )
            self._fill_rawq(12)
            self._process_rawq()
            self._closed = 0
            self.eof = 0

    def set_logfile(self, lf):
        self._logfile = lf

    def fileno(self):
        """Return the fileno() of the socket object used internally."""
        return self.sock.fileno()

    def close(self):
        if self.sock:
            self.sock.close()
            self.reset()
        self.eof = 1

    def reset(self):
        self.sock = None
        self.eof = 0
        self._closed = 1
        self._rawq = ''
        self._q = ''
        self._qi = 0
        self._irawq = 0
        self.iacseq = '' # Buffer for IAC sequence.
        self.sb = 0 # flag for SB and SE sequence.
        self.sbdataq = ''
        self._binary = False
        self._sga = False
        self._do_com = False
        self._linestate = None
        self._modemstate = None
        self._suspended = False

    linestate = property(lambda self: self._linestate)
    modemstate = property(lambda self: self._modemstate)
    closed = property(lambda self: self._closed)

    def write(self, text):
        """Write a string to the socket, doubling any IAC characters.

        Can block if the connection is blocked.  May raise
        socket.error if the connection is closed.
        """
        if IAC in text:
            text = text.replace(IAC, IAC2)
        if self._logfile:
            self._logfile.write("   ->: {!r}\n".format(text))
        self.sock.sendall(text)

    def read(self, amt):
        while not self._q:
            self._fill_rawq()
            self._process_rawq()
        d = self._q[self._qi:self._qi+amt]
        self._qi += amt
        if self._qi >= len(self._q):
            self._q = ''
            self._qi = 0
        return d

    def _fill_rawq(self, n=256):
        if self._irawq >= len(self._rawq):
            self._rawq = ''
            self._irawq = 0
        buf = self.sock.recv(n)
        if self._logfile:
            self._logfile.write("<-{0:003d}: {1!r:s}\n".format(len(buf), buf))
        self.eof = (not buf)
        self._rawq += buf

    def _rawq_getchar(self):
        if not self._rawq:
            self._fill_rawq()
            if self.eof:
                raise EOFError("No data received")
        c = self._rawq[self._irawq]
        self._irawq += 1
        if self._irawq >= len(self._rawq):
            self._rawq = ''
            self._irawq = 0
        return c

    def _process_rawq(self):
        buf = ['', ''] # data buffer and SB buffer
        try:
            while self._rawq:
                c = self._rawq_getchar()
                if not self.iacseq:
                    if c == NULL:
                        continue
                    if c == "\021":
                        continue
                    if c != IAC:
                        buf[self.sb] += c
                        continue
                    else:
                        self.iacseq += c
                elif len(self.iacseq) == 1:
                    if c in (DO, DONT, WILL, WONT):
                        self.iacseq += c
                        continue

                    self.iacseq = ''
                    if c == IAC:
                        buf[self.sb] += c
                    else:
                        if c == SB: # SB ... SE start.
                            self.sb = 1
                            self.sbdataq = ''
                        elif c == SE:
                            self.sb = 0
                            self.sbdataq += buf[1]
                            buf[1] = ''
                            self._suboption()
                        else:
                            logging.warning('Telnet: IAC {!r} not recognized'.format(c))
                elif len(self.iacseq) == 2:
                    cmd = self.iacseq[1]
                    self.iacseq = ''
                    if cmd in (DO, DONT, WILL, WONT):
                        self._neg_option(cmd, c)
                    else:
                        logging.error("telnet bad command: {!r}".format(cmd))
        except EOFError:
            self.iacseq = '' # Reset on EOF
            self.sb = 0
        self._q += buf[0]
        self.sbdataq += buf[1]

    def _sendall(self, data, opt=0):
        if self._logfile:
            self._logfile.write("cmd->: {!r}\n".format([ord(c) for c in data]))
        self.sock.sendall(data, opt)

    def _neg_option(self, cmd, opt):
        if cmd == DO: # 0xfd
            if opt == BINARY:
                self._sendall(IAC + WILL + BINARY)
            elif opt == SGA:
                self._sendall(IAC + WILL + SGA)
            elif opt == COM_PORT_OPTION:
                self._do_com = True
                # Don't bother us with modem state changes
                self._sendall(IAC+SB+COM_PORT_OPTION+SET_MODEMSTATE_MASK+"\x00"+IAC+SE)
            else:
                self._sendall(IAC + WONT + opt)
        elif cmd == WILL:
            if opt == BINARY:
                self._binary = True
            elif opt == SGA:
                self._sga = True
            elif opt == COM_PORT_OPTION:
                self._do_com = True
            else:
                self._sendall(IAC + DONT + opt)
        elif cmd == DONT:
            if opt in (BINARY, SGA):
                raise BadConnectionError("Server doesn't want binary connection.")
            else:
                self._sendall(IAC + WONT + opt)
        elif cmd == WONT:
            if opt in (BINARY, SGA):
                raise BadConnectionError("Could not negotiate binary path.")

    def _suboption(self):
        subopt = self.sbdataq
        self.sbdataq = ''
        if len(subopt) != 3:
            logging.error("Bad suboption recieved: {!r}".format(subopt))
            return
        if subopt[0] == COM_PORT_OPTION:
            comopt = subopt[1]
            if comopt == RESP_NOTIFY_LINESTATE:
                value = subopt[2]
                self._linestate = LineState(subopt[2])
            elif comopt == RESP_NOTIFY_MODEMSTATE:
                self._modemstate = ModemState(subopt[2])
            elif comopt == RESP_FLOWCONTROL_SUSPEND:
                self._suspended = True
                logging.warning("Telnet: requested to suspend tx.")
            elif comopt == RESP_FLOWCONTROL_RESUME:
                self._suspended = False
                logging.warning("Telnet: requested to resume tx.")
            else:
                logging.warning("Telnet: unhandled COM opton: {}".format(repr(subopt)))
        else:
            logging.warning("Telnet: unhandled subnegotion: {}".format(repr(subopt)))

    def interrupt(self):
        self._sendall(IAC + IP)
        self.sync()

    def sync(self):
        self._sendall(IAC + DM, socket.MSG_OOB)
        self._process_rawq()

    def send_command(self, cmd):
        self._sendall(IAC+cmd)

    def send_option(self, disp, opt):
        self._sendall(IAC + disp + opt)

    def set_baud(self, rate):
        self.send_com_option(SET_BAUDRATE, struct.pack("!I", rate))

    def send_com_option(self, opt, value):
        if self._do_com:
            self._sendall(IAC + SB + COM_PORT_OPTION + opt + value + IAC + SE)
        else:
            raise TelnetError("Use of COM option when not negotiated.")

    def upload_zmodem(self, filename):
        """Call external ZMODEM program to upload a file.
        Return an ExitStatus object that should indicate success or failure.
        """
        sockfd = self.sock.fileno()
        pread, pwrite = os.pipe()
        pid = os.fork()
        if pid == 0: # child
            os.dup2(sockfd, 0)
            os.dup2(sockfd, 1)
            os.dup2(pwrite, 2)
            os.close(pread)
            os.close(pwrite)
            for fd in xrange(3,64):
                try:
                    os.close(fd)
                except:
                    pass
            os.write(0, "rz -e -q -s +30\r") # needed with -e flag on sz
            os.execlp("sz", "sz", "-e", "-q", "-y", "-L", "128", filename)
            os._exit(1) # not normally reached
        # parent
        os.close(pwrite)
        while True:
            wpid, es = os.waitpid(pid, 0)
            if wpid == pid:
                break
        errout = os.read(pread, 4096)
        es = ExitStatus("sz {}".format(filename), es)
        es.output = errout
        return es

    def upload(self, filename):
        """Basic upload using cat.
        """
        text = open(filename).read()
        sockfd = self.sock.fileno()
        os.write(sockfd, "cat - > {}\r".format(os.path.basename(filename)))
        os.write(sockfd, text)
        os.write(sockfd, "\r" + chr(4))
        return ExitStatus("cat", 0) # fake exitstatus to be compatible with upload_zmodem.

    # asyncio interface TODO
    def readable(self):
        return True

    def writable(self):
        return False

    def priority(self):
        return True

    def read_handler(self):
        self._fill_rawq()
        self._process_rawq()

    def write_handler(self):
        pass

    def pri_handler(self):
        logging.warning("Telnet: unhandled pri event")

    def hangup_handler(self):
        logging.warning("Telnet: unhandled hangup event")

    def error_handler(self):
        logging.warning("Telnet: unhandled error")

    def exception_handler(self, ex, val, tb):
        logging.error("Telnet poller error: {} ({})".format(ex, val))


class LineState(object):

    def __init__(self, code):
        code = ord(code)
        self.timeouterror = code & 128
        self.transmit_shift_register_empty = code & 64
        self.transmit_holding_register_empty = code & 32
        self.break_detect_error = code & 16
        self.framing_error = code & 8
        self.parity_error = code & 4
        self.overrun_error = code & 2
        self.data_ready = code & 1


class ModemState(object):
    def __init__(self, code):
        code = ord(code)
        self.carrier_detect = bool(code & 128)
        self.ring_indicator = bool(code & 64)
        self.dataset_ready = bool(code & 32)
        self.clear_to_send = bool(code & 16)
        self.delta_rx_detect = bool(code & 8)
        self.ring_indicator = bool(code & 4)
        self.delta_dataset_ready = bool(code & 2)
        self.delta_clear_to_send = bool(code & 1)

    def __str__(self):
        return """ModemState:
         carrier_detect: {}
         ring_indicator: {}
          dataset_ready: {}
          clear_to_send: {}
        delta_rx_detect: {}
         ring_indicator: {}
    delta_dataset_ready: {}
    delta_clear_to_send: {}
        """.format(
            self.carrier_detect,
            self.ring_indicator,
            self.dataset_ready,
            self.clear_to_send,
            self.delta_rx_detect,
            self.ring_indicator,
            self.delta_dataset_ready,
            self.delta_clear_to_send,
            )


def get_telnet(host, port=TELNET_PORT, logfile=None):
    return Telnet(host, port, logfile)


if __name__ == '__main__':
    from pycopia import autodebug
    from pycopia import expect
    logging.loglevel_debug()
    host = "venus"
    port = 6001
    prompt = "$ "
    tn = Telnet(host, port)#, logfile=sys.stderr)
    sess = expect.Expect(tn, prompt=prompt)
    sess.write("\r")
    sess.expect("login:")
    sess.send("tester\r")
    sess.expect("assword:")
    sess.send("testme\r")
    sess.wait_for_prompt()
    print(sess.fileobject().upload("/etc/hosts"))
    sess.send_slow("exit\r")
    print("linestate:", tn.linestate)
    print("modemstate:", tn.modemstate)
    sess.close()


