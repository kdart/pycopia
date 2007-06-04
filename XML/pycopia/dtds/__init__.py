#!/usr/bin/python

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

# TODO get from some config.
USERDTDPATH = os.environ.get("USERDTDPATH", os.path.join("/", "var", "tmp", "dtds"))

# Add user generated dtds to path to pick up user generated dtd files.
__path__.append(USERDTDPATH)


# Constants to be used as shortcut identifiers. Value os module name for
# the docutment types compiled DTD.
CONTENTXML = "pycopia.dtds.contentxml"
GOOGLE = "pycopia.dtds.google"
LOGML = "pycopia.dtds.logml"
POMTEST = "pycopia.dtds.pomtest"
RSS091 = "pycopia.dtds.rss091"
RSS2 = "pycopia.dtds.rss2"
SI = "pycopia.dtds.si"
SL = "pycopia.dtds.sl"
WCSINVALIDATION = "pycopia.dtds.WCSinvalidation"
WML11 = "pycopia.dtds.wml11"
WML12 = "pycopia.dtds.wml12"
WML13 = "pycopia.dtds.wml13"
WML20 = "pycopia.dtds.wml20"
WTA_WML12 = "pycopia.dtds.wta_wml12"
WURFL = "pycopia.dtds.wurfl"
XFDESKTOP_MENU = "pycopia.dtds.xfdesktop_menu"
XHTML11 = "pycopia.dtds.xhtml11"
XHTML1_FRAMESET = "pycopia.dtds.xhtml1_frameset"
XHTML1_STRICT = "pycopia.dtds.xhtml1_strict"
XHTML1_TRANSITIONAL = "pycopia.dtds.xhtml1_transitional"
XHTML_BASIC10 = "pycopia.dtds.xhtml_basic10"
XHTML_BASIC11 = "pycopia.dtds.xhtml_basic11"
XHTML_MOBILE10 = "pycopia.dtds.xhtml_mobile10"
XMLSCHEMA = "pycopia.dtds.XMLSchema"

# alias for default DTD.
WML = WML13
XHTML = XHTML11
XHTML_BASIC = XHTML_BASIC11
RSS = RSS2

class Doctype(object):
  def __init__(self, name, pubid, sysid):
    self.name = name
    self.public = pubid
    self.system = sysid

  def __str__(self):
    if self.public:
      return '<!DOCTYPE %s PUBLIC "%s"\n    "%s">\n' % (self.name, self.public, self.system)
    else:
      return '<!DOCTYPE %s SYSTEM "%s">\n' % (self.name, self.system)


# It seems DOCTYPE can't always be obtained from the DTD, so there is a
# mapping here that must be maintained. This should be done before
# compiling with dtd2py.
DOCTYPES = {}
DOCTYPES[XHTML1_STRICT] = Doctype("HTML", "-//W3C//DTD XHTML 1.0 Strict//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd")
DOCTYPES[XHTML1_TRANSITIONAL] = Doctype("HTML", "-//W3C//DTD XHTML 1.0 Transitional//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd")
DOCTYPES[XHTML1_FRAMESET] = Doctype("HTML", "-//W3C//DTD XHTML 1.0 Frameset//EN",
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd")
DOCTYPES[XHTML11] = Doctype("html", "-//W3C//DTD XHTML 1.1//EN",
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd")
# mobile variants
DOCTYPES[WML11] = Doctype("wml", "-//WAPFORUM//DTD WML 1.1//EN",
          "http://www.wapforum.org/DTD/wml_1.1.xml")
DOCTYPES[WML12] = Doctype("wml", "-//WAPFORUM//DTD WML 1.2//EN",
    "http://www.wapforum.org/DTD/wml12.dtd")
DOCTYPES[WML13] = Doctype("wml", "-//WAPFORUM//DTD WML 1.3//EN",
    "http://www.wapforum.org/DTD/wml13.dtd")
DOCTYPES[WML20] = Doctype("html", "-//WAPFORUM//DTD WML 2.0//EN",
    "http://www.wapforum.org/dtd/wml20.dtd")
DOCTYPES[XHTML_MOBILE10] = Doctype("html", "-//WAPFORUM//DTD XHTML Mobile 1.0//EN",
    "http://www.wapforum.org/DTD/xhtml-mobile10.dtd")
DOCTYPES[XHTML_BASIC10] = Doctype("html", "-//W3C//DTD XHTML Basic 1.0//EN",
             "http://www.w3.org/TR/xhtml-basic/xhtml-basic10.dtd")
DOCTYPES[XHTML_BASIC11] = Doctype("html", "-//W3C//DTD XHTML Basic 1.1//EN",
             "http://www.w3.org/TR/xhtml-basic/xhtml-basic10.dtd")
DOCTYPES[WTA_WML12] = Doctype("wta-wml", "-//WAPFORUM//DTD WTA-WML 1.2//EN",
    "http://www.wapforum.org/DTD/wta-wml12.dtd")

DOCTYPES[SI] = Doctype("si", "-//WAPFORUM//DTD SI 1.0//EN",
                "http://www.wapforum.org/DTD/si.dtd")
DOCTYPES[SL] = Doctype("sl", "-//WAPFORUM//DTD SL 1.0//EN",
                "http://www.wapforum.org/DTD/sl.dtd")


#DOCTYPES[CONTENTXML] = Doctype()
#DOCTYPES[GOOGLE] = Doctype()
#DOCTYPES[LOGML] = Doctype()
#DOCTYPES[POMTEST] = Doctype()
#DOCTYPES[RSS091] = Doctype()
#DOCTYPES[RSS2] = Doctype()
#DOCTYPES[WCSINVALIDATION] = Doctype()
#DOCTYPES[WURFL] = Doctype()
#DOCTYPES[XFDESKTOP_MENU] = Doctype()
#DOCTYPES[XMLSCHEMA] = Doctype()


NAMESPACES = {}
NAMESPACES[XHTML] = "http://www.w3.org/1999/xhtml"
NAMESPACES[XHTML1_STRICT] = NAMESPACES[XHTML]
NAMESPACES[XHTML1_FRAMESET] = NAMESPACES[XHTML]
NAMESPACES[XHTML1_TRANSITIONAL] = NAMESPACES[XHTML]
NAMESPACES[XHTML11] = NAMESPACES[XHTML]
NAMESPACES[WML] = NAMESPACES[XHTML]
NAMESPACES[WML11] = NAMESPACES[XHTML]
NAMESPACES[WML12] = NAMESPACES[XHTML]
NAMESPACES[WML13] = NAMESPACES[XHTML]
NAMESPACES[XHTML_MOBILE10] = NAMESPACES[XHTML]
NAMESPACES[XHTML_BASIC10] = NAMESPACES[XHTML]
NAMESPACES[XHTML_BASIC11] = NAMESPACES[XHTML]


def get_doctype(keyname):
  return DOCTYPES.get(keyname)

def get_mod_file(directory, sourcefilename):
    """get_mod_file(sourcefilename)
    Converts a file name into a file name importable by Python.
    """
    from pycopia.textutils import maketrans
    modname = os.path.splitext(os.path.split(sourcefilename)[1])[0]
    modname = modname.translate(maketrans("-. ", "___"))
    return (os.path.join(directory, modname + ".py"), 
                DOCTYPES.get("%s.%s" % (__name__, modname)))

