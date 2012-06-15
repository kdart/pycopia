#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys, os

from glob import glob
from setuptools import setup

NAME = "pycopia-process"
VERSION = "1.0"


if sys.platform not in ("win32", "cli"):
    DATA_FILES = [
        ('/etc/pycopia', glob("etc/*")),
    ]
else:
    DATA_FILES = []

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    test_suite = "test.ProcessTests",
#    install_requires = ['pycopia-core>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    data_files = DATA_FILES,

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
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Operating System",
                   "Intended Audience :: Developers"],
)


