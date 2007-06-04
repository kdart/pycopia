#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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
Interface to the vgetty voice library.

"""

import sys, os
import signal
SIGPIPE = signal.SIGPIPE 
from errno import EINTR

from pycopia import scheduler
from pycopia.UserFile import FileWrapper
from pycopia.aid import Queue, IF


class VgettyError(Exception):
    pass

class VChatError(VgettyError):
    pass

class VExpectError(VgettyError):
    pass

# used to pass async events up to action methods.
class _AsyncEvent(VgettyError):
    pass

EVENTS = """BONG_TONE BUSY_TONE CALL_WAITING DIAL_TONE
        DATA_CALLING_TONE DATA_OR_FAX_DETECTED FAX_CALLING_TONE
        HANDSET_ON_HOOK LOOP_BREAK LOOP_POLARITY_CHANGE NO_ANSWER
        NO_CARRIER
        NO_DIAL_TONE NO_VOICE_ENERGY RING_DETECTED RINGBACK_DETECTED
        RECEIVED_DTMF SILENCE_DETECTED SIT_TONE TDD_DETECTED
        VOICE_DETECTED UNKNOWN_EVENT""".split()

class CallProgram(object):
    def __init__(self, logfile=None):
        self._q = Queue()
        self._device = None
        self._autostop = False
        self._state = "IDLE"
        self.sched = scheduler.get_scheduler()
        # FileWrapper protects against interrupted system call
        self._in = FileWrapper(os.fdopen(int(os.environ["VOICE_INPUT"]), "r", 1))
        self._out = FileWrapper(os.fdopen(int(os.environ["VOICE_OUTPUT"]), "w", 0))
        self._ppid = int(os.environ["VOICE_PID"])
        self._program = os.environ["VOICE_PROGRAM"]
        # modem login variables
        self.caller_id = os.environ.get("CALLER_ID")
        self.caller_name = os.environ.get("CALLER_NAME")
        self.called_id = os.environ.get("CALLED_ID")
        self.connectstring = os.environ.get("CONNECT")
        self._device = os.environ.get("DEVICE")

        self._log = logfile
        if self._log:
            self._log.write("-----------\n### Starting %s\n----------\n" % (self.__class__.__name__,))
        self.EVENT_DISPATCH = {}
        for ename in EVENTS:
            self.EVENT_DISPATCH[ename] = []
        self.chat(['HELLO SHELL', 'HELLO VOICE PROGRAM', 'READY'])
        # for easy subclass initialization
        self.initialize()


    def __del__(self):
        self.close()

    def register(self, evname, handler):
        """Register an event handler. The event name is one from the EVENTS
        list. The handler should be a callable."""
        assert evname in EVENTS, "bad event name"
        if callable(handler):
            self.EVENT_DISPATCH[evname].append(handler)
        else:
            raise ValueError, "register: handler must be callable"

    def unregister(self, evname, handler):
        hlist = self.EVENT_DISPATCH[evname]
        try:
            hlist.remove(handler)
        except ValueError:
            pass

    def initialize(self):
        """For subclasses to add extra initialization."""
        pass

    def log(self, entrytype, entry):
        if self._log:
            self._log.write("%s: %r\n" % (entrytype, entry))

    def _timeout_cb(self):
        self._timed_out = 1

    def _receive(self):
        self._timed_out = 0
        ev = self.sched.add(60, 0, self._timeout_cb, ())
        try:
            while True:
                try:
                    data = self._in.readline()
                except EnvironmentError, why:
                    if why.errno == EINTR:
                        if self._timed_out == 1:
                            raise TimeoutError, "timed out during recieve."
                        else:
                            continue
                    else:
                        raise
                else:
                    break
        finally:
            self.sched.remove(ev)
        data = data.strip()
        self._state = data
        self.log("RCV", data)
        return data

    def receive(self):
        while True:
            if self._q:
                data = self._q.pop()
            else:
                data = self._receive()
            hlist = self.EVENT_DISPATCH.get(data, None) # checks if event type
            if hlist is None: # not an event
                return data
            else:
                raise _AsyncEvent, (data, hlist)

    def _run_handlers(self, args):
        hlist = args[1]
        if not hlist:
            self.log("EVENT", args[0])
        for handler in hlist:
            self.log("CALL", handler)
            handler()
        if self._autostop:
            self._state = "IDLE"
        self.log("STATE", self._state)

    def send(self, data):
        while 1:
            try:
                self._out.write("%s\n" % (data,))
            except EnvironmentError, why:
                if why.errno == EINTR:
                    continue
                else:
                    raise
            else:
                break
        os.kill(self._ppid, SIGPIPE)
        self.log("SND", data)

    def expect(self, *args):
        self.log("EXP", str(args))
        ev = self.receive()
        try:
            i = list(args).index(ev)
        except ValueError:
            raise VExpectError, "unexected expect value: %r" % (ev,)
        return i

    def chat(self, chatscript):
        receiving = 0
        for cmd in chatscript:
            receiving ^= 1
            if receiving:
                if cmd == '':
                    continue
                self.expect(cmd)
            else:
                self.send(cmd)

    def enable_events(self):
        """Enables event reporting to the shell (dtmf codes, data/fax
                calling tones, silence, quiet)"""
        self.chat(['', 'ENABLE EVENTS', 'READY'])

    def disable_events(self):
        """Disables event reporting to the shell."""
        self.chat(['', 'DISABLE EVENTS', 'READY'])

    def device(self, modemdev):
        """This command sets the device that vgetty will use."""
        self.send("DEVICE %s" % (modemdev,))
        i = self.expect("READY", "DEVICE_NOT_AVAILABLE", "ERROR")
        if i == 0:
            self._device = modemdev
        elif i == 1:
            self._device = None
            raise VgettyError, "device %r not supported" % (modemdev,)
        elif i == 2:
            self._device = None
            raise VgettyError, "device: unknown error"
    # possible values for device() method.
    NO_DEVICE = "NO_DEVICE"
    DIALUP_LINE = "DIALUP_LINE"
    INTERNAL_MICROPHONE = "INTERNAL_MICROPHONE" 
    EXTERNAL_MICROPHONE = "EXTERNAL_MICROPHONE" 
    INTERNAL_SPEAKER = "INTERNAL_SPEAKER"
    LOCAL_HANDSET = "LOCAL_HANDSET"
    EXTERNAL_SPEAKER = "EXTERNAL_SPEAKER"
    DIALUP_WITH_INT_SPEAKER = "DIALUP_WITH_INT_SPEAKER"
    DIALUP_WITH_EXT_SPEAKER = "DIALUP_WITH_EXT_SPEAKER" 
    DIALUP_WITH_INTERNAL_MIC_AND_SPEAKER = "DIALUP_WITH_INTERNAL_MIC_AND_SPEAKER" 
    DIALUP_WITH_EXTERNAL_MIC_AND_SPEAKER = "DIALUP_WITH_EXTERNAL_MIC_AND_SPEAKER" 
    DIALUP_WITH_LOCAL_HANDSET = "DIALUP_WITH_LOCAL_HANDSET"

    def beep(self, freq=None, duration=None):
        """Sends a beep through the chosen device (if frequency or
        length are not given, the defaults from voice.conf are used)"""
        if duration and freq:
            self.send("BEEP %s %s" % (freq, duration))
        elif freq:
            self.send("BEEP %s" % (freq,))
        else:
            self.send("BEEP")
        i = self.expect("BEEPING", "ERROR")
        if i == 0:
            i = self.expect("READY", "ERROR")
            if i == 0:
                return True 
            else:
                raise VgettyError, "beep: failed to beep"
        elif i == 1:
            raise VgettyError, "beep: unknown error"

    def get_tty(self):
        """Returns the modem device currently in use."""
        self.send("GET TTY")
        tty = self._receive()
        self.expect("READY")
        return tty

    def get_modem(self):
        """Returns the voice modem driver name, for example "US Robotics", see
        ../libvoice/*.c, at the end of the file (the big structure). Then
        returns "READY".  The goal of this function is to for example choose
        the right RMD file format to pass for PLAY."""
        self.send("GET MODEM")
        name = self._receive()
        self.expect("READY")
        return name

    def autostop(self, on=True):
        """With AUTOSTOP on, the voicelib will automatically abort a play in
        progress and return READY. This is useful for faster reaction times for
        voice menus."""
        self.chat(["", "AUTOSTOP %s" % (IF(on, "ON", "OFF"),), "READY"])
        self._autostop = bool(on)

    def close(self):
        """Stops conversation with the voice lib."""
        try:
            self.chat(["", "GOODBYE", "GOODBYE SHELL"])
        except _AsyncEvent, event:
            self._run_handlers(event.args)
        self._in.close() ; self._in = None
        self._out.close() ; self._out = None
        self.log("CLOSE", "session closed")

    def stop(self):
        """Stops current action (DIALING, PLAYING, RECORDING or WAITING)
        Current state will be IDLE. ( Please note, that events will NOT be
        reported after "STOP" . If you don't want to do anything but to detect
        events, then try the WAIT command."""
        self._state = "IDLE"
        try:
            self.chat(["", "STOP", "READY"])
            return True
        except _AsyncEvent, event:
            # ignore events during a STOP
            return False

    def dtmf(self, number):
        """Support for sending DTMFs over the voice modem from the voice shell.
        The argument is the DTMFs to dial. This can be used for example to use
        vgetty as a voice-mailbox poller."""
        self.send("DTMF %s" % (number,))
        i = self.expect("READY", "DTMFING", "ERROR")
        if i == 0:
            raise VgettyError, "dtmf: unexpected READY"
        elif i == 1:
            i = self.expect("READY", "ERROR")
            if i == 0:
                return True
            elif i == 1:
                self.expect("READY")
                raise VgettyError, "dtmf: failed to dtmf"
        elif i == 2:
            raise VgettyError, "dtmf: unknown error"

    def quote(self, modemcommand):
        """This adds support for sending modem-specific raw AT commands to the
        voice modem from the voice shell. The argument is the command to issue.
        Please do not use this lightly since it makes your voice shell script
        modem dependant."""
        self.send("QUOTE %s" % (modemcommand,))
        i = self.expect("READY", "ERROR")
        if i == 0:
            return True
        elif i == 1:
            raise VgettyError, "quote: modem reported an error"

    def getfax(self):
        """For receiving a FAX."""
        self.send("GETFAX")
        i = self.expect("READY", "RECEIVING", "ERROR")
        if i == 0:
            raise VgettyError, "getfax: unexpected READY"
        elif i == 1:
            i = self.expect("READY", "ERROR")
            if i == 0:
                return True
            elif i == 1:
                raise VgettyError, "getfax: failed to get fax"
        elif i == 2:
            raise VgettyError, "getfax: unknown error"

    def sendfax(self, params):
        """For sending a FAX."""
        self.send("SENDFAX %s" % (params,))
        i = self.expect("READY", "ERROR")
        if i == 0:
            return True
        elif i == 1:
            raise VgettyError, "sendfax: failed to send fax"

    # operations that can get async events
    def play(self, fname, linger=0):
        """Plays filename through the chosen device (the file must be in
        your modem's format!!! See section 7). Use 'linger' with autostop on
        for better DTMF performance."""
        self.send("PLAY %s %d" % (fname, linger))
        while True: 
            try:
                i = self.expect("PLAYING", "ERROR")
            except _AsyncEvent, event:
                self._run_handlers(event.args)
                if self._autostop:
                    return False
                else:
                    continue
            else:
                break
        if i == 0: # playing
            while True:
                try:
                    i = self.expect("READY", "ERROR")
                    if i == 0:
                        return True
                    elif i == 1:
                        raise VgettyError, "ERROR during play"
                except _AsyncEvent, event:
                    self._run_handlers(event.args)
                    if self._autostop or self._state == "IDLE":
                        return False
                    else:
                        self._state = "PLAYING"
                        continue
        elif i == 1:
            raise VgettyError, "ERROR before play"

    def record(self, fname):
        """Records filename from the chosen device (recorded file will be
        in your modem's format!)"""
        self.send("RECORD %s" % (fname,))
        try:
            i = self.expect("RECORDING", "ERROR")
        except _AsyncEvent, event:
            self._run_handlers(event.args)
            return False
        if i == 0: # recording
            while True:
                try:
                    i = self.expect("READY", "ERROR")
                    if i == 0:
                        return True
                    elif i == 1:
                        self.expect("READY")
                        raise VgettyError, "ERROR while recording"
                except _AsyncEvent, event:
                    self._run_handlers(event.args)
                    if self._state in ("IDLE", "READY"):
                        break
                    else:
                        self._state = "RECORDING"
                        continue
        elif i == 1:
            raise VgettyError, "ERROR before recording"

    def dial(self, number):
        """Dials the given number."""
        self.send("DIAL %s" % (number,))
        try:
            i = self.expect("DIALING", "ERROR")
        except _AsyncEvent, event:
            self._run_handlers(event.args)
            return False
        if i == 0:
            try:
                i = self.expect("READY", "ERROR")
                if i == 0:
                    return True
                elif i == 1:
                    raise VgettyError, "ERROR during dialing"
            except _AsyncEvent, event:
                self._run_handlers(event.args)
                return False
        elif i == 1:
            raise VgettyError, "error before dialing"

    def wait(self, secs):
        """Waits for 'seconds' seconds. During waiting, events will be
        detected and reported!"""
        self.send("WAIT %s" % (secs,))
        while True: 
            try:
                i = self.expect("WAITING", "ERROR")
            except _AsyncEvent, event:
                self._run_handlers(event.args)
                continue
            else:
                break
        if i == 0:
            while True:
                try:
                    i = self.expect("READY", "ERROR")
                    if i == 0:
                        return True
                    elif i == 1:
                        self.expect("READY") # no more events after this.
                        raise VgettyError, "ERROR during wait"
                except _AsyncEvent, event:
                    self._run_handlers(event.args)
                    self._state = "WAITING"
                    continue
        elif i == 1:
            raise VgettyError, "ERROR before wait"

    def duplex(self, sendfile, recfile):
        """Duplex playback and record.  """
        self.send("DUPLEX %s %s" % (sendfile, recfile))
        try:
            i = self.expect("DUPLEXMODE", "ERROR")
        except _AsyncEvent, event:
            self._run_handlers(event.args)
            return False
        if i == 0: # duplex
            while True:
                try:
                    i = self.expect("READY", "ERROR")
                    if i == 0:
                        return True
                    elif i == 1:
                        self.expect("READY")
                        raise VgettyError, "ERROR while recording in duplex mode"
                except _AsyncEvent, event:
                    self._run_handlers(event.args)
                    if self._state in ("IDLE", "READY"):
                        break
                    else:
                        self._state = "DUPLEXMODE"
                        continue
        elif i == 1:
            raise VgettyError, "ERROR before duplex mode"


    # asyncio interface
    def fileno(self):
        return self._in.fileno()

    def handle_read_event(self):
        inp = self._receive()
        self._q.append(inp)


# basic call program that works like the default vgetty one.
class BasicCallProgram(CallProgram):
    def initialize(self):
        self.enable_events()
        self._do_dtmf = self._default_dtmf_handler
        self._dtmf = [] 
        self.register("RECEIVED_DTMF", self._handle_dtmf)

        signal.signal(signal.SIGHUP, self._quit)
        signal.signal(signal.SIGINT, self._quit)
        signal.signal(signal.SIGQUIT, self._quit)
        signal.signal(signal.SIGTERM, self._quit)
        self.register('LOOP_BREAK', self._end)
        self.register('BUSY_TONE', self._end)
        self.register('DIAL_TONE', self._end)
        self.register('SILENCE_DETECTED', self._end)
        self.register('NO_VOICE_ENERGY', self._end)

        self.register("DATA_CALLING_TONE", self._do_data)
        self.register("FAX_CALLING_TONE", self._do_fax)

    def set_dtmf_handler(self, handler=None):
        if handler and callable(handler):
            self._do_dtmf = handler

    def _default_dtmf_handler(self, dtmflist):
        self.log("DTMF", dtmflist)

    def _handle_dtmf(self):
        digit = self._receive()
        self.log("DTMF", digit)
        if digit == "*":
            self._dtmf = [] 
            if self._state == "PLAYING" and not self._autostop:
                self.stop()
        elif digit == "#":
            self.stop()
            if self._do_dtmf:
                self._do_dtmf(self._dtmf)
        else:
            self._dtmf.append(digit)

    def _end(self):
        self.stop()

    def _quit(self, sig, stack):
        self.log("SIG", sig)
        try:
            if self._state.endswith("ING"):
                self.stop()
            self.close()
        except IOError:
            pass
        raise SystemExit, 0

    def _do_data(self):
        self.stop()
        raise SystemExit, 1

    def _do_fax(self):
        self.stop()
        raise SystemExit, 2


# a very basic answering machine function
def answering_machine(config, logfile=None, dtmf_handler=None):
    import time
    inname = os.path.join(config.VOICEDIR, config.SPOOLDIR, "v-%s.rmd" % (int(time.time()),))
    greeting = os.path.join(config.VOICEDIR, config.MESSAGEDIR, config.GREETING)

    cp = BasicCallProgram(logfile=logfile)
    cp.set_dtmf_handler(dtmf_handler)
    cp.play(greeting)
    cp.beep()
    try:
        cp.record(inname)
    except VgettyError, err:
        print >>sys.stderr, "%s: %s" % (time.ctime(), err)
        cp.beep(6000, 3)
    else:
        print >>sys.stderr, "%s:%s|%s|%s|%s" % (time.ctime(), cp._device, inname, 
                    cp.caller_id, cp.caller_name)
    cp.close()
    return 0

def rmd2ogg(src, dst):
    from pycopia import proctools
    cmd = 'rmdtopvf "%s" | pvftolin -C -U | oggenc -Q -r -B 8 -C 1 -R 8000 --genre voicemail -o "%s" -' % (src, dst)
    if os.path.isfile(src):
        return proctools.system(cmd)


