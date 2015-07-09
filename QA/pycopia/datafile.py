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
Manage data file names. Data files are files with data that encode
additional data (metadata) about the dataset in the file name.

decode_filename(pathname) : given a path name, return a dictionary-like object
containing the metdata. The basic name has the key "name". The data will
have a timestamp value, taken from the second field in the name, or the
file's mtime. The metadata may also have the "directory" value.

get_filename(metadata, [directory]) : return a file name encoding the given
metadata values.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
import os
import re

from pycopia import aid
from pycopia import dictlib
from pycopia import timelib



OFF = aid.Enum(0, "OFF")
ON = aid.Enum(1, "ON")
UNKNOWN = aid.Enum(-1, "UNKNOWN")


_STATE_RE = re.compile(r"(\w+)(ON|OFF|UNKNOWN)")
_STATEMAP = {
    "ON": ON,
    "OFF": OFF,
    "UNKNOWN": UNKNOWN,
}

_OTHERDATA_RE = re.compile(r"([a-z]+)([A-Z0-9.,\-]+)")



def get_filename(metadata, directory=None, ext="txt"):
    """Construct data file name from a metadata dictionary.

    Returns the file name, as a string.
    """
    metadata = metadata.copy()
    name = metadata.pop("name", "data")
    directory = metadata.pop("directory", directory)
    try:
        timestamp = metadata.pop("timestamp")
    except KeyError:
        tstring = ""
    else:
        tstring = timestamp.strftime("+%Y%m%d%H%M%S")

    mmd = []
    for key in sorted(metadata.keys()):
        value = metadata[key]
        if type(value) is str:
            value = value.upper()
        mmd.append("%s%s" % (key.lower(), value))

    fname = "%s%s+%s.%s" % ( name, tstring, "+".join(mmd), ext)
    if directory:
        return os.path.join(directory, fname)
    else:
        return fname


def decode_filename(pathname):
    """Decode a metadata encoded file name.

    Returns a DatFileData object populated with metadata.
    """
    data = DataFileData()
    pathname = os.path.abspath(pathname)
    dirname, fname = os.path.split(pathname)
    fname, ext = os.path.splitext(fname)
    nameparts = fname.split("+")
    data.directory = dirname
    data.name = nameparts[0]
    offset = 1
    try:
        mt = timelib.strptime_mutable(nameparts[offset], "%Y%m%d%H%M%S")
    except:
        mt = timelib.localtime_mutable(os.path.getmtime(pathname))
    else:
        offset += 1
    mt.set_format("%a, %d %b %Y %H:%M:%S %Z")
    data.timestamp = mt
    for part in nameparts[offset:]:
        mo = _STATE_RE.match(part)
        if mo:
            data[mo.group(1)] = _STATEMAP[mo.group(2)]
        else:
            mo = _OTHERDATA_RE.match(part)
            if mo:
                valuestring = mo.group(2)
                try:
                    value = eval(valuestring, {}, {})
                    if type(value) is str:
                        value = value.lower()
                except:
                    value = valuestring
                data[mo.group(1)] = value
            else:
                print("name component not matched: %r" % (part,), file=sys.stderr)
    return data


class DataFileData(dictlib.AttrDict):
    def __str__(self):
        s = ["Data metadata:"]
        for name in ("name", "directory", "timestamp"):
            s.append("%14.14s: %s" % (name, self.get(name)))
        for name, value in self._get_states():
                s.append("%14.14s: %s" % (name, value))
        return "\n    ".join(s)

    def __eq__(self, other):
        return self.compare(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_timestamp(self, time=None):
        if time is None:
            time = timelib.now()
        self["timestamp"] = timelib.localtime_mutable(time)

    def compare(self, other, missingok=True):
        namelist = self.keys()
        return self.compare_metadata(other, namelist, missingok)

    def compare_metadata(self, other, namelist, missingok=True):
        for name in namelist:
            try:
                if other[name] != self[name]:
                    return False
            except KeyError:
                if not missingok:
                    return False
        return True

    def get_filename(self, directory=None):
        return get_filename(self, directory)

    def _get_states(self):
        for name, value in self.items():
            if name in ("name", "timestamp", "directory"):
                continue
            yield name, value


def _test(argv):
    from pycopia import autodebug
    metadata = DataFileData()
    metadata.name = "test_datafile"
    metadata.set_timestamp()
    metadata["state"] = ON
    metadata["voltage"] = 2.5
    fname = metadata.get_filename("/tmp")
    print ("filename: ", fname)
    fo = open(fname, "w")
    fo.write("some data.\n")
    fo.close()

    newmeta = decode_filename(fname)
    print (newmeta)
    print (newmeta["voltage"])
    with open(fname) as fo:
        fo.read()
    assert metadata.voltage == newmeta.voltage
    assert newmeta.state == ON
    return metadata, newmeta


if __name__ == "__main__":
    metadata, newmeta = _test(sys.argv)

