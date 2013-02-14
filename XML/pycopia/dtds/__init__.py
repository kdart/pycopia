#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
The dtds package is where compiled DTDs go.

A DTD is "compiled" to Python syntax to make usage faster.

"""

__all__ = [ "contentxml", "google", "logml", "pomtest", "rss091", "rss2", "si", "sl",
  "WCSinvalidation", "wml11", "wml12", "wml13", "wml20", "wta_wml12", "wurfl",
  "xfdesktop_menu", "xhtml11", "xhtml1_frameset", "xhtml1_strict", "xhtml1_transitional",
  "xhtml_basic10", "xhtml_basic11", "xhtml_mobile10", "XMLSchema",
  ]

import os
from pycopia.aid import newclass, Import
from pycopia.XML import ValidationError

# TODO get from some config.
USERDTDPATH = os.environ.get("USERDTDPATH", os.path.join(b"/", b"var", b"tmp", b"dtds"))

# Add user generated dtds to path to pick up user generated dtd files.
__path__.append(USERDTDPATH)


# Constants to be used as shortcut identifiers. Value os module name for
# the docutment types compiled DTD.
# Use one of these as a shortcut name to a document type.
CONTENTXML = b"pycopia.dtds.contentxml"
GOOGLE = b"pycopia.dtds.google"
LOGML = b"pycopia.dtds.logml"
POMTEST = b"pycopia.dtds.pomtest"
WURFL = b"pycopia.dtds.wurfl"
XFDESKTOP_MENU = b"pycopia.dtds.xfdesktop_menu"
RSS091 = b"pycopia.dtds.rss091"
RSS2 = b"pycopia.dtds.rss2"
SI = b"pycopia.dtds.si"
SL = b"pycopia.dtds.sl"
WCSINVALIDATION = b"pycopia.dtds.WCSinvalidation"
WML11 = b"pycopia.dtds.wml11"
WML12 = b"pycopia.dtds.wml12"
WML13 = b"pycopia.dtds.wml13"
WML20 = b"pycopia.dtds.wml20"
WTA_WML12 = b"pycopia.dtds.wta_wml12"
XHTML11 = b"pycopia.dtds.xhtml11"
XHTML1_FRAMESET = b"pycopia.dtds.xhtml1_frameset"
XHTML1_STRICT = b"pycopia.dtds.xhtml1_strict"
XHTML1_TRANSITIONAL = b"pycopia.dtds.xhtml1_transitional"
XHTML_BASIC10 = b"pycopia.dtds.xhtml_basic10"
XHTML_BASIC11 = b"pycopia.dtds.xhtml_basic11"
XHTML_MOBILE10 = b"pycopia.dtds.xhtml_mobile10"
XMLSCHEMA = b"pycopia.dtds.XMLSchema"
SVG = b"pycopia.dtds.svg11_flat_20030114"

# alias for default DTD.
WML = WML13
XHTML = XHTML11
XHTML_BASIC = XHTML_BASIC11
RSS = RSS2

class Doctype(object):
  def __init__(self, name, pubid, sysid):
    self.name = name.encode("ascii")
    self.public = None
    if pubid:
        self.public = pubid.encode("ascii")
    self.system = sysid.encode("ascii")

  def __str__(self):
    if self.public:
      return b'<!DOCTYPE %s PUBLIC "%s"\n    "%s">\n' % (self.name, self.public, self.system)
    else:
      return b'<!DOCTYPE %s SYSTEM "%s">\n' % (self.name, self.system)


# It seems DOCTYPE can't always be obtained from the DTD, so there is a
# mapping here that must be maintained. This should be done before
# compiling with dtd2py.
DOCTYPES = {}
DOCTYPES[POMTEST] = Doctype("toplevel", None, "pomtest.dtd")
DOCTYPES[XHTML1_STRICT] = Doctype("html", "-//W3C//DTD XHTML 1.0 Strict//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd")
DOCTYPES[XHTML1_TRANSITIONAL] = Doctype("html", "-//W3C//DTD XHTML 1.0 Transitional//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd")
DOCTYPES[XHTML1_FRAMESET] = Doctype("html", "-//W3C//DTD XHTML 1.0 Frameset//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd")
DOCTYPES[XHTML11] = Doctype("html", "-//W3C//DTD XHTML 1.1//EN",
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd")
# mobile variants
DOCTYPES[XHTML_MOBILE10] = Doctype("html", "-//WAPFORUM//DTD XHTML Mobile 1.0//EN",
             "http://www.wapforum.org/DTD/xhtml-mobile10.dtd")
DOCTYPES[XHTML_BASIC10] = Doctype("html", "-//W3C//DTD XHTML Basic 1.0//EN",
             "http://www.w3.org/TR/xhtml-basic/xhtml-basic10.dtd")
DOCTYPES[XHTML_BASIC11] = Doctype("html", "-//W3C//DTD XHTML Basic 1.1//EN",
             "http://www.w3.org/TR/xhtml-basic/xhtml-basic10.dtd")
# wml
DOCTYPES[WML11] = Doctype("wml", "-//WAPFORUM//DTD WML 1.1//EN",
          "http://www.wapforum.org/DTD/wml_1.1.xml")
DOCTYPES[WML12] = Doctype("wml", "-//WAPFORUM//DTD WML 1.2//EN",
             "http://www.wapforum.org/DTD/wml12.dtd")
DOCTYPES[WML13] = Doctype("wml", "-//WAPFORUM//DTD WML 1.3//EN",
             "http://www.wapforum.org/DTD/wml13.dtd")
DOCTYPES[WML20] = Doctype("html", "-//WAPFORUM//DTD WML 2.0//EN",
             "http://www.wapforum.org/dtd/wml20.dtd")
DOCTYPES[WTA_WML12] = Doctype("wta-wml", "-//WAPFORUM//DTD WTA-WML 1.2//EN",
             "http://www.wapforum.org/DTD/wta-wml12.dtd")
DOCTYPES[SI] = Doctype("si", "-//WAPFORUM//DTD SI 1.0//EN",
             "http://www.wapforum.org/DTD/si.dtd")
DOCTYPES[SL] = Doctype("sl", "-//WAPFORUM//DTD SL 1.0//EN",
             "http://www.wapforum.org/DTD/sl.dtd")
# Others
DOCTYPES[GOOGLE] = Doctype("GSP", None, "google.dtd")
DOCTYPES[RSS2] = Doctype("rss", None, "rss2.dtd")
DOCTYPES[RSS091] = Doctype("rss", None, "rss091.dtd")
DOCTYPES[WURFL] = Doctype("wurfl", None, "wurfl.dtd")
DOCTYPES[XMLSCHEMA] = Doctype("xs:schema", "-//W3C//DTD XMLSCHEMA 200102//EN",
             "http://www.w3.org/2001/XMLSchema.dtd")
DOCTYPES[SVG] = Doctype("svg", "-//W3C//DTD SVG 1.1//EN",
             "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd")

def get_doctype(keyname):
    return DOCTYPES.get(keyname)

def get_dtd_module(doctype_constant):
    try:
        mod = Import(doctype_constant)
    except ImportError as err:
        raise ValidationError("No compiled DTD found for %r."
                                   " Please run dtd2py. : %s" % (doctype_constant, err))
    return mod

def get_class(dtdmod, name, bases):
    try:
        cls = dtdmod._CLASSCACHE[name]
    except KeyError:
        cls = newclass(name, *bases)
        dtdmod._CLASSCACHE[name] = cls
    return cls

def get_mod_file(directory, sourcefilename):
    """get_mod_file(sourcefilename)
    Converts a file name into a file name importable by Python.
    """
    from pycopia.textutils import maketrans
    modname = os.path.splitext(os.path.split(sourcefilename.encode("ascii"))[1])[0]
    modname = modname.translate(maketrans(b"-. ", b"___"))
    return (os.path.join(directory.encode("ascii"), modname + b".py"),
                DOCTYPES.get("%s.%s" % (__name__, modname)))

