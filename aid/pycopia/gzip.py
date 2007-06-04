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

"""Functions that read and write gzipped streams.

The user of the file doesn't have to worry about the compression,
but random access is not allowed.

Based on the standard gzip module. That module requires a seekable file. 
This module buffers data and is useful for decompressing streams.

This module can also handle multiple segments.

Useful for sockets. supports reading only. 

TODO: writing has not been tested.

"""

import os, time
import struct
import zlib

from pycopia import UserFile

__all__ = ["GzipFile", "open"]

FTEXT, FHCRC, FEXTRA, FNAME, FCOMMENT = 1, 2, 4, 8, 16

READ, WRITE = 1, 2

class GzipError(RuntimeError):
    pass


_OS_TYPES = {
    0: "FAT filesystem (MS-DOS, OS/2, NT/Win32)",
    1: "Amiga",
    2: "VMS (or OpenVMS)",
    3: "Unix",
    4: "VM/CMS",
    5: "Atari TOS",
    6: "HPFS filesystem (OS/2, NT)",
    7: "Macintosh",
    8: "Z-System",
    9: "CP/M",
    10: "TOPS-20",
    11: "NTFS filesystem (NT)",
    12: "QDOS",
    13: "Acorn RISCOS",
    255: "unknown",
}

class GzipHeader(object):
    MAGIC = '\x1f\x8b'
    def __init__(self):
#       self.magic = None # two bytes
        self.method = 8 # one byte
        self.flags = 0 # one byte
        self.text = 0 # represents FTEXT flag
        self.mtime = long(time.time()) # four bytes
        self.extraflag = 0 # one byte
        self.os = 255 # one byte, default unknown
        self.extra = "" # variable (not implemented)
        self.name = "" # variable
        self.comment = "" # variable
        self.hcrc = None # two bytes

    def __str__(self):
        s = []
        s.append("     name: %s" % (self.name))
        s.append("       os: %s (%s)" % (self.os, _OS_TYPES.get(self.os, "bogusvalue")))
        s.append("  comment: %s" % (self.comment))
        s.append("   method: %s" % (self.method))
        s.append("  is text: %s" % (self.text))
        s.append("    mtime: %s" % (time.ctime(self.mtime)))
        s.append("    flags: %s" % (self.flags))
        s.append("extraflag: %s" % (self.extraflag))
        s.append("    extra: %s" % (self.extra))
        s.append("     hcrc: %s" % (self.hcrc))
        return "\n".join(s)

    def read(self, gzf):
        buf = gzf.read_raw(10) # optimize reads for fixed header part
        magic = buf[0:2]
        if magic != self.MAGIC:
            raise GzipError, 'Not a gzipped file'
        method = ord( buf[2] )
        if method != 8:
            raise GzipError, 'Unknown compression method'
        self.method = method
        self.flags = ord( buf[3] )
        self.text = self.flags & FTEXT
        self.mtime = struct.unpack("<L", buf[4:8])[0]
        self.extraflag = ord(buf[8])
        self.os = ord(buf[9])

        flag = self.flags
        if flag & FEXTRA:
            xlen = struct.unpack("<H", gzf.read_raw(2))[0]
            self.extra = gzf.read_raw(xlen)
        if flag & FNAME:
            fn = []
            while (1):
                s=gzf.read_raw(1)
                if not s or s=='\000':
                    break
                fn.append(s)
            self.name = "".join(fn)
        if flag & FCOMMENT:
            fc = []
            while (1):
                s=gzf.read_raw(1)
                if not s or s=='\000':
                    break
                fc.append(s)
            self.comment = "".join(fc)
        if flag & FHCRC:
            self.hcrc = struct.unpack("<H", gzf.read_raw(2))[0]

    def write(self, fo):
        flags = 0
        if self.extra:
            flags = flags | FEXTRA
        if self.name:
            flags = flags | FNAME
        if self.comment:
            flags = flags | FCOMMENT
        if self.hcrc: # XXX compute this
            flags = flags | FHCRC
        fixed = struct.pack("<2sBBLBB", self.MAGIC, self.method, flags, 
                        self.mtime, self.extraflag, self.os)
        fo.write_raw(fixed)
        if self.extra:
            fo.write_raw(struct.pack("<H", len(self.extra)))
            fo.write_raw(self.extra)
        if self.name:
            fo.write_raw("%s\0" % (self.name))
        if self.comment:
            fo.write_raw("%s\0" % (self.comment))
        if self.hcrc:
            fo.write_raw(struct.pack("<H", len(self.hcrc)))

    def set_comment(self, text):
        self.comment = str(text)

    def set_name(self, text):
        self.name = str(text)



