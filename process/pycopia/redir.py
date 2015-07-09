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
Simple Python wrapper for the 'redir' program.
Note that to use this to redirect privileged TCP ports as a regular user you
must make your 'redir' program suid to root. This is a bad security practice,
but is necessary for some scenarios. just be aware.

"""

from pycopia import proctools

try:
    REDIR = proctools.which("redir")
except ValueError:
    raise ImportError, "'redir' program not found in PATH"

def redir(lport, cport, laddr=None, caddr=None, extraopts=None):
    """redir(lport, cport, laddr=None, caddr=None, extraopts=None)
Redirect local port to client port, possible to another host is caddr is given.
Optionally bind to a specific IP if laddr is also given.
    """
    opts = "--lport=%d --cport=%d" % (lport, cport)
    if laddr:
        opts += " --laddr=%s" % (laddr,)
    if caddr:
        opts += " --caddr=%s" % (caddr,)
    cmd = "%s %s %s" % (REDIR, opts, extraopts or "")
    proc = proctools.spawnpipe(cmd, merge=0)
    return proc


def perm_check():
    """In our environment the redir program must be suid with root owner. It
needs to open privileged ports. Returns True if permissions are ok, False
otherwise."""
    import os, stat
    if os.getuid() == 0:
        return 1 # we are already running as root...
    st = os.stat(REDIR)
    return st.st_uid == 0 and (stat.S_IMODE(st.st_mode) & stat.S_ISUID)
check_perm = perm_check # alias

def remote_redir(host, lport, cport, laddr=None, caddr=None, extraopts=None,
        user=None, password=None, logfile=None):
    """run the port redirector on a remote host. Note that to redirect priviged
ports the 'redir' program on the remote host must be suid root. SSH is used
for this. If necessary, you can pass in a user and password for the ssh
program."""
    from pycopia import sshlib
    opts = "--lport=%d --cport=%d" % (lport, cport)
    if laddr:
        opts += " --laddr=%s" % (laddr,)
    if caddr:
        opts += " --caddr=%s" % (caddr,)
    cmd = "redir %s %s" % (opts, extraopts or "")
    rd = sshlib.get_ssh(host, user=user, password=password, logfile=logfile, cmd=cmd)
    return rd


def start_redir(lhost=None, lport=25, cport=9025):
    """start_redir(lhost=None, lport=25, cport=9025)
Starts the redir program in such a way as to ensure that whatever
listening port is specified, local or remote, connections get to the
cport on the host where this is run. If remote execution is necessary
then SSH will be used.  lhost defaults to localhost."""
    from pycopia import socket
    if lhost is None:
        lhost = socket.getfqdn()
    if socket.check_port(lhost, lport):
        raise RuntimeError, "something is already listening on (%r, %r)" % (lhost, lport)
    if socket.islocal(lhost):
        if perm_check():
            return redir(lport, cport)
        else:
            raise RuntimeError, "cannot run redir as non-root. check suid bit."
    else:
        myself = socket.getfqdn()
        # for this to work it assumes a lot...
        # 1. ssh is configured for public-key authentication (no
        # password).
        # 2. redir exists and is on the PATH on the remote host.
        # 3. redir is suid-root on the host.
        return remote_redir(lhost, lport, cport, caddr=myself)

# Matching killlall for start_redir (above), in case you need it.
# But you should probably use the returned objects interrupt() method.
def killall(lhost=None):
    from pycopia import socket
    from pycopia import proctools
    if lhost is None or socket.islocal(lhost):
        proctools.killall("redir")
    else:
        from pycopia import sshlib
        sshlib.ssh_command(lhost, "killall redir")

