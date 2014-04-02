#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys, os

from setuptools import setup
from glob import glob


NAME = "pycopia-vim"
VERSION = "1.0"


# Get the VIM value from vim, which is were we need to put the .vim files.
# There's got to be a better way..., but this screen-scraping program
# works, and also demonstrates the Pycopia proctools module ;-).
def get_vimvar():
    from pycopia import proctools
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

    return [(vimfiles, glob("vimfiles/*.vim")),
            (vimcolors, glob("vimfiles/colors/*")),
            (vimsyntax, glob("vimfiles/syntax/*")),
           ]

if sys.platform not in ("win32", "cli"):
    try:
        DATA_FILES = get_vimfiles()
    except (ImportError, AttributeError):
        DATA_FILES = []
else:
    DATA_FILES = []

setup (name=NAME, version=VERSION,
    namespace_packages = ["pycopia"],
    packages = ["pycopia", "pycopia.vimlib"],
    test_suite = "test.VimTests",
    zip_safe=False, # vim can't import from zip file.
    data_files = DATA_FILES,
    scripts = glob("bin/*"),
#    install_requires = [
#            'pycopia-process>=1.0.dev-r138,==dev',
#            'pycopia-WWW>=1.0.dev-r138,==dev'],
    dependency_links = [
            "http://www.pycopia.net/download/"
                ],

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
    #download_url = "ftp://ftp.pycopia.net/pub/python/%s.%s.tar.gz" % (NAME, VERSION),
    classifiers = ["Operating System :: POSIX",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Intended Audience :: Developers"],
)

if not DATA_FILES:
    print ("Be sure to take a look at the files in vimfiles directory "
    "and copy them to your preferred vimfiles location.")

