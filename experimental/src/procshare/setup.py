# Procshare is forked from the Python "posh" project. I needed to modify
# it to work with pyNMS proctools process manager module.

from distutils.core import setup, Extension
import sys
from glob import glob

sources = glob("src/*.c")
undefine = []
define = []

try:
    sys.argv.remove("--debug")
    undefine.append("NDEBUG")
    define.append(("DEBUG", 1))
except ValueError:
    pass

_core = Extension("_procshare_core",
                  sources,
                  define_macros=define,
                  undef_macros=undefine)

setup(name="procshare",
      version="1.2",
      description="POSH -- Python Object Sharing",
      long_description="POSH -- Python Object Sharing",
      author="Steffen Viken Valvaag",
      author_email="steffenv@stud.cs.uit.no",
      maintainer="Keith Dart",
      maintainer_email="keith@dartworks.biz",
      license="GNU General Public License (GPL)",
      ext_modules=[_core])
