#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab
# 
# $Id$
#
#    Copyright (C) 1999-2007  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from glob import glob

NAME = "pycopia-experimental"
VERSION = "1.0a2"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]


setup(
    name = NAME, version = VERSION,
    #packages = find_packages(),
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    scripts =glob("bin/*")+glob("sbin/*"), 
    install_requires = ['docutils>=0.5'],

    data_files=[('/etc/pycopia', glob("etc/*.dist"))],
    package_data = {
        '': ['*.txt', '*.rst', '*.doc'],
    },
    # metadata for upload to PyPI
    author = "Keith Dart",
    author_email = "keith@pycopia.net",
    description = "the mother of all frameworks for rapid application development in Python.",
    long_description = """A framework of frameworks for rapid application development in Python.
    It includes packages for XML and XHTML parsing and generating, SNMP manager, 
    SMI query API, Cisco-style CLI framework, QA automation, program control, and more.""",
    license = "LGPL",
    keywords = "framework web CLI network SNMP SMI XML XHTML QA automation",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    classifiers = [
       "Operating System :: POSIX", 
       "Intended Audience :: Developers",
       "Topic :: Software Development :: Libraries :: Application Frameworks"
       "Topic :: System :: Networking :: Monitoring",
       "Topic :: Text Processing :: Markup :: XML",
    ],
)

