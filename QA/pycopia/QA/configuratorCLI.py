#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# License: LGPL
# Keith Dart <keith@dartworks.biz>

"""
Command Interface for testing Configurator and DUT.

"""


from pycopia import CLI
from pycopia import IO
from pycopia import UI

class ConfiguratorShellCLI(CLI.GenericCLI):

    def _setup(self, obj, name):
        # Obtain host name directly from device.
        # this also asserts the configurator is working.
        self._obj = obj
        hostname = obj.hostname()
        self._environ["hostname"] = hostname
        self._environ["PS1"] = "Configurator(%%I%s%%N)> " % (hostname,)
        self._namespace = {"ctor":self._obj, "environ":self._environ}
        self._reset_scopes()

    def command(self, argv):
        """command <command>
    Run any shell command and return its output and exit status."""
        cmd = " ".join(argv[1:])
        if cmd:
           res, rv = self._obj.command(cmd)
        if rv:
            self._print(res)
        else:
            self._print("Bad exit: %s" % (rv,))
            self._print(res)

    def tail(self, argv):
        """tail <fname> [<filter>]
    tail a file, using the optional filter regular expression to filter lines."""
        fname = argv[1]
        if len(argv) > 2:
            filt = argv[2]
        else:
            filt = None
        s = self._obj
        s.tail(fname, filt)
        try:
            while 1:
                l = s.readline()
                self._print(l)
        except KeyboardInterrupt:
            s.interrupt()

    def exit(self, argv):
        """exit
    Exit from root if root. If not root, exit shell configurator."""
        if self._obj.is_root():
            self._obj.exit()
            return
        else:
            self._obj.exit()
            raise CommandQuit


class ConfiguratorTheme(UI.DefaultTheme):
    pass

def configurator_cli(argv):
    """configurator_cli [-s <script>] [-g] <device>

    Interact with a DUT configurator. If no device is specified use the testbed DUT.

    Options:
        -g Use paged output (like 'more')
        -s <script> Run a CLI script from the given file instead of entering
           interactive mode.

    """
    import os
    from pycopia.QA import configurator
    from pycopia import getopt
    from pycopia.storage import Storage

    paged = False 
    script = None

    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "s:?g")
    except GetoptError:
            print configurator_cli.__doc__
            return
    for opt, val in optlist:
        if opt == "-?":
            print configurator_cli.__doc__
            return
        elif opt == "-g":
            paged = True
        elif opt == "-s":
            script = val

    if not args:
        print configurator_cli.__doc__
        return

    if paged:
        from pycopia import tty
        io = tty.PagedIO()
    else:
        io = IO.ConsoleIO()

    # do runtime setup
    cf = Storage.get_config(initdict=longopts)
    cf.reportfile = "configurator_cli"
    cf.logbasename = "configurator_cli.log"
    cf.arguments = argv

    dev = cf.devices[args[0]]

    ctor = configurator.get_configurator(dev, logfile=cf.logfile)

    # construct the CLI
    theme = ConfiguratorTheme("Configurator> ")
    ui = UI.UserInterface(io, cf, theme)
    cmd = CLI.get_generic_cmd(ctor, ui, ConfiguratorShellCLI)
    cmd.device = dev # stash actual device for future reference
    parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_configurator"))

    if script:
        try:
            parser.parse(script)
        except KeyboardInterrupt:
            pass
    else:
        parser.interact()
    try:
        ctor.exit()
    except:
        pass


if __name__ == "__main__":
    import sys
    configurator_cli(sys.argv)
