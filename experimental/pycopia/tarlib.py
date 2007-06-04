#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 

"""
tarlib.py 0.1 (c) C.Hintze 10mar1998

This library provides classes for accessing tarfiles. As test and demo prog,
it realizes a far-not-complete tar command.

You can use it under the same conditions like Python itself.

I have tested it with tarfiles created with the tar command coming with
Solaris 2.5.1, and GNU Tar 1.11.8 for some days.

You can use it under the same conditions like Python itself.

Now coming to the warranty. There is no warranty! Never and in no case ;-)

Copyright notice
================

This source is copyrighted, but you can freely use and copy it as long as you
don't change or remove the copyright notice:

I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I BE LIABLE FOR
ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


To-do:
    - Work on sparse files known under GNU Tar.
    - Add __setitem__ and __setslice__ methods.
    - Add update method
    - Improve the cache mechanism.
    - Speed-up the deletion of entries.
    - Delete should not delete all items with the same key from the
      archive, but the last one.


Bugs:
    - If you have not cached the archive, _gotokey will goto the FIRST item
      with filename == key. Whereas if you use cached access, the LAST item
      would be found.
    - Therefore __getkey() will deliver the LAST item with that
      name of the archive if cached, the first one otherwise.

    There are certainly a mass of further bugs, only I am to lazy to find them.
    If you encounter an bug, please inform me at:

                  mailto:clemens.hintze@bln.sel.alcatel.de.

    Describe what you have tried to do, and the contents of the version string
    contained in the variable version on top of the file.
    Please do not forget to attach your tarfile that will cause the troubles.
    If the tarfiles is to large, try to construct a smaller one, which also
    will produce this kind of error.
"""

version = "$Version$"

import os, stat, string, time, types
import grp, pwd, StringIO


# Size constants of some header member
RECORDSIZE     = 512
NAMSIZ         = 100
TUNMLEN        = 32
TGNMLEN        = 32
SPARSE_EXT_HDR = 21
SPARSE_IN_HDR  = 4

# Magic filler constant.
TMAGIC         = 'ustar\0\0\0'        # 7 chars and a null

# Linkflag constants
LF_OLDNORMAL   = '\0'    # normal disk file, Unix compat
LF_NORMAL      = '0'     # normal disk file
LF_LINK        = '1'     # link to previously dumped file
LF_SYMLINK     = '2'     # symbolic link
LF_CHR         = '3'     # character special file
LF_BLK         = '4'     # block special file
LF_DIR         = '5'     # directory
LF_FIFO        = '6'     # FIFO special file
LF_CONTIG      = '7'     # contiguous file
LF_DUMPDIR     = 'D'     # Dir entry, contains name of files that where in the
                         # dir at the time the dump was made.
LF_LONGLINK    = 'K'     # NEXT file on tape have long linkname.
LF_LONGNAME    = 'L'     # NEXT file on tape have a long name
LF_MULTIVOL    = 'M'     # Continuation of file that began on other volume
LF_NAMES       = 'N'     # Contains filenames does not fit in 100 chars.
LF_SPARSE      = 'S'     # This is for sparse files.
LF_VOLHDR      = 'V'     # File is a tape/volume header.  Ignore it on extr.

# Value of chksum during computing of header chksum
CHKBLANKS      = ' ' * 8

# Bits used in the mode field - values in octal
TSUID          = 2048    # set UID on execution
TSGID          = 1024    # set GID on execution
TSVTX          = 512     # save text (sticky bit)

# File permissions
TUREAD         = 256     # read by owner
TUWRITE        = 128     # write by owner
TUEXEC         = 64      # execute/search by owner
TGREAD         = 32      # read by group
TGWRITE        = 16      # write by group
TGEXEC         = 8       # execute/search by group
TOREAD         = 4       # read by other
TOWRITE        = 2       # write by other
TOEXEC         = 1       # execute/search by other



class Error(Exception):
    pass



