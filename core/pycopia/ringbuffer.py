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
Defines a RingBuffer object that act as character/byte buffers.

"""

import mmap

# get an anonymous mmap range. Only works on Linux (possibly other Unix)
def _get_buf(size):
    _buf = mmap.mmap(-1, size, flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS,
                    prot=mmap.PROT_READ|mmap.PROT_WRITE )
    _buf.seek(0,2) # move seek pointer to end
    return _buf


class RingBuffer(object):
    """RingBuffer([size])
    Return a character oriented ring buffer with read and write methods.

    """
    def __init__(self, size=8192):
        self.size = size
        self._buf = _get_buf(size)
        self._full = 0
        self._bot = 0
        self._top = 0

    def __str__(self):
        return self.getvalue()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.size)

    def reset(self):
        self._bot = 0
        self._top = 0
        self._buf.seek(0)

    def getvalue(self):
        t, b, s = self._top, self._bot, self.size
        if t >= b:
            return self._buf[b:t]
        else:
            return self._buf[b:] + self._buf[:t]

    def getrawvalue(self):
        return buffer(self._buf)

    def __len__(self):
        t, b, s = self._top, self._bot, self.size
        return (t + (t < b)*s) - b

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __iadd__(self, seq):
        self.write(seq)
        return self

    def close(self):
        self._buf.close()
        self._buf = None

    def headroom(self):
        t, b, s = self._top, self._bot, self.size
        return s - ((t + (t < b)*s) - b)

    def seek(self, pos, whence=0):
        t, b, bs = self._top, self._bot, self.size
        if whence == 0: # "seeking" from start moves up bottom ptr
            pos = min((t + (t < b)*bs) - b, pos) # pos truncated to length of data
            wrap, i = divmod(b+pos, bs)
            self._bot = i
            self._buf.seek(i, 0)

        elif whence == 1:
            raise IOError("ring buffer has no current position.")

        elif whence == 2: # seeking backwards from top moves bottom ptr up
            assert pos < 0
            n = t+pos
            if n <= 0:
                n += bs
            self._bot = n
            self._buf.seek(n,0)
        else:
            raise IOError("whence must be 0 or 2.")

    def find(self, string, start=0):
        t, b, bs = self._top, self._bot, self.size
        if b+start < t:
            i = self._buf.find(string, b+start)
            if i >= 0:
                return b + i
            else:
                return i # should be -1
        else: # deal with wrapping
            i = self._buf.find(string, b+start)
            if i >= 0:
                return i - b
            i = self._buf.find(string, 0)
            if i >= 0:
                return (bs - b) + i
            else:
                return i

    def read(self, amt=2147483646):
        t, b, bs = self._top, self._bot, self.size
        l = (t + (t < b)*bs) - b
        amt = min(l, amt)
        wrap, i = divmod(b+amt, bs)
        if wrap:
            rv = self._buf[b:] + self._buf[:i]
        else:
            rv = self._buf[b:b+amt]
        self._bot = i
        self._full = 0
        return rv

    def write(self, seq):
        t, b, bs = self._top, self._bot, self.size
        l = (t + (t < b)*bs) - b
        ls = len(seq)
        self._full = bs <= (l + 1)

        # special case where the write is larger than the buffer
        # if we are going to write a sequence that is a multiple of the
        # bufsize, we really only need to write the remaining tail.
        if ls > bs:
            self._buf[:-1] = seq[-(bs-1):] # just reset everything
            self._bot = 0 ; self._top = bs-1
            self._buf.seek(0, 0)
            return
        # now, figure if it wrapped, and write it in.
        wrap, i = divmod(t+ls, bs)
        if wrap:
            self._buf[t:] = seq[:ls-i]
            self._buf[:i] = seq[ls-i:]
        else:
            self._buf[t:i] = seq
        if self._full:
            pos = (b + ls) % bs
            self._bot = pos
        self._top = i

    def readline(self):
        i = self.find("\n")
        if i >= 0:
            return self.read(i+1)
        else:
            return self.read()

    def readlines(self, sizehint=None):
        rv = []
        line = self.readline()
        while line:
            rv.append(line)
            line = self.readline()
        return rv



