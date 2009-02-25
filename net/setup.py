#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-net"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = ['pycopia-process<=1.0,==dev', 
                        'pycopia-CLI<=1.0,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    scripts = glob("bin/*"), 
    test_suite = "test.NetTests",

    description = "General purpose network related modules.",
    long_description = """General purpose network related modules.
    Modules for updating DNS, modeling metworks, measuring networks, and a
    framework for the creation of arbitrary chat-style protocols.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia networks",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking",
                   "Intended Audience :: Developers"],
)


