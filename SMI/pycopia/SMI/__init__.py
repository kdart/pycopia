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
An SMI parser and collection of tools. This package wraps the SWIG generated
code that in turn wraps the libsmi library. The libsmi library is a C library
that parses SMI files.

libsmi home page:

http://www.ibr.cs.tu-bs.de/projects/libsmi/

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys


# "global" OIDMAP contains reverse OID for all imported MIBS.
OIDMAP = {}

def update_oidmap(basemodname):
    modname = "%s_OID" % basemodname
    __import__(modname)
    oidmod = sys.modules[modname]
    OIDMAP.update(oidmod.OIDMAP)
    # clean up extra references
    delattr(oidmod, "OIDMAP")
    del sys.modules[modname]