class TarEntry(object):
    """
    The 'TAR' objects deliver and accept only instances of that class.
    It serves mainly as a container, to held all relevant information for a
    TarEntry. 'data' have to be of an type which supports all reading and
    navigating methods like a 'FileType' or 'StringIO' instance. If during
    initialization 'data' was of type 'StringType', it will be converted
    silently to a 'StringIO' instance. To get the contents, stored in 'data',
    you can use the Python standard function str() on the instance.
    """
    def __init__(self, name='', data='', mode=TUREAD+TUWRITE, uid=0, gid=0,
                 size=-1, mtime=-1, linkflag='0', linkname='', uname='',
                 gname=''):
        if data is None:
            return
        if type(data) == types.StringType:
            data = StringIO.StringIO(data)
        elif type(data) is types.FileType:
            try:
                s = os.lstat(data.name)
            except os.error, detail:
                raise Error, detail[1]
            if name == '':
                name = data.name
            mode, uid, gid, size, mtime = s[0], s[4], s[5], s[6], s[8]
            if stat.S_ISLNK(mode):
                linkflag = LF_SYMLINK
                size = 0
            elif stat.S_ISREG(mode):
                linkflag = LF_NORMAL
            elif stat.S_ISDIR(mode):
                linkflag = LF_DIR
                size = 0
            elif stat.S_ISCHR(mode):
                linkflag = LF_CHR
            elif stat.S_ISBLK(mode):
                linkflag = LF_BLK
            elif stat.S_ISFIFO(mode):
                linkflag = LF_FIFO
            try:
                linkname = os.readlink(data.name)
            except:
                linkname = ''
            try:
                uname = pwd.getpwuid(uid)[0]
            except:
                uname = ''
            try:
                gname = grp.getgrgid(gid)[0]
            except:
                gname = ''
        if name == '':
            name = 'data'
        if size == -1:
            size = _eofpos(data)
        if mtime == -1:
            mtime = time.mktime(time.localtime(time.time()))
        self.name = name
        self.data = data
        self.mode = mode
        self.uid  = uid
        self.gid  = gid
        self.size = size
        self.mtime = mtime
        self.linkflag = linkflag
        self.linkname = linkname
        self.uname = uname
        self.gname = gname

    def __str__(self):
        return self.getdata()

    def getdata(self):
        if type(self.data) is types.StringType:
            return self.data
        self.data.seek(0, 0)
        return self.data.read()

    def setdata(self, data):
        if type(data) is types.StringType:
            data = StringIO.StringIO(data)
        self.data = data



