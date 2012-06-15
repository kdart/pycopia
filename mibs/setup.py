#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


from setuptools import setup

NAME = "pycopia-mibs"
VERSION = "1.0"


setup(name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.mibs"],
#    install_requires = ['pycopia-SMI>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    test_suite = "test.MibsTests",
    zip_safe = True,

    description = "Collection of pre-compiled MIBs for Pycopia SNMP.",
    long_description = """Collection of pre-compiled MIBs for Pycopia SNMP.
    These are generated Python modules, produced by mib2py program.""",
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia framework MIB SMI",
    url = "http://www.pycopia.net/",
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)

