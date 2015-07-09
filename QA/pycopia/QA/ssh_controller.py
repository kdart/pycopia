#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Controller that wraps an SSH session.
"""

from pycopia.OS.exitstatus import ExitStatus
from pycopia import sshlib

from pycopia.QA import controller


class ShellController(controller.Controller):
    """A Controller for a POSIX shell."""
    def initialize(self):
        self._iamroot = False
        self._reset("XyZ% ")
        self.readline = self._intf.readline

    def _reset(self, newprompt):
        s = self._intf
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
        ret = ExitStatus(cmd, int(ret)<<8)
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
                raise ControllerError, "could not set hostname"
        else:
            resp, el = self.command("hostname")
            if el:
                return resp.strip()
            else:
                raise ControllerError, "could not get hostname"

    def version(self):
        resp, rv = self.command("uname -a")
        if rv:
            return resp.strip()
        else:
            raise ControllerError, "could not get version string."

    def routes(self):
        "Return a report of current IP routes."
        resp, es = self.command("route -n") # XXX
        if es:
            return resp
        else:
            raise ControllerError, es

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
        ret = ExitStatus("<interrupted process>", int(ret)<<8)
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



def get_controller(equipment, logfile=None):
    try:
        del os.environ["TERM"]
    except KeyError:
        pass
    ssh = sshlib.get_ssh(equipment["hostname"], equipment["user"],
            equipment["password"], prompt=equipment["prompt"],
            logfile=logfile)
    ctor = ShellController(ssh)
    ctor.host = equipment["hostname"]
    ctor.user = equipment["user"]
    ctor.password = equipment["password"]
    return ctor