class TAR(object):
    """
    Instances of that class are connected with a .tar FILE (sorry no tapes)!

    During creation, you may decide if the instance cache its contents or not.
    If cached, the initialization may takes a while, while later access should
    much faster than without caching. If you decide to not cache the tarfile,
    the initialization is much more quicker, but every access will be slown down
    in a magnitude. But nevertheless, if you only want to add a file, it should
    not be necessary to chache access.

    Of course, you may also use objects of type StringIO.StringIO as tarfiles.
    (BTW: One of the main reasons, why I have written this class!)

    After initialization, the instance behaves like a map (DictionaryType) AND a
    list (ListType). You may access an entry via indexing, or via keys. The keys
    are the filenames stored in that archive.

    As it behaves like a list, it is also possible to do following:

        fp = open('t.tar', 'r')
        tar = TAR(fp, cached=1)
        for entry in tar:
            print entry.name
        fp.close()

    (But look also at the method 'iterate'.)

    You may only 'append' a new 'TarEntry' to a tarfile (sorry no replacing
    yet).

    To delete an entry, simply use python's 'del' buildin like that:

        del tar[3]             # deletes the fourth entry from tarfile.
        del tar[-1]            # deletes the last entry from tarfile.
        del tar['README']      # deletes the file(s) README from archive.

    The python buildin 'len' will return the number of entries in the archive.

    The methods of that class are based on following conventions:

        __name__   - implemented to fake the instance as map or list.
        name       - directly usable by the user (public interface).
        _name      - base primitives to implement the base access mechanism
                     (protected interface).
        __name     - primitives to implement the current acess scheme (private
                     interface).
    """
    def __init__(self, fp, cached=0):
        self.cached = cached
        self.__fp = fp
        self.__header = None
        self._rewind()
        self.__endpos = _eofpos(self.__fp)
        self.__posstack = []
        if cached:
            self._buildcache()

    def __delitem__(self, i):
        if type(i) is types.StringType:
            self.__delkey(i)
        elif type(i) is types.IntType:
            self.__delindex(i)

    def __delslice__(self, start, stop):
        for i in range(start, stop):
            self.__delindex(i)

    def __getitem__(self, i):
        if type(i) is types.StringType:
            return self.__getkey(i)
        elif type(i) is types.IntType:
            return self.__getindex(i)

    def __getslice__(self, start, stop):
        result = []
        self.__pushpos()
        for i in range(start, stop):
            result.append(self.__getindex(i))
        self.__poppos()
        return result

    def __len__(self):
        if self.cached:
            return len(self.__keynamescache)
        return len(self.keys())

    ##
    ## Public interface: Use it to access the tarfile.
    ##

    def append(self, entry):
        """
        Used to append data to the archive. You does not need to have a real
        file, to add the data. Here a small example:
           entry = TarEntry(data='Hello World! This is a dummy file')     or
           entry = TarEntry(name='Dummy.File', data='Hello World again!')
           tar.appendentry(entry)
        Now the archive contains a new entry. If you extract it, it would be
        written into the file 'Dummy.File' with rw- permission for owner.
        """
        if not isinstance(entry, TarEntry):
            raise TypeError, 'expect instance of TarEntry, got ' + `entry`
        try:
            self.__getindex(-1)
        except IndexError:
            self._rewind()
        seekp, nexti = self.__seekp, self.__nexti
        self._writeentry(entry)
        if self.cached:
            self._appendtocache(entry.name, seekp, nexti)

    def get(self, key, default):
        """
        Returns the last entry stored under 'key' or 'default', if 'key' does
        not exist in archive.
        """
        try:
            return self.__getkey(key)
        except KeyError:
            return default

    def has_key(self, key):
        """
        Returns 1, if 'key' exits in archive, 0 otherwise.
        """
        if self.cached:
            return self.__keycache.get(key, 0) != 0
        return key in self.keys()

    def items(self):
        """
        Return a list of tuples. Every tuple contains as first item the key
        (filename) and as the second one the TarEntry itself.
        """
        return self.iterate(lambda e: (e.name, e))

    def iterate(self, cmd):
        """
        Iterates over every entry of the archive, calls function cmd with the
        current entry as argument, and append the result of that function
        call to a list. After all items are processed, the resulting list is
        returned.
        """
        result = []
        self.__pushpos()
        for entry in self:
            result.append(cmd(entry))
        self.__poppos()
        return result

    def keys(self):
        """
        Returns a list with all keys (that is filenames) of the archive.
        """
        if self.cached:
            return self.__keynamescache
        return self.iterate(lambda e: e.name)

    def values(self):
        """
        Returns a list with all items of the archive packed into TarEntry
        instances.
        """
        return self.iterate(lambda e: e)

    ##
    ## Protected interface: Implements the base access scheme.
    ##

    def _appendtocache(self, name, seekp, nexti):
        """
        Append its argument on the end of the cache.
        """
        self.__keycache[name] = (seekp, nexti)
        self.__indexcache.append((seekp, nexti))
        self.__keynamescache.append(name)

    def _buildcache(self, start=0):
        """
        Builds the cache from position 'start' of the archive until its
        end.
        """
        if start == 0:
            self.__keycache = {}
            self.__indexcache = []
            self.__keynamescache = []
        self.__pushpos()
        self.__fp.seek(start, 0)
        self.__seekp = start
        while 1:
            seekp, nexti = self.__seekp, self.__nexti
            entry = self._next()
            if not entry:
                break
            self._appendtocache(entry.name, seekp, nexti)
        self.__poppos()

    def _eof(self):
        """
        End of archive reached?
        """
        return self.__seekp >= self.__endpos

    def _gotoindex(self, i):
        """
        Move the internal seekp to the beginning of the i'th item of the
        archive.
        """
        maxlen = len(self)
        if i < 0:
            i = maxlen + i
        if not (0 <= i < maxlen):
                raise IndexError, 'list index out of range'
        if self.cached:
            try:
                self.__seekp, self.__nexti = self.__indexcache[i]
            except IndexError:
                #self.__seekp, self.__nexti = 0, 0
                raise IndexError, 'list index out of range'
        else:
            self._rewind()
            seekp, nexti = self.__seekp, self.__nexti
            while not self._eof():
                self._next()
                if i == nexti:
                    break
                seekp, nexti = self.__seekp, self.__nexti
            else:
                raise IndexError, 'list index out of range'
            self.__seekp, self.__nexti = seekp, nexti

    def _gotokey(self, key):
        """
        Move the internal seekp to the beginning of the last item with the
        filename 'key' stored in the archive.
        """
        if self.cached:
            self.__seekp, self.__nexti = self.__keycache[key]
        else:
            self._rewind()
            seekp, nexti = self.__seekp, self.__nexti
            while not self._eof():
                item = self._next()
                if item and key == item.name:
                    break
                seekp, nexti = self.__seekp, self.__nexti
            else:
                raise KeyError, key
            self.__seekp, self.__nexti = seekp, nexti

    def _next(self):
        """
        Returns a 'TarEntry' instance filled with the item beginning right
        under the internal seekp. Advance the internal seekp to the next
        item of the archive.
        """
        if self._eof():
            return None
        self.__fp.seek(self.__seekp)
        self.__header = self.__fp.read(RECORDSIZE)
        if self.__header[0] == '\0':
            self.__seekp = self.__endpos
            return None
        self.__nexti = self.__nexti + 1
        self.entry = TarEntry(data=None)
        self.__extrHeader(self.entry)
        size = self.entry.size
        recordcount = (size / RECORDSIZE) + ((size % RECORDSIZE) != 0)
        startpos = self.__fp.tell()
        self.entry.data = _Subfile(self.__fp, startpos, startpos+size)
        self.__fp.seek(startpos + recordcount*RECORDSIZE)
        self.__seekp = self.__fp.tell()
        self.__checkheader()
        return self.entry

    _readentry = _next

    def _rewind(self):
        """
        Set the internal seekp to the beginning of the archive.
        """
        self.__fp.seek(0, 0)
        self.__seekp = 0
        self.__nexti = 0

    def _writeentry(self, entry):
        """
        Write the 'TarEntry' instance stored in 'entry' into the archive
        beginning at the position the internal seekp points to.
        """
        header = self.__buildheader(entry.name, entry.mode, entry.uid,
                                    entry.gid, entry.size, entry.mtime,
                                    entry.linkflag, entry.linkname, entry.uname,
                                    entry.gname)
        self.__appendheader(header)
        self.__appenddata(str(entry), entry.size)

    ##
    ## Private interface: Implements current map/list-like access scheme.
    ## Contains also helper methods.
    ##

    def __appenddata(self, stream, size=-1):
        """
        Appends the data stored in 'stream' just to the place where the
        internal seekp points to. If len(stream) % RECORDLEN != 0, write some
        chr(0) right after the stream until (len(stream)+len(fillerchars)) %
        RECORDLEN == 0. After the 'stream', RECORDLEN bytes will be written
        into archvie to indicate the end.
        """
        if size == -1:
            size = len(stream)
        recordcount = (size / RECORDSIZE) + ((size % RECORDSIZE) != 0)
        if size > 0:
            self.__fp.write(stream)
        fillersize = recordcount * RECORDSIZE - size
        self.__fp.write('\0' * (fillersize+RECORDSIZE))
        self.__nexti = self.__nexti + 1
        self.__seekp = self.__fp.tell()
        self.__endpos = self.__seekp

    def __appendheader(self, header):
        """
        Write the header to the archive, beginning with pos indicated by
        the internal seekp.
        """
        self.__fp.write(header)

    def __buildheader(self, fname, mode, uid, gid, size, mtime,
                     linkflag='0', linkname='', uname='', gname=''):
        """
        Builds a tar header, which contains the information taken from the
        arguments.
        """
        header = fname + '\0' * (NAMSIZ - len(fname))
        header = header + _int2octstr(mode, 8)
        header = header + _int2octstr(uid, 8)
        header = header + _int2octstr(gid, 8)
        header = header + _int2octstr(size, 12)
        header = header + _int2octstr(mtime, 12)
        header = header + '%s'
        header = header + linkflag
        header = header + linkname + '\0' * (NAMSIZ - len(linkname))
        header = header + TMAGIC
        header = header + uname + '\0' * (TUNMLEN - len(uname))
        header = header + gname + '\0' * (TGNMLEN - len(gname))
        header = header + '\0' * (RECORDSIZE - len(header) - 6)
        sum = _chksum(header % (CHKBLANKS,))
        return header % (_int2octstr(sum, 8),)

    def __checkheader(self):
        """
        Checks whether the last read header is valid or not. Every header
        stores a chksum, to which the header should be checked against.
        """
        header = self.__header
        hsum = _getnbr(header, NAMSIZ + 3*8 + 2*12, 8)
        sum = _chksum(header[:NAMSIZ + 3*8 + 2*12])
        sum = sum + _chksum(CHKBLANKS)
        sum = sum + _chksum(header[NAMSIZ + 3*8 + 2*12 + 8:])
        if hsum != sum:
            raise Error, ('corrupt header', hsum, sum)

    def __delindex(self, i):
        """
        Delete the i'th entry from the archive.
        """
        self._gotoindex(i)
        self.__moverestback()

    def __delkey(self, key):
        """
        Delete all items of the archive, whose filename == 'key'. Will be
        changed in future, so that only the last item will be deleted.
        """
        self._gotokey(key)
        self.__moverestback()
        while 1:
            try:
                self._gotokey(key)
            except KeyError:
                break
            else:
                self.__moverestback()

    def __extrHeader(self, entry):
        """
        Read RECORDLEN bytes from the archive beginning with the pos, the
        internal seekp currently points to. After that, decode the record
        as if it is a tar header. Write all informations into the
        'TarEntry' instance stored in 'entry'.
        """
        pos = 0
        entry.name = _getstr(self.__header, pos); pos = pos + NAMSIZ
        entry.mode = _getnbr(self.__header, pos, 8); pos = pos + 8
        entry.uid  = _getnbr(self.__header, pos, 8); pos = pos + 8
        entry.gid  = _getnbr(self.__header, pos, 8); pos = pos + 8
        entry.size = _getnbr(self.__header, pos, 12); pos = pos + 12
        entry.mtime = _getnbr(self.__header, pos, 12); pos = pos + 12
        pos = pos + 8  # Skip the checksum
        entry.linkflag = _getstr(self.__header, pos); pos = pos + 1
        entry.linkname = _getstr(self.__header, pos); pos = pos + NAMSIZ
        entry.magic = _getstr(self.__header, pos); pos = pos + 8
        entry.uname = _getstr(self.__header, pos); pos = pos + TUNMLEN
        entry.gname = _getstr(self.__header, pos); pos = pos + TGNMLEN
        entry.devmajor = _getnbr(self.__header, pos, 8); pos = pos + 8
        entry.devminor = _getnbr(self.__header, pos, 8); pos = pos + 8
        if entry.magic[:3] == 'GNU':
            entry.atime = _getnbr(self.__header, pos, 12); pos = pos + 12
            entry.ctime = _getnbr(self.__header, pos, 12); pos = pos + 12
            entry.offset = _getnbr(self.__header, pos, 12); pos = pos + 12
            entry.longname = _getstr(self.__header, pos); pos = pos + 4

    def __getindex(self, i):
        """
        Returns the i'th item of the archive as instance of TarEntry.
        """
        if i != self.__nexti:
            self._gotoindex(i)
        entry = self._next()
        if not entry:
            raise IndexError, 'list index out of range'
        return entry

    def __getkey(self, key):
        """
        Returns the last item whose fielname is 'key' stored in a
        'TarEntry' instance.
        """
        self.__pushpos()
        try:
            self._gotokey(key)
            entry = self._next()
        finally:
            self.__poppos()
        return entry

    def __moverestback(self):
        """
        Move all items stored after the current one to the pos of the
        current one. So in fact the current one will be deleted.
        """
        seekp, nexti = self.__seekp, self.__nexti
        entry = self._next()
        rest = self.__fp.read()
        self.__fp.seek(seekp, 0)
        self.__fp.write(rest)
        if self.cached:
            index = self.__keynamescache.index(entry.name)
            seekp, nexti = self.__indexcache[index]
            del self.__keycache[entry.name]
            del self.__indexcache[index:]
            del self.__keynamescache[index:]
            self._buildcache(seekp)
        self._rewind()

    def __pushpos(self):
        """
        Push the interna seekp and the nextindex pointer onto a internal
        stack.
        """
        self.__posstack.insert(0, (self.__seekp, self.__nexti))

    def __poppos(self):
        """
        Posp the last pushed internal seekp and nexti pointer back to the
        internal object.
        """
        self.__seekp, self.__nexti = self.__posstack[0]
        del self.__posstack[0]
        self.__fp.seek(self.__seekp)



