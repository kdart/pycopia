#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-QA"
VERSION = "1.0a5"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = [
        'pycopia-storage>=1.0a4,==dev', 
        'pycopia-CLI>=1.0a4,==dev',
        'docutils>=0.5'
        ],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    scripts =glob("bin/*"), 
    data_files = [
        ('/etc/pycopia', glob("etc/*.dist")),
    ],
    test_suite = "test.QATests",

    description = "Pycopia packages to support professional QA roles.",
    long_description = """Pycopia packages to support professional QA roles.
    A basic QA automation framework. Provides base classes for test cases,
    test suites, test runners, reporting, lab models, terminal emulators,
    remote control, and other miscellaneous functions.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@dartworks.biz",
    keywords = "pycopia QA framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Software Development :: Quality Assurance",
                   "Intended Audience :: Developers"],
)


