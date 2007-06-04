#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Top level test runner.  This module is the primary test runner for the
automation framework. It instantiates the configuration object and the test
suites, then initializes and runs them. 

From the command line (using the 'runtest' program):

runtest <testmodulename>...

Options:
    -h   - print help
    -d   - debug mode
    -v   - be more verbose
    -f <filename>  - Use <filename> to load additional configuration.

or, in a script,

---------
#!/usr/bin/python
from pycopia import testrunner
import mytestmodule

testrunner.run_module(mytestmodule)
---------

"""

import sys, os
import shutil

from pycopia import getopt
from pycopia import scheduler
from pycopia import timelib
from pycopia.storage import Storage 

__testrunner = None

class TestRunner(object):
    def __init__(self):
        cf = Storage.get_config()
        self._config = cf
        TESTHOME = os.environ.get("TESTHOME", self._config.get("TESTHOME"))
        if not TESTHOME:
            raise ValueError, "I don't know where to find tests. Try setting TESTHOME"
        sys.path.append(TESTHOME)

    def get_config(self):
        return self._config

    def __call__(self, argv):
        cf = self._config
        optlist, extraopts, args = getopt.getopt(argv[1:], "hdvc:f:n:N")
        for opt, optarg in optlist:
            if opt == "-h":
                print __doc__
                sys.exit(2)
            if opt == "-d":
                cf.flags.DEBUG += 1
            if opt == "-v":
                cf.flags.VERBOSE += 1
            if opt == "-c" or opt == "-f":
                cf.mergefile(optarg)
            if opt == "-n":
                cf.NOTE = optarg
            if opt == "-N":
                cf.flags.NONOTE = True
        cf.update(extraopts)
        cf.argv = args # test args
        cf.arguments = [os.path.basename(argv[0])] + argv[1:] # original command line

        self.initialize()
        if cf.argv:
            self.run_modules(cf.argv)
        else:
            from pycopia import cliutils
            testlist = self.get_test_list()
            try:
                test = cliutils.choose(testlist)
            except:
                return None
            else:
                self.run_module(test)
        self.finalize()

    def run_module(self, mod):
        """run_module(module)
    Runs the module. The parameter should be a module object, but if it is a
    string then a module object with that name will be imported. 
    """
        cf = self._config
        if type(mod) is str:
            mod = self.get_module(mod)
        if not mod:
            raise ValueError, "Unable to locate test module"
        try:
            cf.module_ID = mod._ID
        except AttributeError:
            cf.module_ID = "<unknown>"
        cf.reportbasename = mod.__name__.replace(".", "_")
        cf.logbasename = "%s.log" % (cf.reportbasename,)
        # merge any test-module specific config files.
        testconf = os.path.join(os.path.dirname(mod.__file__) , "%s.conf" % (mod.__name__.split(".")[-1],))
        cf.mergefile(testconf)
        # resultsdir is where you would place any resulting data files.
        starttime = timelib.now()
        cf.resultsdir = os.path.join(
                os.path.expandvars(cf.get("resultsdirbase", "/var/tmp")),
                "%s-%s" % (cf.reportbasename, timelib.strftime("%Y%m%d%H%M", timelib.localtime(starttime)))
        )
        # make results dir, don't worry if it already exists
        try:
            os.mkdir(cf.resultsdir)
        except OSError, errno:
            if errno[0] == EEXIST:
                pass
            else:
                raise
        # firstly, run the module-level initialize function.
        if hasattr(mod, "initialize") and callable(mod.initialize):
            if cf.flags.DEBUG:
                try:
                    mod.initialize(cf)
                except:
                    ex, val, tb = sys.exc_info()
                    from pycopia import debugger
                    debugger.post_mortem(ex, val, tb)
            else:
                mod.initialize(cf)

        rpt = cf.get_report()
        cf.reportfilenames = rpt.filenames # Report file's names. save for future use.
        rpt.initialize()
        rpt.logfile(cf.logfilename)
        rpt.add_title("Test Results for module %r." % (mod.__name__, ))
        rpt.add_message("ARGUMENTS", " ".join(cf.arguments))
        note = self.get_note()
        if note:
            rpt.add_message("NOTE", note)
            self._config.comment = note
        else:
            self._config.comment = "<none>"
        self._reporturl(rpt)
        rpt.add_message("MODULESTART", timelib.strftime("%a, %d %b %Y %H:%M:%S %Z", timelib.localtime(starttime)))
        mod.run(cf) # run the test!
        rpt.add_message("MODULEEND", timelib.localtimestamp())
        rpt.finalize()
        # force close of report and logfile between modules
        cf.logfile.flush()
        del cf.report ; del cf.logfile 
        for fname in cf.reportfilenames:
            if not fname.startswith("<"):
                shutil.move(fname, cf.resultsdir)

        # lastly, run the module-level finalize function.
        if hasattr(mod, "finalize") and callable(mod.finalize):
            if cf.flags.DEBUG:
                try:
                    mod.finalize(cf)
                except:
                    ex, val, tb = sys.exc_info()
                    from pycopia import debugger
                    debugger.post_mortem(ex, val, tb)
            else:
                mod.finalize(cf)

    def _reporturl(self, rpt):
        cf = self._config
        baseurl = cf.get("baseurl")
        documentroot = cf.get("documentroot")
        resultsdir = cf.resultsdir
        if baseurl and documentroot:
            rpt.add_url("RESULTSDIR", baseurl+resultsdir[len(documentroot):])
        else:
            rpt.add_message("RESULTSDIR", resultsdir)

    def run_modules(self, modlist):
        """run_modules(modlist)
    Runs the run_module() function on the supplied list of modules (or module
    names).  """
        for mod in modlist:
            self.run_module(mod)
            # give things time to "settle" from previous suite. Some spawned
            # processes may delay exiting and hold open TCP ports, etc.
            scheduler.sleep(2) 

    def get_module(self, name):
        if sys.modules.has_key(name):
            return sys.modules[name]
        try:
            mod = __import__(name)
            components = name.split('.')
            for comp in components[1:]:
                mod = getattr(mod, comp)
        except ImportError:
            print >>sys.stderr, "*** Could not find test module %s." % (name)
            return None
        else:
            return mod

    def get_note(self):
        note = self._config.get("NOTE")
        if note:
            return note
        elif not self._config.flags.get("NONOTE"):
            from pycopia import cliutils
            return cliutils.get_text("> ", "Enter a small note to describe the test conditions. End with single '.'.")
        else:
            return None

    # overrideable interace follows

    def initialize(self):
        pass

    def finalize(self):
        pass

    def get_test_list(self):
        import glob
        TESTHOME = os.environ.get("TESTHOME", self._config.get("TESTHOME"))
        if not TESTHOME:
            raise ValueError, "I don't know where to find tests. Try setting TESTHOME"
        modnames = []
        os.path.walk(TESTHOME, _collect, modnames)
        modnames = map(lambda n: n[len(TESTHOME)+1:].replace("/", "."), modnames)
        return modnames



def get_testrunner():
    global __testrunner
    if not __testrunner:
        __testrunner = TestRunner()
    return __testrunner

def delete_testrunner():
    global __testrunner
    __testrunner = None


# callback for testdir walker
def _collect(flist, dirname, names):
    for name in names:
        if name.endswith(".py") and not name.startswith("_") and (name.find("CVS") == -1):
            flist.append(os.path.join(dirname, name[:-3]))

def main(argv):
    tr = get_testrunner()
    tr(argv)