class _Subfile(object):
    """
    This calss is taken in whole from the 'mailbox' library included in the
    standard distribution of Python 1.5.
    """
    def __init__(self, fp, start, stop):
        self.__fp = fp
        self.start = start
        self.stop = stop
        self.pos = self.start

    def read(self, length = None):
        if self.pos >= self.stop:
            return ''
        if length is None:
            length = self.stop - self.pos
        self.__fp.seek(self.pos)
        self.pos = self.pos + length
        return self.__fp.read(length)

    def readline(self, length = None):
        if self.pos >= self.stop:
            return ''
        if length is None:
            length = self.stop - self.pos
        self.__fp.seek(self.pos)
        data = self.__fp.readline(length)
        if len(data) < length:
            length = len(data)
        self.pos = self.pos + length
        return data

    def tell(self):
        return self.pos - self.start

    def seek(self, pos, whence=0):
        if whence == 0:
            self.pos = self.start + pos
        elif whence == 1:
            self.pos = self.pos + pos
        elif whence == 2:
            self.pos = self.stop + pos

    def close(self):
        pass



##
## Helper functions
##

def _chksum(str):
    sum = 0
    for b in str:
        sum = sum + ord(b)
    return sum

def _eofpos(fp):
    oldseekp = fp.tell()
    fp.seek(0, 2)
    pos = fp.tell()
    fp.seek(oldseekp, 0)
    return pos

