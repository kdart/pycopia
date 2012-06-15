#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


from glob import glob
from setuptools import setup

NAME = "pycopia-SNMP"
VERSION = "1.0"


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.SNMP", "pycopia.Devices"],
#    install_requires = ['pycopia-mibs>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    package_data = {
        'pycopia.Devices': ['*.txt'],
    },
    scripts = glob("bin/*"),
    test_suite = "test.SNMPTests",

    description = "SNMP protocol module for Python.",
    long_description = """SNMP protocol module for Python.
    Provides SNMP query, traps, and device manager objects.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework SNMP",
    url = "http://www.pycopia.net/",
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


