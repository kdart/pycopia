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
Detailed platform detection functions.  Differentiate Linux distributions
and MS Windows frameworks.

"""

from __future__ import print_function

import sys
import re

LINUX_RELEASE_FILES = [
    "/etc/vmware-release",
    "/etc/redhat-release",
    "/etc/gentoo-release",
    "/etc/lsb-release", # Ubuntu, possibly others
]

LINUX_RELEASE_RE = re.compile(r"(.*) release (.*)")

class OSInfo(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __str__(self):
        s = ["Platform info:"]
        for name in ("platform", "arch", "osname", "osversion",
                "distribution", "release"):
            s.append("%15.15s: %s" % (name, getattr(self, name, "Unknown")))
        return "\n".join(s)

    def is_linux(self):
        return self.platform.startswith("linux")

    def is_windows(self):
        return self.platform == "win32"

    def is_cli(self):
        return self.platform == "cli"

    def is_gentoo(self):
        return self.distribution.startswith("Gentoo")

    def is_vmware(self):
        return self.distribution.startswith("VMware")

    def is_rhel(self):
        return self.distribution.startswith("Red")

    def is_centos(self):
        return self.distribution.startswith("Cent")

    def is_ubuntu(self):
        return self.distribution.startswith("Ubu")

    def is_redhat(self): # rpm-based
        dist = self.distribution
        return dist.startswith("Red") or dist.startswith("Cent")


def _get_linux_dist():
    for fname in LINUX_RELEASE_FILES:
        if os.path.exists(fname):
            text = open(fname).read()
            mo = LINUX_RELEASE_RE.search(text)
            if mo:
                return map(str.strip, mo.groups())
            else:
                pass
    return "Unknown", "Unknown"

def get_platform():
    global os 
    rv = OSInfo()
    rv.platform = sys.platform
    if sys.platform.startswith("linux"):
        import os # making this global breaks on IronPython
        osname, _, kernel, _, arch = os.uname()
        rv.arch = arch
        rv.osname = osname
        rv.osversion = kernel
        rv.distribution, rv.release = _get_linux_dist()
    elif sys.platform in ("win32", "cli"):
        import os
        rv.arch = os.environ["PROCESSOR_ARCHITECTURE"]
        rv.osname = os.environ["OS"]
        rv.distribution = "Microsoft"
        if sys.platform == "win32":
            import win32api
            major, minor, build, api, extra = win32api.GetVersionEx()
            rv.osversion = "%d.%d.%d-%s" % (major, minor, build, extra)
            rv.release = "Unknown"
        elif sys.platform == "cli":
            rv.osversion = "Unknown"
            rv.release = "Unknown"
    return rv


if __name__ == "__main__":
    print (get_platform())

