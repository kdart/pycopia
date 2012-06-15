#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import print_function

import sys
import os

from setuptools import setup, Extension
from glob import glob

NAME = "pycopia-utils"
VERSION = "1.0"

SCRIPTS = []
EXTENSIONS = []

if sys.platform == "darwin":
    EXTENSIONS.append(Extension('pycopia.itimer', ['pycopia.itimer.c']))
elif sys.platform.startswith("linux"):
    EXTENSIONS.append(Extension('pycopia.itimer', ['pycopia.itimer.c'], libraries=["rt"]))
    SCRIPTS = glob("bin/*")


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    scripts = SCRIPTS,
    ext_modules = EXTENSIONS,
#    install_requires = ['pycopia-aid>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
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


if sys.platform.startswith("linux"):
    if os.getuid() == 0 and sys.argv[1] == "install":
        print ("Installing SUID helpers.")
        try:
            build_tools()
        except:
            ex, val, tb = sys.exc_info()
            print ("Could not build helper programs:", file=sys.stderr)
            print ("%s (%s)" % (ex, val), file=sys.stderr)
    else:
        print ("You must run 'setup.py install' as root to install helper programs.", file=sys.stderr)

