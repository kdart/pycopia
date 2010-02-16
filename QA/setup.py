#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


import sys
import os

import ez_setup
ez_setup.use_setuptools()

import platutils

from glob import glob
from setuptools import setup, find_packages

NAME = "pycopia-QA"
VERSION = "1.0"
REVISION="$Revision$"

DNAME = NAME.split("-", 1)[-1]
EGGNAME = "%s-%s.dev_r%s" % (NAME.replace("-", "_"), VERSION, REVISION[1:-1].split(":")[-1].strip())

platinfo = platutils.get_platform()
CACHEDIR="/var/cache/pycopia"

# Some services, such as the Pyro nameserver, are set up to run as the
# "tester" psuedo-user.  This also creates the "tester" group that testing
# personnel should also be a member of.
def system_setup():
    if platinfo.is_linux():
        import os, pwd
        if os.getuid() == 0:
            if platinfo.is_gentoo():
                try:
                    pwent = pwd.getpwnam("tester")
                except KeyError:
                    os.system("useradd -c Tester " 
                    "-G users,uucp,audio,cdrom,dialout,video,games,usb,crontab,messagebus,plugdev " 
                    "-m -U tester") # also creates tester group
                    print "Change password for new user tester:"
                    os.system("passwd tester")
                    pwent = pwd.getpwnam("tester")
                if not os.path.isdir(CACHEDIR):
                    os.mkdir(CACHEDIR)
                    os.chown(CACHEDIR, pwent.pw_uid, pwent.pw_gid)
                    os.chmod(CACHEDIR, 0770)


if platinfo.is_linux():
    DATA_FILES = [
            ('/etc/pycopia', glob("etc/*.dist")),
    ]
    if platinfo.is_gentoo():
        DATA_FILES.append(('/etc/init.d', glob("etc/init.d/gentoo/*")))
    elif platinfo.is_redhat():
        DATA_FILES.append(('/etc/init.d', glob("etc/init.d/redhat/*")))
    SCRIPTS = glob("bin/*")

    WEBSITE = os.environ.get("WEBSITE", "localhost")
    DATA_FILES.extend([
        #(os.path.join("/var", "www", WEBSITE, 'htdocs'), glob("doc/html/*.html")),
        #(os.path.join("/var", "www", WEBSITE, 'cgi-bin'), glob("doc/html/cgi-bin/*.py")),
        #(os.path.join("/var", "www", WEBSITE, 'media', 'js'), glob("media/js/*.js")),
        (os.path.join("/var", "www", WEBSITE, 'media', 'css'), glob("media/css/*.css")),
        #(os.path.join("/var", "www", WEBSITE, 'media', 'images'), glob("media/images/*.png")),
    ])

else:
    DATA_FILES = []
    SCRIPTS = []


setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = find_packages(),
    install_requires = [
        'pycopia-CLI>=1.0.dev-r138,<=dev',
        'pycopia-storage>=1.0.dev-r138,<=dev', 
        'pycopia-WWW>=1.0.dev-r279,<=dev',
        'docutils>=0.5',
        'Pyro>=3.9',
        ],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],
    scripts = SCRIPTS,
    data_files = DATA_FILES,
    test_suite = "test.QATests",

    description = "Pycopia packages to support professional QA roles.",
    long_description = """Pycopia packages to support professional QA roles.
    A basic QA automation framework. Provides base classes for test cases,
    test suites, test runners, reporting, lab models, terminal emulators,
    remote control, and other miscellaneous functions.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@dartworks.biz",
    keywords = "pycopia QA framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s" % (DNAME, EGGNAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Topic :: Software Development :: Quality Assurance",
                   "Intended Audience :: Developers"],
)


if "install" in sys.argv:
    system_setup()

