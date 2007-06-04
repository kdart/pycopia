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
Support for MD5 checking.

"""

import sys, os
import md5

if sys.platform == "win32":
    UserFile = file
else:
    from pycopia.UserFile import UserFile # signal protected file

from pycopia.aid import Enum, IF

# check modes
Binary = Enum(1, "*")
Text = Enum(0, " ")


# a file containing md5sum data that is compatible with the GNU md5sum program.
class SumFile(UserFile):
    def write_record(self, digest, binary, fname):
        if "\\" in fname or "\n" in fname:
            self.write("\\")
        self.write("%s %s%s\n" % (digest, IF(binary, "*", " "), repr(fname)[1:-1]))

    def read_record(self):
        escaped = 0
        line = self.readline()
        if not line:
            return "", Binary, ""
        line = line.strip()
        if line.startswith("\\"):
            escaped = 1
            line = line[1:]
        digest = line[:32]
        assert line[32] == " "
        if line[33] == "*":
            mode = Binary
        else:
            mode = Text
        if escaped:
            fname = eval('"%s"' % line[34:])
        else:
            fname = line[34:]
        return digest, mode, fname

    def read_records(self):
        while 1:
            d, mode, fname = self.read_record()
            if d:
                yield d, mode, fname
            else:
                raise StopIteration


def md5sum(filename, mode=Binary):
    m = md5.new()
    f = open(filename, IF(mode, "rb", "r"))
    b = f.read(4096)
    while b:
        m.update(b)
        b = f.read(4096)
    return m.hexdigest()

def compare_md5(filename, chash, mode):
    fhash = md5sum(filename, mode)
    return fhash == chash

def _default_failure(fname):
    print >>sys.stdout, "!!! problem with file '%s/%s'!" % (os.getcwd(), fname,)

def _verbose_progress(name, disp):
    print name, IF(disp, "OK", "ERROR")

# recurse into subdirectories checking the md5sums.txt files.
def check_md5sums_all(root=None, failure_cb=_default_failure, progress_cb=None):
    if root is None:
        root = os.getcwd()
    check_md5sums(root, failure_cb, progress_cb)
    names = os.listdir(root)
    for name in names:
        if os.path.isdir(name):
            if progress_cb:
                progress_cb("\nChecking directory: %r" %(name,), 1)
            check_md5sums_all(os.path.join(root, name), failure_cb, progress_cb)

def check_md5sums(root=None, failure_cb=_default_failure, progress_cb=None):
    # opens the text file as produced by the md5sum program
    if root is None:
        savedir = root = os.getcwd()
    else:
        savedir = os.getcwd()
        os.chdir(root)
    try:
        try:
            sumfile = SumFile("md5sums.txt")
        except IOError:
            if progress_cb: # verbose...
                print >>sys.stderr, "No md5sums.txt file found in %r" % (os.getcwd(),)
            return # skip directories that don't have an md5sums.txt file
        for chash, mode, fname in sumfile.read_records():
            try:
                disp = compare_md5(fname, chash, mode)
            except IOError, err:
                failure_cb("%s: %s" % (fname, err))
                continue

            if progress_cb:
                progress_cb(fname, disp)
            if not disp:
                failure_cb(fname)
    finally:
        os.chdir(savedir)

def make_md5sums(filelist=None, progress_cb=None, mode=Binary):
    if filelist is None:
        filelist = filter(os.path.isfile, os.listdir(os.getcwd()))
        try:
            filelist.remove("md5sums.txt")
        except ValueError:
            pass
    sumfile = SumFile("md5sums.txt", "w")
    try:
        for fname in filelist:
            try:
                mdhash = md5sum(fname, mode)
            except IOError:
                print >>sys.stderr, "No file named '%s' found." % (fname, )
                continue
            if progress_cb:
                progress_cb(fname, 1)
            sumfile.write_record(mdhash, mode, fname)
    finally:
        sumfile.close()

def make_md5sums_all(root=None, progress_cb=None, mode=Binary):
    if root is None:
        root = os.getcwd()
    names = os.listdir(root)
    filelist = filter(os.path.isfile, names)
    make_md5sums(filelist, progress_cb, mode)
    try:
        for name in names:
            if os.path.isdir(name):
                if progress_cb:
                    progress_cb("Making directory: %r" %(name,), 1)
                new = os.path.join(root, name)
                os.chdir(new)
                make_md5sums_all(new, progress_cb, mode)
    finally:
        os.chdir(root)

def md5sums(path):
    """Reads the md5sums.txt file in path and returns the number of files
    checked good, then number bad (failures), and a list of the failures."""
    failures = []
    counter = Counter()
    check_md5sums(path, failures.append, counter)
    return counter.good, counter.bad, failures

# md5sums callback for counting files
class Counter(object):
    def __init__(self):
        self.good = 0
        self.bad = 0

    def __call__(self, name, disp):
        if disp:
            self.good += 1
        else:
            self.bad += 1

