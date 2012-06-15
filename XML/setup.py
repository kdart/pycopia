#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys
import os

from glob import glob
from setuptools import setup

NAME = "pycopia-XML"
VERSION = "1.0"
#REVISION = os.environ["PYTHON_REVISION"]


if sys.platform not in ("win32", "cli"):
    DATA_FILES=[('/etc/pycopia/dtd', glob("etc/dtd/*.dtd")+glob("etc/dtd/*.ent"))]
else:
    DATA_FILES=[]

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.XML", "pycopia.dtds"],
#    install_requires = ['pycopia-core>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    data_files=DATA_FILES,
    scripts = glob("bin/*"),
    test_suite = "test.XMLTests",

    description = "Work with XML in a Pythonic way.",
    long_description = """Work with XML in a Pythonic way.
    Provides Python(ic) Object Model, or POM, for creating, inspecting, or
    modifying basic XML documents. Provides XML factory objects. Partially
    validates documents when emitted. This framework requires a DTD for
    the XML. Never "print" XML tags again.""",
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework XML",
    url = "http://www.pycopia.net/",
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Text Processing :: Markup :: XML",
                   "Intended Audience :: Developers"],
)


