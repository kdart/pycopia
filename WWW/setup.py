#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys, os
from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-WWW"
VERSION = "1.0"


import platutils
platinfo = platutils.get_platform()

if platinfo.is_linux():

    WEBSITE = os.environ.get("WEBSITE", "localhost")

    DATAFILES = [
        ('/etc/pycopia', glob("etc/*.example") + glob("etc/*.dist")),
        ('/etc/pycopia/ssl', glob("etc/ssl/*")),
        ('/etc/pycopia/lighttpd', glob("etc/lighttpd/*")),
        (os.path.join(sys.prefix, 'libexec', 'pycopia'), glob("libexec/*")),
    ]
    if platinfo.is_gentoo():
        DATAFILES.append(('/etc/init.d', glob("etc/init.d/gentoo/*")))
    elif platinfo.is_redhat():
        DATAFILES.append(('/etc/init.d', glob("etc/init.d/redhat/*")))

    DATAFILES.extend([
        (os.path.join("/var", "www", WEBSITE, 'media', 'js'), glob("media/js/*.js")),
        (os.path.join("/var", "www", WEBSITE, 'media', 'css'), glob("media/css/*.css")),
        (os.path.join("/var", "www", WEBSITE, 'media', 'images'), glob("media/images/*.png")),
        #(os.path.join("/var", "www", WEBSITE, 'media', 'images'), glob("media/images/*.jpg")),
    ])
    SCRIPTS = glob("bin/*")
else:
    DATAFILES = []
    SCRIPTS = []


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
#    install_requires = [
#            'pycopia-XML>=1.0.dev-r138,==dev',
#            'simplejson>=1.0,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    data_files = DATAFILES,
    scripts = SCRIPTS,
    test_suite = "test.WWWTests",

    description = "Pycopia WWW tools and web application framework.",
    long_description = """Pycopia WWW tools and web application framework.
    Provides FCGI servers, XHTML page generator with functional style
    interfaces, XHTML generator objects, and lightweight web application
    framework. Some support for WML as well. Designed to work closely with
    the lighttd front-end server via the FCGI interface. You may run any
    number of FCGI handlers, each in its own process with its own user ID
    and associated permissions. Generally, supports a design comprised of
    a set of JSON handlers with the expectation that the web application
    will be mostly provided by Javascript on the client side.  The
    framework also works with Google's web application engine.""",
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia WWW framework XHTML FCGI WSGI",
    url = "http://www.pycopia.net/",
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
                   "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
                   "Topic :: Software Development :: Quality Assurance",
                   "Intended Audience :: Developers"],
)

