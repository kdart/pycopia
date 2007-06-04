#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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
Wrapper for the ssh program. 

Provides get_ssh, ssh_command, and scp functions.

"""

import sys, os

from pycopia import proctools
from pycopia import expect
from pycopia.aid import IF

try:
    SSH = proctools.which("ssh")
    SCP = proctools.which("scp")
    KEYGEN = proctools.which("ssh-keygen")
    KEYSCAN = proctools.which("ssh-keyscan")
except ValueError:
    raise ImportError, "ssh program not found!"

class SSHRetry(RuntimeError):
    pass

#                  |01234567890123456789
TESTED_VERSIONS = ["OpenSSH_3.4p1, SSH protocols 1.5/2.0, OpenSSL 0x0090605f",
                   "OpenSSH_3.5p1, SSH protocols 1.5/2.0, OpenSSL 0x0090701f",
                   "OpenSSH_3.6.1p2, SSH protocols 1.5/2.0, OpenSSL 0x0090701f",
                   "OpenSSH_3.8.1p1, OpenSSL 0.9.7d 17 Mar 2004",
                   "OpenSSH_4.5p1, OpenSSL 0.9.8a 11 Oct 2005",
                   "OpenSSH_4.3p2"
                   ]

SSH_OPTIONS = '-F %s' % os.path.join("/", "etc", "pycopia", "ssh_config")

class SSHExpect(expect.Expect):
    def sshexit(self):
        self.send("\r~.\r")

    def login(self, password=None):
        """login([password]) 
Supplies a password for the SSH session. Net necessarily any subsequent login
prompts. """
        if password is None:
            import getpass
            password = getpass.getpass("Password: ")
        while True:
            mo = self.expect(["WARNING:", "assword:", "try again"], timeout=20)
            if mo:
                i = self.expectindex
                if i == 0:
                    raise SSHRetry, "SSHExpect.sshlogin: try again, bad host key."
                elif i == 1:
                    self._fo.write(password+"\r")
                    break
                elif i == 2:
                    continue
            else:
                raise RuntimeError, "SSHExpect.sshlogin: unknown response."

    def death_callback(self, deadssh):
        if self._log:
            self._log.write("ssh exited: %s" % (deadssh.exitstatus))
        self.close()


def _build_commandline(host, **kwargs):
#user=None, password=None, prompt=None, callback=None, logfile=None, extraoptions=""
    if kwargs["user"] is None:
        cmd = "%s %s %s" %(SSH, host, command)
    else:
        cmd = "%s %s@%s %s" %(SSH, user, host, command)

def ssh_command(host, command, user=None, password=None, prompt=None, logfile=None):
    """ssh_command(host, command, [user], [password], [prompt], [logfile])
Runs the command on the given host via SSH, and return the result.
    """
    pm = proctools.get_procmanager()
    if user is None:
        cmd = "%s %s %s" %(SSH, host, command)
    else:
        cmd = "%s %s@%s %s" %(SSH, user, host, command)
    sshproc = pm.spawnpty(cmd)
    ssh = SSHExpect(sshproc)
    sshproc.set_callback(ssh.death_callback)
    ssh.set_prompt(prompt or "$")
    ssh.setlog(logfile)
    if password is not None:
        ssh.login(password)
    rv = ssh.read()
    return rv

def get_ssh(host, user=None, password=None, prompt=None, callback=None, logfile=None, extraoptions="",
            cmd=None, async=False):
    """get_ssh(host, [user], [password], [prompt], [callback], [logfile])
Uses ssh to get a shell on the given host, and automatically authenticate by
password if a password is given.  Returns an SSHExpect object.

The logfile parameter should be a file-like object (has a 'write' method).
"""
    pm = proctools.get_procmanager()
    hostuser = IF(user, "%s@%s" % (user, host), host)
    command = "%s %s %s %s %s" % (SSH, SSH_OPTIONS, extraoptions, hostuser, cmd or "")
    sshproc = pm.spawnpty(command, logfile=logfile, async=async)
    ssh = SSHExpect(sshproc)
    sshproc.set_callback(callback or ssh.death_callback)
    ssh.set_prompt(prompt or "$")
    if password is not None:
        ssh.login(password)
    return ssh

def get_ssh_unsafe(host, *args, **kwargs):
    """get_ssh_unsafe(host, ...)
Like get_ssh(), but automatically removes any stale known_hosts entry, if
required."""
    try:
        return get_ssh(host, *args, **kwargs)
    except SSHRetry:
        remove_known_host(host)
        return get_ssh(host, *args, **kwargs)

def scp(srchost=None, srcpath=None, dsthost=None, dstpath=None, user=None, 
                password=None, prompt=None, callback=None, logfile=None):
    """scp(source, destination, [password])
