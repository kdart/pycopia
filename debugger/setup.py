#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from glob import glob

NAME = "pycopia-debugger"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia"],
    install_requires = [
            'pycopia-aid>=1.0.dev-r138,==dev', 
            'pycopia-CLI>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    package_data = {
        'pycopia': ['*.doc'],
    },
    scripts =glob("bin/*"), 
    test_suite = "test.DebuggerTests",

    description = "Enhanced Python debugger.",
    long_description = """Enhanced Python debugger.
    Like pdb, but has more inspection commands, colorized output, command
    history.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


