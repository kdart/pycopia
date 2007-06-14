#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-storage"
VERSION = "1.0a2"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = ['pycopia-core>=1.0a1,==dev', 'pycopia-CLI>=1.0a1,==dev', 'Durus>=3.5'],
    test_suite = "test.StorageTests",
    scripts = glob("bin/*"), 
    data_files = [
        ('/etc/pycopia', glob("etc/*.example")),
    ],

    description = "Pycopia storage and object model.",
    long_description = """Pycopia persistent storage and object model.
    Provides a storage build on top of Durus that defines container types
    and some persistent objects useful for networks and network device
    testing.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


