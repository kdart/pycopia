#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Translate paths to and from various platforms.

Using cygwin on Windows presents the small problem of translating NT paths to
cygwin paths for some applications.

"""
import ntpath, posixpath

from pycopia.aid import IF

def unix2win(path):
    return path.replace("/", "\\")

def win2unix(path):
    return path.replace("\\", "/")

def nt2cygwin(winpath):
    if winpath.find(":") > 0:
        [drive, path] = winpath.split(":", 1)
        return "/cygdrive/%s%s%s" % (drive.lower(), IF(path.startswith("\\"), "", "/"), path.replace("\\", "/"))
    else:
        return "/cygdrive/c%s%s" % (IF(winpath.startswith("\\"), "", "/"), winpath.replace("\\", "/")) # assume C: drive if not given
win2cygwin = nt2cygwin # alias


def cygwin2nt(path):
    parts = path.split("/")
    if path.startswith("/cygdrive"):
        return "%s:\\%s" % (parts[2].upper(), ntpath.join(*tuple(parts[3:])))
    elif not parts[0]: # empty is root
        return ntpath.join("C:\\cygwin", *tuple(parts))
    else:
        return ntpath.join(*tuple(parts))


def _test(argv):
    print cygwin2nt("/cygdrive/c/tmp"), "C:\\tmp"
    print cygwin2nt("/usr/bin"), "C:\\cygwin\\usr\\bin"
    print cygwin2nt("usr/bin"), "usr\\bin"
    print nt2cygwin("C:\\share\\dir1"), "/cygdrive/c/share/dir1"
    print nt2cygwin("\\Program Files\\dir1"), "/cygdrive/c/Program Files/dir1"
    print nt2cygwin("\\share\\dir1"), "/cygdrive/c/share/dir1"

if __name__ == "__main__":
    import sys
    _test(sys.argv)

