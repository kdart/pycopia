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
Managing logfile rotation. A ManagedLog object is a file-like object that
rotates itself when a maximum size is reached.

"""

import sys, os

if sys.version_info.major == 3:
    import io
    file = io.FileIO

class SizeError(IOError):
    pass

class LogFile(file):
    """LogFile(name, [mode="w"], [maxsize=360000])
    Opens a new file object. After writing <maxsize> bytes a SizeError will be
    raised.  """
    def __init__(self, name, mode="w", maxsize=360000):
        super(LogFile, self).__init__(name, mode)
        self.maxsize = maxsize
        self.written = 0

    def write(self, data):
        self.written += len(data)
        super(LogFile, self).write(data)
        self.flush()
        if self.written > self.maxsize:
            raise SizeError

    def rotate(self):
        return rotate(self)

    def note(self, text):
        """Writes a specially formated note text to the file.The note starts
with the string '\\n#*=' so you can easily filter them. """
        self.write("\n#*===== %s =====\n" % (text,))


class ManagedLog(object):
    """ManagedLog(name, [maxsize=360000], [maxsave=9])
    A ManagedLog instance is a persistent log object. Write data with the
    write() method. The log size and rotation is handled automatically.

    """
    def __init__(self, name, maxsize=360000, maxsave=9):
        if os.path.isfile(name):
            shiftlogs(name, maxsave)
        self._lf = LogFile(name, "w", maxsize)
        self.maxsave = maxsave

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__, self._lf.name, self._lf.maxsize, self.maxsave)

    def write(self, data):
        try:
            self._lf.write(data)
        except SizeError:
            self._lf = rotate(self._lf, self.maxsave)

    def note(self, data):
        try:
            self._lf.note(data)
        except SizeError:
            self._lf = rotate(self._lf, self.maxsave)

    def written(self):
        return self._lf.written

    def rotate(self):
        self._lf = rotate(self._lf, self.maxsave)

    # auto-delegate remaining methods (but you should not read or seek an open
    # log file).
    def __getattr__(self, name):
        return getattr(self._lf, name)


# useful for logged stdout for daemon processes
class ManagedStdio(ManagedLog):
    def write(self, data):
        try:
            self._lf.write(data)
        except SizeError:
            sys.stdout.flush()
            sys.stderr.flush()
            self._lf = rotate(self._lf, self.maxsave)
            fd = self._lf.fileno()
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            sys.stdout = sys.stderr = self


def rotate(fileobj, maxsave=9):
    name = fileobj.name
    mode = fileobj.mode
    maxsize = fileobj.maxsize
    fileobj.close()
    shiftlogs(name, maxsave)
    return LogFile(name, mode, maxsize)


# assumes basename logfile is closed.
def shiftlogs(basename, maxsave):
    topname = "%s.%d" % (basename, maxsave)
    if os.path.isfile(topname):
        os.unlink(topname)

    for i in range(maxsave, 0, -1):
        oldname = "%s.%d" % (basename, i)
        newname = "%s.%d" % (basename, i+1)
        try:
            os.rename(oldname, newname)
        except OSError:
            pass
    try:
        os.rename(basename, "%s.1" % (basename))
    except OSError:
        pass


def open(name, maxsize=360000, maxsave=9):
    return ManagedLog(name, maxsize, maxsave)

def writelog(logobj, data):
    try:
        logobj.write(data)
    except SizeError:
        return rotate(logobj)
    else:
        return logobj




