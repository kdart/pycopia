#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys, os

from glob import glob
from setuptools import setup, find_packages

import platutils
platinfo = platutils.get_platform()

NAME = "pycopia-storage"
VERSION = "1.0"


if platinfo.is_linux():
    DATAFILES = [
        ('/etc/pycopia', glob("etc/*.example") + glob("etc/*.dist")),
        ('/etc/pam.d', glob("etc/pam.d/*")),
    ]
    if platinfo.is_gentoo():
        DATAFILES.append(('/etc/init.d', glob("etc/init.d/gentoo/*")))
    elif platinfo.is_redhat():
        DATAFILES.append(('/etc/init.d', glob("etc/init.d/redhat/*")))

    WEBSITE = os.environ.get("WEBSITE", "localhost")
    DATAFILES.extend([
        #(os.path.join("/var", "www", WEBSITE, 'htdocs'), glob("doc/html/*.html")),
        #(os.path.join("/var", "www", WEBSITE, 'cgi-bin'), glob("doc/html/cgi-bin/*.py")),
        (os.path.join("/var", "www", WEBSITE, 'media', 'js'), glob("media/js/*.js")),
        (os.path.join("/var", "www", WEBSITE, 'media', 'css'), glob("media/css/*.css")),
        #(os.path.join("/var", "www", WEBSITE, 'media', 'images'), glob("media/images/*.png")),
    ])
    SCRIPTS = glob("bin/*")
else:
    DATAFILES = []
    SCRIPTS = []


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
#    install_requires = [
#        'pycopia-core>=1.0.dev-r138,==dev',
#        'pycopia-CLI>=1.0.dev-r138,==dev',
#        'sqlalchemy>=0.9.0',
#        'pycrypto>=2.0',
#        'urwid>=1.0',
#        #'psycopg>=2.0',
#        ],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    test_suite = "test.StorageTests",
    scripts = SCRIPTS,
    data_files = DATAFILES,

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
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


