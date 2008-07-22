#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys, os

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from pycopia import proctools
from glob import glob


NAME = "pycopia-vim"
VERSION = "1.0a3"

ENAME = NAME.replace("-", "_")
DNAME = NAME.split("-", 1)[-1]

# Get the VIM value from vim, which is were we need to put the .vim files.
# There's got to be a better way..., but this screen-scraping program
# works, and also demonstrates the Pycopia proctools module ;-).
def get_vimvar():
    proc = proctools.spawnpty("vim")
    proc.write(":echo $VIM\r")
    proc.write(":exit\r")
    var = proc.read()
    proc.wait()
    proctools.remove_procmanager()
    start = 0
    s = []
    for c in var:
        if not start:
            if c != "/": # find start of path.
                continue
            else:
                start = 1
        if c.isalnum() or c.isspace() or c == "/":
            s.append(c)
        else:
            break
    return "".join(s)

def get_vimfiles():
    VIM = get_vimvar()
    vimfiles = os.path.join(VIM, "vimfiles")
    vimsyntax = os.path.join(VIM, "vimfiles", "syntax")
    vimcolors = os.path.join(VIM, "vimfiles", "colors")

    return [(vimfiles, glob("vimfiles/*.vim") + 
                      glob("vimfiles/*.c") + 
                      glob("vimfiles/*.html") + 
                      glob("vimfiles/*.py") ),
            (vimcolors, glob("vimfiles/colors/*")),
            (vimsyntax, glob("vimfiles/syntax/*")),
           ]

datafiles = get_vimfiles()

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.vimlib"],
    test_suite = "test.VimTests",
    data_files = datafiles,
    scripts = glob("bin/*"), 
    install_requires = ['pycopia-process>=1.0a1,==dev', 'pycopia-WWW>=1.0a1,==dev'],

    description = "Extend Vim with Python helpers for Python IDE functionality.",
    long_description = """Extend Vim with Python helpers for Python IDE functionality.
    Includes enhanced syntax files, color scheme, and key mappings for
    Python development with the vim editor.
    """,
    license = "LGPL",
    author = "Keith Dart",
    author_email = "keith@kdart.com",
    keywords = "pycopia vim framework",
    url = "http://www.pycopia.net/",
    download_url = "http://pycopia.googlecode.com/svn/trunk/%s#egg=%s-dev" % (DNAME, ENAME),
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX", 
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)