# a Gzip stream reader that does not require a seekable file.
class GzipFile(UserFile.FileWrapper):
    def __init__(self, fo, mode="r", compresslevel=6, header=None):
        super(GzipFile, self).__init__(fo)
        self.compresslevel = compresslevel
        self.eof = 0
        self._buf = ""
        self._bufsize = 0
        self._rawq = ""
        self._rawqsize = 0
        self.segments = 0
        # check mode and initialize
        if mode[0] in "wa":
            self._mode = WRITE
            self._init_write(header)
        elif mode[0] == "r":
            self._mode = READ
            self._init_read()
        else:
            raise ValueError, "GzipFile: unknown file mode."


    def new_segment(self, header):
        if self._mode == WRITE:
            rest = self.compress.flush()
            if rest:
                self._write(rest)
            self.write32(self.crc)
            self.write32(self.segsize)
            header.write(self)
            self._init_write()
            self.segments += 1


    def __repr__(self):
        return '<GzipFile open on fd %r id:%x>' % (self._fd, id(self))

    def close(self):
        if self._mode == WRITE:
            rest = self.compress.flush()
            if rest:
                self._write(rest)
            self.write32(self.crc)
            self.write32(self.segsize)
        super(GzipFile, self).close()

    def _init_write(self, header):
        self.crc = zlib.crc32("")
        self.segsize = 0
        if not header:
            header = GzipHeader() # take default values
            header.set_name("<unknown>")
        header.write(self)
        self.header = header
        self.compress = zlib.compressobj(self.compresslevel)

    def _init_read(self):
        self.crc = zlib.crc32("")
        self.segsize = 0
        self.decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        self.header = GzipHeader()
        self.header.read(self)

    def _process_rawq(self):
        data = self.decompress.decompress(self._rawq)
        self._add_read_data(data)
        self._rawq = ""
        self._rawqsize = 0
        if self.decompress.unused_data:
            # Ending case: we've come to the end of a member in the file.
            self.segments += 1
            self._check_end()
    
    def _check_end(self):
        # Check the CRC and file size, and set the new_memeber flag so we read
        # a new member on the next call.
        left = self.decompress.unused_data
        if len(left) < 8:
            left += self.read_raw(8-len(left)) # read fell on trailer boundary
        crc32 = struct.unpack("<l", left[0:4])[0]
        isize = struct.unpack("<l", left[4:8])[0]
        self._rawq = left[8:]
        self._rawqsize = len(self._rawq)
        # verify crc check and size
        if crc32 % 0x100000000L != self.crc % 0x100000000L:
            raise GzipError, "CRC check failed"
        elif isize != self.segsize:
            raise GzipError, "Incorrect length of data produced"
        # if there is more raw data left, there must be another segment
        if self._rawq:
            self._init_read()

    def _add_read_data(self, data):
        self.crc = zlib.crc32(data, self.crc)
        self.segsize += len(data)
        self._buf += data
        self._bufsize += len(data)

    def _add2raw(self, data):
        self._rawq += data
        self._rawqsize += len(data)

    def read(self, amt=2147483646):
        if self._rawq:
            self._process_rawq()
            return self._read_uncompressed(amt)
        
        while not self.eof and self._bufsize <= amt:
            buf = super(GzipFile, self).read(min(4096, amt)) # read compressed data, may block
            if not buf:
                self.eof = 1
            else:
                self._add2raw(buf)
                self._process_rawq()
        return self._read_uncompressed(amt)

    def _read_uncompressed(self, amt):
        if amt >= self._bufsize:
            buf = self._buf
            self._buf = ""
            self._bufsize = 0
            return buf
        else:
            buf = self._buf[:amt]
            self._buf = self._buf[amt:]
            self._bufsize -= amt
            return buf

    # read from the rawq or file
    def read_raw(self, amt=2147483646):
        while not self.eof and self._rawqsize < amt:
            buf = super(GzipFile, self).read(min(4096, amt)) # read compressed data, may block
            if not buf:
                self.eof = 1
            else:
                self._add2raw(buf)
        return self._read_rawq(amt)

    def _read_rawq(self, amt=2147483646):
        if amt >= self._rawqsize:
            buf = self._rawq
            self._rawq = ""
            self._rawqsize = 0
            return buf
        else:
            buf = self._rawq[:amt]
            self._rawq = self._rawq[amt:]
            self._rawqsize -= amt
            return buf

    #write methods

    def write32(self, value):
        self._write(struct.pack("<l", value))

    def write32u(self, value):
        if value < 0:
            value = value + 0x100000000L
        self._write(struct.pack("<L", value))

    # writes data out compressed
    def write(self, data):
        if self._mode == WRITE:
            self.segsize += len(data)
            self.crc = zlib.crc32(data, self.crc)
            data = self.compress.compress(data)
            self._write(data)
        else:
            raise GzipError, "trying to write to stream in READ mode."

    # writes data out uncompressed
    def write_raw(self, data):
        if self._mode == WRITE:
            self._write(data)
        else:
            raise GzipError, "trying to write to stream in READ mode."


### open factory function

def open(name, mode="r", compresslevel=9, header=None):
    #flags = UserFile.mode2flags(mode)
    #fd = os.open(name, flags)
    fo = open(name, mode)
    return GzipFile(fo, mode, compresslevel, header)

