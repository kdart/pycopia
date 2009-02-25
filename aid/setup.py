#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

NAME = "pycopia-aid"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.emailplus"],
    test_suite = "test.AidTests",

    author = "Keith Dart",
    author_email = "keith@kdart.com",
    description = "General purpose objects that enhance Python's core modules.",
    long_description = """General purpose objects that enhance Python's core modules.
    You can use these modules in place of the standard modules with the same name.
    This package is part of the collection of python packages known as pycopia.""",
    license = "LGPL",
    keywords = "pycopia framework Python extensions",
    url = "http://www.pycopia.net/",
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s-%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Programming Language :: Python",  
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)

