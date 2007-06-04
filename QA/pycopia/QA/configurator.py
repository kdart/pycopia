#!/usr/bin/python
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>
# $Id$

"""
Abstract interfaces for object controllers.

"""

import sys, os

from pycopia import proctools
from pycopia import sshlib

class ConfigError(AssertionError):
    pass

# base class for all types of Controllers.
class Controller(object):
    def __init__(self, intf):
        self._intf = intf # the low-level device interface, whatever it is.
        self.initialize()

    def __del__(self):
        self.finalize()

    def initialize(self):
        pass

    def finalize(self):
        pass

    def set_logfile(self, lf): # XXX assumes expect object wrapping process object
        fo = self._intf.fileobject()
        fo.newlog(lf)


class ControllerShell(Controller):
    """A Controller for a POSIX shell."""
    def initialize(self):
        self._iamroot = False
        self._reset("XyZ% ")
        self.readline = self._intf.readline

    def _reset(self, newprompt):
        s = self._intf
        #s.send("\r")
        s.wait_for_prompt()
        s.set_prompt(newprompt)
        s.send("export PS1=%r ; unset PROMPT_COMMAND\r" % (newprompt,))
        s.wait_for_prompt() # first is for prompt embedded in command that was just sent
        s.wait_for_prompt()
        s.send("export TERM=tty43 ; HISTSIZE=0\r")
        s.wait_for_prompt()
        s.send("stty cols 132\r")
        s.wait_for_prompt()

    def command(self, cmd, timeout=600):
        "Send a shell command and return the output and the exit status."
        s = self._intf
        s.send(str(cmd))
        s.send("\r")
        s.readline() # eat command that was just sent
        resp = s.wait_for_prompt(timeout)
        s.send("echo $?\r")
        s.readline() # eat echo line
        #ret = s.readline()
        ret = s.wait_for_prompt()
        ret = proctools.ExitStatus(cmd, int(ret)<<8)
        return resp, ret

    def rootcommand(self, cmd, timeout=600):
        doexit = False
        if not self.is_root():
            self.rootme()
            doexit = True
        try:
            resp, rv = self.command(cmd, timeout)
        finally:
            if doexit:
                self.exit()
        return resp, rv

    def hostname(self, newname=None):
        "Get the hostname."
        if newname:
            resp, el = self.command("hostname %s" % (newname,))
            if el:
                return True
            else:
                raise ConfigError, "could not set hostname"
        else:
            resp, el = self.command("hostname")
            if el:
                return resp.strip()
            else:
                raise ConfigError, "could not get hostname"

    def version(self):
        resp, rv = self.command("uname -a")
        if rv:
            return resp.strip()
        else:
            raise ConfigError, "could not get version string."

    def routes(self):
        "Return a report of current IP routes."
        resp, es = self.command("route -n") # XXX
        if es:
            return resp
        else:
            raise ConfigError, es

    def reboot(self):
        "Reboot this device"
        self._intf.send("reboot\r")
        rv = self._intf.wait_for_prompt()
        fo = self._intf.fileobject()
        fo.flushlog()
        del fo
        self._intf.close()
        self._intf = None
        return rv

    def rootme(self):
        """Become root using sudo."""
        if not self._iamroot:
            s = self._intf
            s.set_prompt("# ")
            s.send("sudo -s\r")
            self._reset("XyZ# ")
            self._iamroot = True

    def is_root(self):
        "Returns boolean indicating if login is in root account state."
        return self._iamroot

    def exit(self):
        "Exit from root if you are root, or else exit the connection."
        s = self._intf
        if self._iamroot:
            s.send("exit\r")
            s.set_prompt("XyZ% ")
            s.wait_for_prompt()
            self._iamroot = False
        else:
            self._intf.send("exit\r")
            self._intf.close()
            self._intf = None

    def passwd(self, newpass, oldpass=None):
        "Change the password"
        self._intf.send("passwd\r")
        self._intf.expect("New")
        self._intf.send("%s\r" % (newpass,))
        self._intf.expect("Retype")
        self._intf.send("%s\r" % (newpass,))
        self._intf.wait_for_prompt()

    def tail(self, fname, filt=None):
        "Tail a log. return the contained file object so user can call readline() on it."
        if filt:
            cmd = "tail -f %s | grep %s\r" % (fname, filt)
        else:
            cmd = "tail -f %s\r" % (fname, )
        self._intf.send(cmd)
        self._intf.readline() # eat command that was just sent
        fo = self._intf.fileobject()
        return fo

    def interrupt(self):
        "Interrupt a running process. Return the exit value."
        s = self._intf
        fo = s.fileobject()
        fo.interrupt()
        s.wait_for_prompt()
        s.send("echo $?\r")
        s.readline()
        ret = s.readline()
        s.wait_for_prompt()
        ret = proctools.ExitStatus("<interrupted process>", int(ret)<<8)
        return ret

    def scp(self, src, dst, download=False):
        """Use scp to copy a file from local host to remote device (if download
        is false), or from remote device to local host (if download is True)."""
        if download:
            return sshlib.scp(srchost=self.host, srcpath=src, dsthost=None, dstpath=dst,
                user=self.user, password=self.password, logfile=self._intf.fileobject().getlog())
        else:
            return sshlib.scp(srchost=None, srcpath=src, dsthost=self.host, dstpath=dst,
                user=self.user, password=self.password, logfile=self._intf.fileobject().getlog())



# factory for figuring out the correct Controller to use, and returning it.
def get_controller(dut, logfile=None):
    return _get_controller(dut, dut.accessmethod, logfile)

def get_initial_controller(dut, logfile=None):
    return _get_controller(dut, dut.initialaccessmethod, logfile)

def _get_controller(dut, cm, logfile):
    if cm == "ssh":
        try:
            del os.environ["TERM"]
        except KeyError:
            pass
        ssh = sshlib.get_ssh(dut, dut.user, dut.password, prompt=dut.prompt, logfile=logfile)
        ctor = ControllerShell(ssh)
        ctor.host = str(dut)
        ctor.user = dut.user
        ctor.password = dut.password
        return ctor
    elif cm == "serial":
        return NotImplemented
    elif cm == "telnet":
        return NotImplemented
    elif cm == "http":
        return NotImplemented
    elif cm == "https":
        return NotImplemented
    elif cm == "console":
        return NotImplemented
    elif cm == "snmp":
        return NotImplemented
    else:
        raise ValueError, "invalid configuration method: %s." % (cm,)


