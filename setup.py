#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
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
Master builder (custom script).
This top-level setup script helps with dealing with all sub-packages at
once. It also provides an installer for a nicer developer mode. 

Invoke it like a standard setup.py script. However, Any names after the
operation name are taken as sub-package names that are operated on. If no
names are given then all packages are operated on.

Commands:
 list         -- List available subpackages. These are the names you may optionally supply.
 publish      -- Put source distribution on pypi.
 build        -- Run setuptools build phase on named sub-packages (or all of them).
 install      -- Run setuptools install phase.
 eggs         -- Build distributable egg package.
 rpms         -- Build RPMs on platforms that support building RPMs.
 msis         -- Build Microsoft .msi on Windows.
 wininst      -- Build .exe installer on Windows.
 develop      -- Developer mode, as defined by setuptools.
 develophome  -- Developer mode, installing .pth and script files in user directory.
 clean        -- Run setuptools clean phase.
 squash       -- Squash (flatten) all named sub-packages into single tree
                 in $SQUASHDIR, or user site-directory if no $SQUASHDIR defined.
                 This also removes the setuptools runtime dependency.

Most regular setuptools commands also work. They are passed through by
default.

NOTE: The install operation requires that the sudo command be configured for you.

"""

import sys
import os

try:
    WEXITSTATUS = os.WEXITSTATUS
except AttributeError: # running on Windows
    def WEXITSTATUS(arg):
        return arg
    os.environ["HOME"] = os.environ["USERPROFILE"]
    RSYNCCHECK = "rsync --version >nul"
else:
    RSYNCCHECK = "rsync --version >/dev/null"

PACKAGES = [
"aid",
"utils",
"core",
"CLI",
"debugger",
"process",
"SMI",
"mibs",
"SNMP",
"storage",
"QA",
"net",
"audio",
"XML",
"WWW",
"vim",
"fepy",
]

HOMESITE = os.path.expandvars("$HOME/.local/lib/python%s/site-packages" % (sys.version[:3],))
SQUASHDIR = os.environ.get("SQUASHDIR", HOMESITE)
SCRIPTDIR = os.environ.get("SCRIPTDIR", os.path.expandvars("$HOME/bin"))


def _do_commands(name, cmds, root):
    # use sudo on Linux and possibly other platforms. On Windows it's
    # assumed you're running as Administrator (everybody does it...)
    if root and sys.platform not in ("win32", "cli"):
        sudo = "sudo "
    else:
        sudo = ""
    cmd = "%s%s setup.py %s" % (sudo, sys.executable, " ".join(cmds))
    print "========", name, "==", cmd
    rv = False
    os.chdir(name)
    try:
        rv = WEXITSTATUS(os.system(cmd)) == 0
    finally:
        os.chdir("..")
        print "====================== END", name
        print
    return rv

def do_eggs(name):
    return _do_commands(name, ["bdist_egg"], False)

def do_rpms(name):
    return _do_commands(name, ["bdist_rpm"], False)

def do_msis(name):
    return _do_commands(name, ["bdist_msi"], False)

def do_wininst(name):
    return _do_commands(name, ["bdist_wininst"], False)

# "scripts", those files in bin/, may require some special interpreter
# flags, such as -S, that the setuptools developer mode mangles. Therefore,
# there is this special script installer that does a regular install for
# developer mode.
def _do_scripts(name, scriptdir):
    os.chdir(name)
    try:
        cmd = "%s setup.py install_scripts --install-dir %s" % (sys.executable, scriptdir)
        rv = WEXITSTATUS(os.system(cmd)) == 0
    finally:
        os.chdir("..")
    if not rv:
        print "Warning: scripts for %r may not have installed." % (name,)

def do_develophome(name):
    if not os.path.isdir(HOMESITE):
        os.makedirs(HOMESITE)
    _do_scripts(name, SCRIPTDIR)
    return _do_commands(name, ["develop -x -l -N",  "--install-dir", HOMESITE], False)

def do_develop(name):
    _do_scripts(name, SCRIPTDIR)
    return _do_commands(name, ["develop -x -l -N"], False)

def do_publish(name):
    return _do_commands(name, ['egg_info -RDb ""', "sdist", "register", "upload"], False)

def do_egg_info(name):
    return _do_commands(name, ['egg_info'], False)

def do_install(name):
    return _do_commands(name, ["install --install-scripts /usr/local/bin -O2"], True)

def do_clean(name):
    return _do_commands(name, ["clean"], False)

def do_list(name):
    print name,
    return True

# "squash" selected sub packages to a single package. Also removes
# setuptools dependency when tarballed.
def do_squash(name):
    if not _check_rsync():
        print "Squash requires rsync tool to be installed."
        return False
    if not os.path.isdir(SQUASHDIR):
        os.makedirs(SQUASHDIR)
    os.chdir(name)
    uname = os.uname()
    bin_dir = os.path.join("build", "lib.%s-%s-%s" % (uname[0].lower(), uname[4], sys.version[:3]))
    # e.g: build/lib.linux-x86_64-2.5/pycopia
    print "======== SQUASH", name, "to", SQUASHDIR
    try:
        if WEXITSTATUS(os.system("%s setup.py build" % (sys.executable,))) != 0:
            return False
        for pydir in ("build/lib", bin_dir):
            if os.path.isdir(pydir):
                cmd = "rsync -azvu %s/ %s" % (pydir, SQUASHDIR)
                if WEXITSTATUS(os.system(cmd)) != 0:
                    return False
    finally:
        os.chdir("..")
    _null_init(SQUASHDIR)
    print "====================== END", name, "squashed into", SQUASHDIR
    print
    return True

def _null_init(directory):
    open(os.path.join(directory, "pycopia", "__init__.py"), "w").close()

def _check_rsync():
    return WEXITSTATUS(os.system(RSYNCCHECK)) == 0

def do_generic(name):
    pass

def main(argv):
    try:
        cmd = argv[1]
    except IndexError:
        print __doc__
        return 1
    try:
        method = globals()["do_" + cmd]
    except KeyError:
        def method(name):
            return _do_commands(name, [cmd], False)
    for name in (argv[2:] or PACKAGES):
        if not method(name):
            break
    print
    return 0

sys.exit(main(sys.argv))
