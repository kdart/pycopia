#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

NAME = "pycopia-debugger"
VERSION = "0.9"

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    install_requires = ['pycopia-aid>=0.9', 'pycopia-CLI>=0.9'],
    package_data = {
        'pycopia': ['*.doc'],
    },
    test_suite = "test.DebuggerTests",

    description = "Enhanced Python debugger.",
    long_description = """Enhanced Python debugger.
    Like pdb, but has more inspection commands, colorized output, command
    history.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


