#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

NAME = "pycopia-fepy"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = ['pycopia-aid>=1.0,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    test_suite = "test.FepyTests",

    description = "Modules for use with IronPython.",
    long_description = """
    The purpose of the modules here are to enhance the IronPython runtime
    with extra modules for debugging and better integration with the rest
    of the Pycopia framework. 
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@dartworks.biz",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = [ "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)


