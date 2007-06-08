#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys
import os

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, Extension 

NAME = "pycopia-utils"
VERSION = "1.0a1"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

if sys.version_info[:2] < (2, 5):
# The readline and mmap modules here are copies of the Python 2.5 modules.
# They can also be used with previous versions of Python (as far as I can
# tell).  They provide some new features and bug fixes that Pycopia needs
# to function properly.

    readline = Extension('readline', ['readline.c'],
                    define_macros=[("HAVE_RL_COMPLETION_MATCHES", None)],
                    library_dirs=['/usr/lib/termcap'],
                   libraries=["readline", "ncurses"])

    mmap = Extension('mmap', ['mmapmodule.c'],)
    extensions  = [readline, mmap]
else:
    extensions  = []


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    ext_modules=extensions,
    install_requires = ['pycopia-process>=0.9,==dev'],
    test_suite = "test.UtilsTests",

    description = "Pycopia helper programs.",
    long_description = """Some functions of Pycopia require root
    privileges. This module contains some helper programs so that Pycopia
    scripts can run as non-root, but still perform some functions that
    require root (e.g. open ICMP socket, SNMP trap port, and syslog port). 
    It also includes the Python 2.5 readline module for older Pythons.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@dartworks.biz",
    keywords = "pycopia framework ping",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)

def build_tools():
    savedir = os.getcwd()
    os.chdir("src")
    try:
        os.system("sh configure")
        os.system("make")
        os.system("make install")
        os.system("make sinstall")
    finally:
        os.chdir(savedir)


# unlinks the orignal modules, since the new ones are installed into
# site-packages.
def unlink_old_modules():
    pythonver = "%s.%s" % tuple(sys.version_info[:2])
    for name in ("readline", "mmap"):
        try:
            os.unlink("%s/lib/python%s/lib-dynload/%s.so" % (sys.prefix, pythonver, name))
        except OSError:
            pass


if os.getuid() == 0 and sys.argv[1] == "install":
    print "Installing SUID helpers."
    try:
        build_tools()
    except:
        ex, val, tb = sys.exc_info()
        print >>sys.stderr, "Could not build helper programs:"
        print >>sys.stderr, "%s (%s)" % (ex, val)

    if extensions:
        unlink_old_modules()
else:
    print >>sys.stderr, "You must run 'setup.py install' as root to install helper programs."

