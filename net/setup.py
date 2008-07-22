#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-net"
VERSION = "1.0a3"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = ['pycopia-process>=1.0a1,==dev', 
                        'pycopia-CLI>=1.0a1,==dev'],
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
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking",
                   "Intended Audience :: Developers"],
)


