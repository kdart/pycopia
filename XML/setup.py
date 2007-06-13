#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup

NAME = "pycopia-XML"
VERSION = "1.0a1"

DNAME = NAME.split("-", 1)[-1]
ENAME = NAME.replace("-", "_")

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.XML", "pycopia.dtds"],
    install_requires = ['pycopia-core>=1.0a1,==dev'],
    data_files=[('/etc/pycopia/dtd', glob("etc/dtd/*.dtd")+glob("etc/dtd/*.ent"))],
    scripts = glob("bin/*"), 
    test_suite = "test.XMLTests",

    description = "Work with XML in a Pythonic way.",
    long_description = """Work with XML in a Pythonic way.
    Provides Python(ic) Object Model, or POM, for creating, inspecting, or
    modifying basic XML documents. Partially validates documents. This framework
    requires a DTD for the XML. Never "print" XML tags again.""",
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework XML",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Text Processing :: Markup :: XML",
                   "Intended Audience :: Developers"],
)


