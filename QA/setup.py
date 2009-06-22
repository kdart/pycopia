#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-QA"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = [
        'pycopia-storage>=1.0.dev-r138,<=dev', 
        'pycopia-CLI>=1.0.dev-r138,<=dev',
        'docutils>=0.5'
        ],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    scripts =glob("bin/*"), 
    data_files = [
        ('/etc/pycopia', glob("etc/*.dist")),
        # XXX only Gentoo Linux supported for now.
        ('/etc/init.d', glob("etc/init.d/gentoo/*")),
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
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Software Development :: Quality Assurance",
                   "Intended Audience :: Developers"],
)


