#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from glob import glob

NAME = "pycopia-core"
VERSION = "0.9.7"

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.ISO", "pycopia.inet", "pycopia.OS",
    "pycopia.OS.CYGWIN_NT", "pycopia.OS.Darwin", "pycopia.OS.FreeBSD",
    "pycopia.OS.SunOS",
    "pycopia.OS.Win32",
    "pycopia.OS.Linux",
    "pycopia.OS.Linux.proc",
    "pycopia.OS.Linux.proc.net",
    ],
    install_requires = ['pycopia-aid>=0.9.4'],
    package_data = {
        '': ['*.txt', '*.doc'],
    },
    test_suite = "test.CoreTests",
    data_files = [('/etc/pycopia', glob("etc/*"))],
    scripts = glob("bin/*"), 
    zip_safe = False,

    description = "Core components of the Pycopia application framework.",
    long_description = """Core components of the Pycopia application framework.
    Modules used by other PYcopia packages, that you can also use in your
    applications. There is a asynchronous handler interface, CLI tools,
    and misc modules.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework core Linux",
    url = "http://www.pycopia.net/",
    download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)