Copies the file from source to destination. these parameters are strings that
are passed directly to the scp command, and should follow the syntax for this
command. 
    """
    opts = "-q"
    src = location(srchost, user, srcpath)
    dst = location(dsthost, user, dstpath)
    CMD = "%s %s %s '%s' '%s'" % (SCP, SSH_OPTIONS, opts, src, dst)
    if logfile:
        logfile.write(CMD+"\n")
    scp = proctools.spawnpty(CMD, logfile=logfile)
    if password is not None:
        escp = SSHExpect(scp)
        scp.set_callback(callback or escp.death_callback)
        escp.login(password)
        discard = escp.read()
    else:
        discard = scp.read()
    es = scp.wait()
    return es

def location(host=None, user=None, path=None, forssh=False):
    """Construct an appropriate ssh/scp path spec based on the combination of
    parameters. Supply host, user, and path."""
    sep = IF(forssh, "", ":")
    if host is None:
        if user is None:
            if path is None:
                raise ValueError, "must supply at least one of host, or user."
            else:
                return path
        else:
            if path is None:
                raise ValueError, "user without host?"
            else:
                return path # ignore user in this case
    else:
        if user is None:
            if path is None:
                return "%s%s" % (host, sep)
            else:
                return "%s:%s" % (host, path)
        else:
            if path is None:
                return "%s@%s%s" % (user, host, sep)
            else:
                return "%s@%s:%s" % (user, host, path)


def ssh_version():
    """ssh_version() Return the version string for the ssh command on this system."""
    ssh = proctools.spawnpipe("ssh -TV")
    ver = ssh.read()
    return ver

def check_version():
    """Checks that the installed ssh program is the same as this module was
    tested with (and written for)."""
    ver = ssh_version()[:13]
    for vs in TESTED_VERSIONS:
        if ver == vs[:13]:
            return 1
    return 0


def get_procs():
    """get_ssh_list() Returns list of managed ssh processes."""
    pm = proctools.get_procmanager()
    return pm.getbyname("ssh")


# Support objects follow.
# Mostly, these are for creating or modifying various ssh related files.
class KnownHostsFile(object):
    def __init__(self):
        self._fname = os.path.join(os.environ["HOME"], ".ssh", "known_hosts")
        self._lines = None
        self.open()

    def __del__(self):
        self.close()

    def __str__(self):
        return "".join(self._lines)

    def open(self):
        try:
            fo = open(self._fname, "r")
        except OSError:
            self._lines = []
        else:
            self._lines = fo.readlines()
            fo.close()
        self._dirty = 0

    def close(self):
        if self._dirty:
            fo = open(self._fname, "w+")
            fo.writelines(self._lines)
            fo.close()
            self._dirty = 0

    def add(self, hostname, publickey, comment=None):
        if comment:
            line = "%s %s %s\n" % (hostname, publickey, comment)
        else:
            line = "%s %s\n" % (hostname, publickey)
        self._lines.append(line)
        self._dirty = 1

    def remove(self, hostname):
        from pycopia import ipv4
        try:
            ip = str(ipv4.IPv4(hostname))
        except:
            ip = None
        new = []
        for line in self._lines:
            if line.startswith(hostname):
                self._dirty = 1
                continue
            elif ip and line.startswith(ip):
                self._dirty = 1
                continue
            else:
                new.append(line)
        self._lines = new

def get_known_hosts():
    return KnownHostsFile()

def get_userdir():
    return os.path.join(os.environ["HOME"], ".ssh")

def remove_known_host(hostname):
    khf = KnownHostsFile()
    khf.remove(hostname)
    khf.close()

def keygen(keytype="dsa", bits=1024, comment="", filename=None, passphrase=None, logfile=None, async=0, safe=1):
    """Generate a new ssh user key of the specified keytype."""
    assert keytype in KEYTYPES, "keytype must be one of: %s" % (KEYTYPES,)
    pm = proctools.get_procmanager()
    fn = filename or os.path.join(os.environ["HOME"], ".ssh", "id_%s" % (keytype,))
    ph = passphrase or ""
    if os.path.exists(fn):
        if safe:
            raise SSHRetry, "key file %s already exists." % (fn,)
        else:
            os.unlink(fn)
    command = '%s -q -N "%s" -t %s -b %s -C "%s" -f %s' % \
            (KEYGEN, ph, keytype, bits, comment, filename)
    kgproc = pm.spawnpty(command, logfile=logfile, async=async)
    kgproc.read()
    kgproc.wait()
    return kgproc.exitstatus

def keyscan(host, keytype="dsa", logfile=None, async=0):
    """Run ssh-keyscan. Return key, and program exit status."""
    assert keytype in KEYTYPES, "keytype must be one of: %s" % (KEYTYPES,)
    pm = proctools.get_procmanager()
    command = '%s -t %s %s' % (KEYSCAN, keytype, host)
    ksproc = pm.spawnpty(command, logfile=logfile, async=async)
    res = ksproc.read()
    ksproc.wait()
    lines = res.split("\n")
    [host, text] = lines[1].split(None, 1)
    if text.startswith("hostkey"):
        return None, ksproc.exitstatus
    if text[0] in "0123456789":
        rv = _parse_rsa1_pub(text)
    else:
        rv = _parse_rsa_dsa_pub(text)
    return rv, ksproc.exitstatus

##### key and keyfile objects.

class SSHKey(object):
    def parse(self, text):
        raise NotImplementedError

class SSHKeyRSA1(SSHKey):
    pass

class SSHKeyRSA1pub(SSHKey):
    def __init__(self, bits, exponent, modulus, comment=""):
        self.bits = int(bits)
        self.exponent = int(exponent)
        self.modulus = long(modulus)
        self.comment = str(comment)

    def __eq__(self, other):
        try:
            return self.exponent == other.exponent and self.modulus == other.modulus
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.exponent != other.exponent or self.modulus != other.modulus
        except AttributeError:
            return NotImplemented

    def __str__(self):
        if self.comment:
            return "%d %d %ld %s" % (self.bits, self.exponent, self.modulus, self.comment)
        else:
            return "%d %d %ld" % (self.bits, self.exponent, self.modulus)


# this is really only for RSA/DSA public keys
class SSHKeyPublic(SSHKey):
    def __init__(self, key, comment=""):
        self.key = str(key) # key is base64 encoded
        self.comment = str(comment)

    def __eq__(self, other):
        try:
            return self.key == other.key
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.key != other.key
        except AttributeError:
            return NotImplemented

    def __str__(self):
        return "%s %s %s" % (self.keytype, self.key, self.comment)


class SSHKeyRSA(SSHKey):
    pass

class SSHKeyRSApub(SSHKeyPublic):
    keytype = "ssh-rsa"



class SSHKeyDSA(SSHKey):
    pass

class SSHKeyDSApub(SSHKeyPublic):
    keytype = "ssh-dss"



class AuthorizedKeys(SSHKey):
    pass


# parser figures out the type, as well. Just pass a key file name, ruturn
# object of correct type with initialized values. Works something like a
# recursive-decent parser, except that it is not recursive. ;-)
def parse_key(filename):
    base, ext = os.path.splitext(filename)
    if ext and ext == ".pub":
        return parse_public(filename)
    else:
        return parse_private(filename)

def parse_public(filename):
    fo = open(filename)
    text = fo.read().strip()
    fo.close()
    if text[0] in "0123456789":
        return _parse_rsa1_pub(text)
    else:
        return _parse_rsa_dsa_pub(text)

def _parse_rsa1_pub(text):
    parts = text.split()
    [bits, exponent, modulus] = parts[:3]
    if len(parts) >= 4: # comments are optional
        comment = parts[3]
    else:
        comment = ""
    return SSHKeyRSA1pub(bits, exponent, modulus, comment)

def _parse_rsa_dsa_pub(text):
    parts = text.split()
    assert len(parts) >= 2, "parse_rsa_dsa: need at least 2 parts."
    if len(parts) >= 3:
        comment = parts[2]
    else:
        comment = ""
    [keytype, key] = parts[:2]
    assert keytype in KEYTYPES, "keytype (%r) not valid." % (keytype,)
    keycls_priv, keycls_pub = _CLSMAP[keytype]
    return keycls_pub(key, comment)


def parse_private(filename):
    raise NotImplementedError

def new_key(keytype="dsa", bits=1024, comment="", filename=None, passphrase=None):
    pass

# map to tuple of private key, public key classes
_CLSMAP = {"ssh-dss": (SSHKeyDSA, SSHKeyDSApub), 
            "ssh-rsa": (SSHKeyRSA, SSHKeyRSApub), 
            "rsa1": (SSHKeyRSA1, SSHKeyRSA1pub), 
            "rsa": (SSHKeyRSA, SSHKeyRSApub), 
            "dsa": (SSHKeyDSA, SSHKeyDSApub), 
            }
KEYTYPES = _CLSMAP.keys()

