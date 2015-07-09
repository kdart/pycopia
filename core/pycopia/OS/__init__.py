
"""
Platform dependent modules, and modules using "duck-typing" to hide
platform details.

"""

import sys
import os

# Patch os module with extra constants.
os.ACCMODE = 0o3

# Additional module path for polymorphic platform modules.
platdir = {
    "linux1":"Linux",
    "linux2":"Linux",
    "linux3":"Linux",
    "linux":"Linux",
    "cygwin":"CYGWIN_NT",
    "sunos5":"SunOS",
    "freebsd4":"FreeBSD",
    "freebsd5":"FreeBSD",
    "darwin":"Darwin",
    "win32":"Win32"}[sys.platform]

__path__.append(os.path.join(__path__[0], platdir))


