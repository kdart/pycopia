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
Use wxcut and wxpaste to get and set the X selection.

"""

from pycopia import proctools

WXCOPY = proctools.which("wxcopy")
WXPASTE = proctools.which("wxpaste")

WXCOPY_OPTIONS = '-clearselection'
WXPASTE_OPTIONS = ''


def wxcopy(text, callback=None, logfile=None, extraoptions="", async=False):
    pm = proctools.get_procmanager()
    command = "%s %s %s" % (WXCOPY, WXCOPY_OPTIONS, extraoptions)
    copy = pm.spawnpipe(command, logfile=logfile, async=async)
    copy.write(text)
    copy.close()
    return copy.wait()

def wxpaste(callback=None, logfile=None, extraoptions="", async=False):
    """wxpaste - output a cutbuffer to stdout, returned as a string."""
    pm = proctools.get_procmanager()
    command = "%s %s %s" % (WXPASTE, WXPASTE_OPTIONS, extraoptions)
    paste = pm.spawnpipe(command, logfile=logfile, async=async)
    rv = paste.read()
    paste.close()
    es = paste.wait()
    if es:
        return rv
    else:
        raise proctools.ProcessError(es)