def _getstr(stream, start=0, length=0):
    if length == 0:
        endpos = string.find(stream, '\0', start)
    else:
        endpos = start + length
    if endpos > -1:
        return stream[start:endpos]
    return stream

def _getnbr(stream, start, length):
    for b in stream[start:start+length]:
        if b != '\0':
            break
        start = start + 1
        length = length - 1
    str = _getstr(stream[start:start+length])
    if str:
        return string.atoi(string.strip(str), 8)
    return None

def _int2octstr(int, length=0):
    return '%0*o\0' % (length-1, int)

def _octstr2int(octstr):
    return string.atoi(string.strip(octstr), 8)



##
## Test prog realizes a very small and simple tar command
##

if __name__ == '__main__':
    import fnmatch, getopt, re, sys, time

    usagetxt = """
Purpose:
        This tool realize a very incomplete tar command. It should not
    replace the real UNIX tar (for that, it is too slow and to incomplete),
    but serves as demo of the tarlib.py library. But it has also some
    features you cannot find in many standard tar command. This would be:
        - Deletion of items from archive,
        - Extraction of files via wildcarts, ...

        You can only use .tar files. No .tar.Z, .tar.gz, tapes or other.

Syntax:
    %s -{cdfhrtvx} <files...>

Whereby:
        -c  Creates a new archive. If the archive already exists, it will
            be truncated first.
        -d  Delete files from archive.
        -f <archive>  Use tarfile <file> as archive.
        -h  Shows that help text.
        -r  Appends files on the end of the archive.
        -t  Shows the contents of the archive.
        -v  Verbose. Enhance or enable the processing display for the
            commands -{cdrtx}
        -x  Extract files from archive.

""" % (os.path.basename(sys.argv[0]),)

    ##
    ## Helper funcs for test program
    ##

    def __mode2str(mode):
        """
        Converts a bitpattern to a UNIX like permission string.
        """
        str = ''
        for i in range(2, -1, -1):
            for j in range(2, -1, -1):
                k = i*3 + j
                if j == 0 and (mode & 2**(9+i)) != 0:
                    str = str + 's'
                elif (mode & (2**k)) != 0:
                    str = str + ['x', 'w', 'r'][k%3]
                else:
                    str = str + '-'
            #str = str + '/'
        return str[:-1]

    def __add(tar, fname, verbose=0):
        """
        Add one file to the end of the archive. If 'fname' is a directory,
        all files and subdirectires will also be added.
        """
        path = ''
        if fname == '*':
            __error('No file to add!')
        dir = os.path.isdir(fname)
        if dir and fname[-1] != os.sep:
            fname = fname + os.sep
        try:
            fp = open(fname, 'r')
        except IOError, detail:
            __error('Cannot open file', `fname`, `detail[1]`)
        try:
            tar.append(TarEntry(data=fp))
            if verbose:
                print 'a', fname
        finally:
            fp.close()
        if dir:
            path = os.path.join(path, fname)
            for file in os.listdir(path):
                __add(tar, os.path.join(path, file), verbose)

    def __createpath(path):
        """
        Look whether every directory of a given path exists, create it otherwise,
        and chdir to it.
        """
        if path:                          # If there is a path before the file...
            for dir in string.split(path, os.sep):
                if dir == '':                             # path was absolut
                    os.chdir(os.sep)
                else:
                    if not os.path.exists(dir):
                        os.mkdir(dir)
                    os.chdir(dir)

    def __delete(tar, fname, verbose=0):
        """
        Delete file 'fname' from the archive. If the file occurs more than
        one time in the archive, all occurrences will be deleted.
        """
        if fname == '*':
            __error('Deletion of ALL files not allowed!')
        fnames = filter(lambda f,p=fname: fnmatch.fnmatch(f, p), tar.keys())
        for fname in fnames:
            try:
                del tar[fname]
            except KeyError:
                __error('No such file', `fname`, 'in archive!')
            if verbose:
                print 'd', fname

    def __error(*args):
        """
        Concat all args and write them to STDERR. At least the interpreter
        will be exited.
        """
        for arg in args:
            sys.stderr.write(arg+' ')
        sys.stderr.write('\n')
        sys.exit(1)

    def __extract(tar, fname, verbose=0):
        """
        Extracts one file from the archive to the filesystem. All files will
        be handled as regular files except symlinks and directories. The 'fname'
        may contain wildcards. All matching files are then extracted.
        Directory pathes will silently be created.
        """
        cwd = os.getcwd()
        fnames = filter(lambda f,p=fname: fnmatch.fnmatch(f, p), tar.keys())
        for fname in fnames:
            try:
                entry = tar[fname]
            except KeyError:
                __error('No such file', `fname`, 'in archive!')
            path, name = os.path.split(entry.name)
            if stat.S_ISDIR(entry.mode):
                continue                 # Ignore directories
            elif stat.S_ISLNK(entry.mode):
                try:                     # Try to create symlink
                    os.symlink(entry.linkname, fname)
                except os.error, detail:
                    print 'x', fname, ': Could not create symlink to',
                    print entry.linkname + ':', detail[1]
                    continue
            else:                        # The rest is stated as regular files.
                try:
                    __createpath(path)
                    try:
                        fp = open(name, 'w')
                    except IOError, detail:
                        __error('Cannot open file', `fname`, detail[1])
                    try:
                        fp.write(entry.data.read())
                        os.chmod(name, entry.mode)
                    finally:
                        fp.close()
                finally:
                    os.chdir(cwd)
            if verbose:
                print 'x', fname

    def __list(tar, fname, verbose=0):
        """
        List information of 'fname' stored in archive. If 'fname' is '*', all
        files of the archive are shown. If 'verbose' flag was set, for every
        file, information are also be displayed in a long form like 'ls -l'.
        If fname is a directory, all entries stored in archive and belongs to
        that directory are also displayed.
        """
        line = '%s%s %5s/%-5s%9s %s %s'
        fnames = filter(lambda f,p=fname: fnmatch.fnmatch(f, p), tar.keys())
        for fname in fnames:
            try:
                e = tar[fname]
            except KeyError:
                __error('No such file', `fname`)
            if verbose:
                if stat.S_ISDIR(e.mode):
                    dir = 'd'
                elif stat.S_ISLNK(e.mode):
                    dir = 'l'
                else:
                    dir = '-'
                date = time.strftime('%b %d %H:%M %Y',time.localtime(e.mtime))
                print line % (dir, __mode2str(e.mode), e.uid, e.gid, e.size, date,
                              e.name),
                if dir == 'l':
                    print '->', e.linkname,
                print
            else:
                print e.name

    def __usage():
        """
        Shows the usage of that demo.
        """
        sys.stderr.write('\n'+version+'\n')
        sys.stderr.write(usagetxt)
        sys.exit(1)

    command = None
    mode = 'r+'
    fp = None
    tar = None
    verbose = 0
    cmdtable = {'-c':__add, '-d':__delete, '-r':__add,
                '-t':__list, '-x':__extract}
    if len(sys.argv) == 1:
        __usage()
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cdf:hrtvx')
        for opt, val in opts:
            if opt in ['-c', '-d', '-r', '-t', '-x']:
                if command:
                    __error('Only one of -{cdrtx} allowed')
                command = cmdtable[opt]
                if opt == '-c':
                    mode = 'w+'
            elif opt == '-f':
                if fp:
                    fp.close()
                try:
                    fp = open(val, mode)
                except IOError, detail:
                    __error('Cannot open', `val`+':', detail[1])
                tar = TAR(fp, cached=1)
            elif opt == '-v':
                verbose = 1
            elif opt == '-h':
                __usage()
        if tar is None:
            __error('No tar archive assigned!')
        if not command:
            __error('No command given! One of -{cdrtx} has to be given')
        if not args:
            args = '*'
        for file in args:
            command(tar, file, verbose)
    finally:
        if fp:
            fp.close()
