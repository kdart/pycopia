#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>


"""
Module used to extract Pycopia-QA test plan documentation from the set of
automated test plans found in the test module location.
"""

import sys, os, re, shutil
import locale
try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_file

# for checking base class
from types import ModuleType

from pycopia.QA import core
from pycopia.storage import Storage


def fix_path():
    TESTHOME = os.environ.get("TESTHOME")
    if not TESTHOME:
        raise ValueError, "I don't know where to find tests. Try setting TESTHOME"
    sys.path.append(TESTHOME)
    return TESTHOME

def build_testplans(argv):
    from pycopia.WWW import XHTML
    py_matcher = re.compile(r"(^[a-zA-Z]+)\.py$", re.M)
    HOME = fix_path()
    STYLESHEET = "/stylesheets/qa_tp.css"
    hl = len(HOME)+1
    if len(argv) > 1:
        DOCDIR = os.path.expanduser(os.path.expandvars(argv[1]))
    else:
        DOCDIR = "/var/www/localhost/htdocs/testplans"
    os.chdir(DOCDIR)
    index = XHTML.new_document(XHTML.STRICT)
    index.add_title("Test Plan Index")
    index.add_to_head("Link", rel="stylesheet", href=STYLESHEET, type="text/css")
    index.add_header(1, "Test Plan Index")
    index.add_para("""Below is a list of test packages. Each test module
located in the package is documented inside the package document.  """)
    UL = index.get_unordered_list()
    index.append(UL)

    for dirname, dirs, files in os.walk(HOME):
        if "__init__.py" in files:
            pkgname = ".".join(dirname[hl:].split("/"))
            rstname = pkgname.replace(".", "_")+".rst"
            htmlname = pkgname.replace(".", "_")+".html"

            A = index.get_element("A", href=htmlname)
            A.add_text(pkgname)
            UL.add_item(A)

            fo = file(rstname, "w")
            extract_package(fo, pkgname)
            fo.close()
            publish_file(source_path=rstname, parser_name='restructuredtext', 
                        writer_name='html', destination_path=htmlname,
                        settings_overrides={"stylesheet":STYLESHEET})
            for fname in files: # copy any included files to destination
                if fname[-3:] in ("jpg", "png", "gif", "rst"):
                    shutil.copy(os.path.join(dirname, fname), DOCDIR)
        else:
            for fname in files:
                mo = py_matcher.match(fname)
                if mo:
                    modname = mo.group(1)
                    rstname = modname.replace(".", "_")+".rst"
                    htmlname = modname.replace(".", "_")+".html"

                    A = index.get_element("A", href=htmlname)
                    A.add_text(modname)
                    UL.add_item(A)

                    fo = file(rstname, "w")
                    extract_module(fo, modname)
                    fo.close()
                    publish_file(source_path=rstname, parser_name='restructuredtext', 
                                writer_name='html', destination_path=htmlname,
                                settings_overrides={"stylesheet":STYLESHEET})

    indexfile = file("testplan_index.html", "w")
    index.emit(indexfile)
    indexfile.close()


# Scan the module for test cases defined in it and write them to the file
# object. Also write the module level documentation. This will create a
# structured document that closely matches the Python package structure.
def mod_doc(fo, mod):
    setattr(mod, "_visited_", True)
    fo.write("\n.. _%s:\n" % (mod.__name__.split(".")[-1],))
    fo.write(mod.__doc__) # module doc, should be RST
    fo.write("\n:Module Name:\n")
    fo.write("    %s\n" %(mod.__name__,))
    if hasattr(mod, "__all__"):
        fo.write(":Test Modules:\n")
        for name in mod.__all__:
            fo.write("    - %s_\n" %(name,))
    if hasattr(mod, "get_suite"):
        fo.write("\n:Default Tests:\n")
        cf = Storage.get_config()
        suite = mod.get_suite(cf)
        for test in suite:
            fo.write("    - %r\n" %(test,))
    fo.write("\n")
    for name in dir(mod):
        obj = getattr(mod, name)
        if type(obj) is type(object) and issubclass(obj, core.Test):
            if mod.__name__ == obj.__module__: # defined in THIS module
                # test ID is full class path
                if obj.__doc__:
                    tid = "%s.%s" % (obj.__module__, obj.__name__)
                    head = "Test Case: %s" % (obj.__name__,)
                    fo.write("\n.. _%s:\n\n%s\n" % (obj.__name__, head))
                    fo.write("-"*len(head))       # Test class header should be H2
                    fo.write("\n:Test Case ID:\n")
                    fo.write("    %s\n" %(tid,))
                    fo.write(obj.__doc__)
                fo.write("\n")
        elif type(obj) is ModuleType:
            if (hasattr(obj, "__path__") and os.path.split(obj.__file__)[0].startswith(os.path.split(mod.__file__)[0])) or \
                        obj.__name__.startswith(mod.__name__): # sub package or module
                if not hasattr(obj, "_visited_"):
                    #setattr(obj, "_visited_", True)
                    mod_doc(fo, obj)


def extract_module(fo, modname):
    """Extract a single modules test plan documents."""
    mod = __import__(modname)
    mod_doc(fo, mod)

def extract_package(fo, pkgname):
    """Create one large RST document from a package of test modules."""
    pkg = __import__(pkgname, globals(), locals(), ['*'])
    assert hasattr(pkg, "__path__")
    mod_doc(fo, pkg)

def extract_main(argv):
    """Reads the modules in the named package root, and writes RST (from the
    docstrings) to the given file (or stdout)."""
    close = lambda : None
    try:
        fname = argv[2]
    except IndexError:
        fo = sys.stdout
    else:
        if fname == "-":
            fo = sys.stdout
        else:
            fo = file(fname, "w")
            close = fo.close
    pkgname = argv[1]

    extract_package(fo, pkgname)
    close() # don't close stdout

def _test(argv):
    build_testplans(["build_testplans"])

if __name__ == "__main__":
    _test(sys.argv)

