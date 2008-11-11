#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

NAME = "pycopia-CLI"
VERSION = "1.0a4"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    install_requires = ['pycopia-aid>=1.0a1,==dev'],
    test_suite = "test.CLITests",

    description = "Pycopia framework for constructing POSIX/Cisco style command line interface tools.",
    long_description = """Pycopia framework for constructing POSIX/Cisco style command line
    interface tools.  Supports context commands, argument parsing,
    debugging aids.  Modular design allows you to wrap any object with a
    CLI tool.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia CLI framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


