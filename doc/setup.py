#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import os
from glob import glob
from setuptools import setup

NAME = "pycopia-doc"
VERSION = "1.0"

import platutils
platinfo = platutils.get_platform()

if platinfo.is_linux():
    WEBSITE = os.environ.get("WEBSITE", "localhost")
    wspath = os.path.join("/var", "www", WEBSITE, 'htdocs', 'docs')
    _static = os.path.join(wspath, "html", "_static")
    DATA_FILES = [
        (_static, glob("source/_static/*")),
        (_static, glob("source/_themes/pycopia/static/*")),
    ]
else:
    DATA_FILES = []

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.doc"],
#    install_requires = [
#            'pycopia-core>=1.0,==dev',
#            'sphinx>=1.0',
#    ],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    test_suite = "test.DocTests",
    data_files = DATA_FILES,
    description = "Pycopia documentation.",
    long_description = """Pycopia documentation.
    Documentation, and tools for generating documentaton for Pycopia.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


