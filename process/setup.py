#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys, os

import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup

NAME = "pycopia-process"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    test_suite = "test.ProcessTests",
    install_requires = ['pycopia-core<=1.0,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    data_files = [
        ('/etc/pycopia', glob("etc/*")),
        (os.path.join(sys.prefix, 'share', 'pycopia', 'docs'), 
             glob("doc/*.rst")),
    ],

    description = "Modules for running, interacting with, and managing processes.",
    long_description = """Modules for running, interacting with, and managing processes.
    A process manager for spawning and managing multiple processess. Support for Python coprocess.
    Expect module for interacting with processes. Can connect with pipes or pty. 
    Objects for status reporting and process information.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Operating System",
                   "Intended Audience :: Developers"],
)


