#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Translate paths to and from various platforms.

Using cygwin on Windows presents the small problem of translating NT paths to
cygwin paths for some applications.

"""
from __future__ import print_function

import ntpath, posixpath


def unix2win(path):
    return path.replace("/", "\\")

def win2unix(path):
    return path.replace("\\", "/")

def nt2cygwin(winpath):
    if winpath.find(":") > 0:
        [drive, path] = winpath.split(":", 1)
        return "/cygdrive/%s%s%s" % (drive.lower(), ("" if path.startswith("\\") else "/"), path.replace("\\", "/"))
    else:
        return "/cygdrive/c%s%s" % (("" if winpath.startswith("\\") else "/"), winpath.replace("\\", "/")) # assume C: drive if not given
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
    print(cygwin2nt("/cygdrive/c/tmp"), "C:\\tmp")
    print(cygwin2nt("/usr/bin"), "C:\\cygwin\\usr\\bin")
    print(cygwin2nt("usr/bin"), "usr\\bin")
    print(nt2cygwin("C:\\share\\dir1"), "/cygdrive/c/share/dir1")
    print(nt2cygwin("\\Program Files\\dir1"), "/cygdrive/c/Program Files/dir1")
    print(nt2cygwin("\\share\\dir1"), "/cygdrive/c/share/dir1")

if __name__ == "__main__":
    import sys
    _test(sys.argv)

