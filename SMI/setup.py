#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import ez_setup
ez_setup.use_setuptools()

from glob import glob
from setuptools import setup, Extension 

NAME = "pycopia-SMI"
VERSION = "0.9.4"


_libsmi = Extension("_libsmi", ["libsmi_wrap.c"], libraries=["smi"])

setup (name=NAME, version=VERSION,
    ext_modules = [_libsmi],
    py_modules = ["libsmi"], # stock SWIG wrapper
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.SMI"],       # custom Python wrapper - use this one.
    install_requires = ['pycopia-aid>=0.9'],
    scripts = glob("bin/*"), 
    zip_safe = False,
    test_suite = "test.SMITests",

    author = "Keith Dart",
    author_email = "keith@kdart.com",
    description = "Python wrapper for libsmi, providing access to MIB/SMI data files.",
    long_description = """Python wrapper for libsmi, providing access to MIB/SMI data files.
    Also provides a nicer API that is more object-oriented. Includes node interators.""",
    license = "LGPL",
    keywords = "SMI MIB SNMP",
    url = "http://www.pycopia.net/",
    download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: System :: Networking :: Monitoring",
                   "Intended Audience :: Developers"],
)


