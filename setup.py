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
 list             -- List available subpackages. These are the names you may optionally supply.
 publish          -- Put source distribution on pypi.
 build            -- Run setuptools build phase on named sub-packages (or all of them).
 install          -- Run setuptools install phase.
 install_scripts  -- Only install scripts (files in bin) with a direct copy.
 eggs             -- Build distributable egg package.
 rpms             -- Build RPMs on platforms that support building RPMs.
 msis             -- Build Microsoft .msi on Windows.
 wininst          -- Build .exe installer on Windows.
 develop          -- Developer mode, as defined by setuptools.
 develophome      -- Developer mode, installing .pth and script files in user directory.
 clean            -- Run setuptools clean phase.
 squash           -- Squash (flatten) all named sub-packages into single tree
                     in $PYCOPIA_SQUASH, or user site-directory if no $PYCOPIA_SQUASH defined.
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
    SCRIPT_DIR = os.path.join(sys.prefix, "Scripts")
else:
    RSYNCCHECK = "rsync --version >/dev/null"
    SCRIPT_DIR = "/usr/local/bin"

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
"net",
"audio",
"XML",
"WWW",
"QA",
"vim",
"fepy",
]

# newer Pythons also search this location in user's directory.  We can use
# this for storing the .pth files in develop mode. Should we also support
# older Python?

HOMESITE = os.path.join(os.path.expandvars("$HOME"), ".local", "lib",
                        "python%s" % (sys.version[:3],), "site-packages")
PYCOPIA_SQUASH = os.environ.get("PYCOPIA_SQUASH", HOMESITE)
PYCOPIA_BIN = os.environ.get("PYCOPIA_BIN", os.path.join(os.path.expandvars("$HOME"), "bin"))


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
# flags, such as -S, This prevents setuptools from functioning.
# Since Pycopia scripts are written generically there is not reason not to
# install them as-is.

# only works on Linux for now.
def _do_scripts(name, scriptdir, root=False):
    if root and sys.platform not in ("win32", "cli"):
        sudo = "sudo "
    else:
        sudo = ""
    os.chdir(name)
    rv = True
    try:
        if os.path.isdir("bin"):
            cmd = "%scp -dR --preserve=mode  bin/* %s" % (sudo, scriptdir)
            print "======== SCRIPTS", name, "==", cmd
            rv = WEXITSTATUS(os.system(cmd)) == 0
    finally:
        os.chdir("..")
    print "====================== END SCRIPTS", name
    return rv

def do_install_scripts(name):
    return _do_scripts(name, PYCOPIA_BIN)

def do_develophome(name):
    if not os.path.isdir(HOMESITE):
        os.makedirs(HOMESITE)
    rv = _do_commands(name, ["develop", "--install-dir", HOMESITE, "--script-dir", PYCOPIA_BIN, "-l -N"], False)
    rvs = _do_scripts(name, PYCOPIA_BIN)
    return rv and rvs

def do_develop(name):
    rv = _do_commands(name, ["develop", "--script-dir", PYCOPIA_BIN, "-l -N"], False)
    rvs = _do_scripts(name, PYCOPIA_BIN)
    return rv and rvs

def do_publish(name):
    return _do_commands(name, ['egg_info -RDb ""', "sdist", "register", "upload"], False)

def do_egg_info(name):
    return _do_commands(name, ['egg_info'], False)

def do_install(name):
    rv1 = _do_commands(name, ["install -O2", "--install-scripts",  SCRIPT_DIR], True)
    # Don't use the setuptools script wrapper for Pycopia scripts. This
    # will overwrite the installed scripts with a direct copy.
    rv2 = _do_scripts(name, SCRIPT_DIR, True)
    return rv1 and rv2

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
    if not os.path.isdir(PYCOPIA_SQUASH):
        os.makedirs(PYCOPIA_SQUASH)
    os.chdir(name)
    uname = os.uname()
    bin_dir = os.path.join("build", "lib.%s-%s-%s" % (uname[0].lower(), uname[4], sys.version[:3]))
    # e.g: build/lib.linux-x86_64-2.5/pycopia
    print "======== SQUASH", name, "to", PYCOPIA_SQUASH
    try:
        if WEXITSTATUS(os.system("%s setup.py build" % (sys.executable,))) != 0:
            return False
        for pydir in ("build/lib", bin_dir):
            if os.path.isdir(pydir):
                cmd = "rsync -azvu %s/ %s" % (pydir, PYCOPIA_SQUASH)
                if WEXITSTATUS(os.system(cmd)) != 0:
                    return False
    finally:
        os.chdir("..")
    _null_init(PYCOPIA_SQUASH)
    print "====================== END", name, "squashed into", PYCOPIA_SQUASH
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
