#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
COmmand interface to a plistconfig object. Used for interactive editing.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia import CLI
from pycopia import plistconfig


class ConfigCommands(CLI.BaseCommands):

    def ls(self, argv):
        """ls [subcontainer]
    Show container."""
        name = argv[1] if len(argv) > 1 else None
        if name is None:
            self._list(self._obj)
        else:
            try:
                subobj = self._obj[name]
            except KeyError:
                self._ui.error("Object not found: {}".format(name))
                return
            if isinstance(subobj, dict):
                self._print(name, ":")
                self._list(subobj)
            else:
                self._print(subobj)

    def _list(self, container):
        for key in container:
            val = container[key]
            if isinstance(val, dict):
                self._print("{:>18.18s} = {{...}}".format(key))
            else:
                self._print("{:>18.18s} = {!r}".format(key, val))

    def chdir(self, argv):
        """chdir/cd <container>
    Make <container> the current container."""
        name = argv[1]
        if name == "..":
            raise CLI.CommandQuit()
        item = self._get(name)
        if isinstance(item, dict):
            cmd = self.clone(ConfigCommands)
            cmd._setup(item, "%Ykey%N:{}> ".format(name))
            raise CLI.NewCommand(cmd)
        else:
            self._print("%s: not a container." % (name,))

    cd = chdir

    def mkdir(self, argv):
        """mkdir <name>
    Make a new container here."""
        name = argv[1]
        cont = self._obj
        for part in name.split("."):
            cont = cont.add_container(part)
        self._reset_scopes()

    def set(self, argv):
        """set [-t <type>] <name> <value>
    Sets the named attribute to a new value. The value will be converted into a
    likely suspect, but you can specify a type with the -t flag.  """
        tval = CLI.clieval
        optlist, longoptdict, args = self.getopt(argv, "t:")
        for opt, optarg in optlist:
            if opt == "-t":
                tval = eval(optarg, {}, {})
                if type(tval) is not type:
                    self._ui.error("Bad type.")
                    return
        try:
            value = tval(*tuple(args[1:]))
        except TypeError as terr:
            self._ui.error(err)
            return
        name = args[0]
        self._obj[name] = value
        self._reset_scopes()

    def delete(self, argv):
        """delete <name>
    Delete the named configuration item. The deleted item is saved and can be
    undeleted here or in a different container."""
        name = argv[1]
        try:
            obj = self._obj[name]
            del self._obj[name]
            self._reset_scopes()
            self._environ["stash"] = (name, obj)
        except KeyError:
            self._ui.error("No such item: %r." % (name,))
        else:
            self._print("%r deleted." % (name,))

    def undelete(self, argv):
        """undelete
    Restore a previously deleted item into the current container."""
        objt = self._environ.get("stash")
        if objt is None:
            self._print("Nothing to undelete.")
        else:
            self._obj[objt[0]] = objt[1]
            del self._environ["stash"]
            self._reset_scopes()

    def get(self, argv):
        """get/show <name>
    Show the value of <name>."""
        item = self._get(argv[1])
        if item is not None:
            self._print(repr(item))
        else:
            self._ui.error("No such item.")

    def move(self, argv):
        """move <name> <newlocation>
    Move an entry to another location. 
    Currently you can only move down the tree, not up (i.e. no ".." allowed)."""
        name = argv[1]
        newlocname = argv[2]
        item = self._obj.get(name)
        if item is None:
            self._ui.error("Source not found.")
            return
        newloc = self._get(newlocname)
        if isinstance(newloc, plistconfig.AutoAttrDict):
            newloc[name] = item
            del self._obj[name]
            self._reset_scopes()
        else:
            self._ui.error("Can't move to non container.")

    def rename(self, argv):
        """rename <key> <newkey>
    Rename a key name to another name."""
        oldname = argv[1]
        newname = argv[2]
        item = self._obj.get(oldname)
        if item is None:
            self._ui.error("Name not found.")
            return
        else:
            self._obj[newname] = item
            del self._obj[oldname]
            self._reset_scopes()

    def _reset_scopes(self):
        containers = [key for key in self._obj.keys() if isinstance(self._obj[key], dict)]
        noncontainers = [key for key in self._obj.keys() if not isinstance(self._obj[key], dict)]
        self.add_completion_scope("cd", containers)
        self.add_completion_scope("chdir", containers)
        self.add_completion_scope("ls", containers)
        self.add_completion_scope("get", noncontainers)
        self.add_completion_scope("delete", noncontainers)
        self.add_completion_scope("move", containers + noncontainers)

    def _get(self, name):
        item = self._obj
        for part in name.split("."):
            item = item.get(part)
        return item


class RootCommands(ConfigCommands):

    def _setup(self, obj, fname, prompt="> "):
        self._obj = obj
        self._fname = fname
        self._environ["PS1"] = str(prompt)
        self._reset_scopes()

    def finalize(self):
        if plistconfig.is_modified(self._obj) and self._ui.yes_no("Changes have been made. Commit?"):
            self._obj.tofile(self._fname)

    def commit(self, argv):
        """commit
    Save any changes."""
        self._obj.tofile(self._fname)

    save = commit # alias

    def saveas(self, argv):
        """saveas [<newfilename>]
    Save current configuration into new file."""
        fname = argv[1] if len(argv) > 1 else self._ui.get_value("File name to save as? ")
        plistconfig.write_config(self._obj, fname)



def plistcli(argv):
    """plistcli [-?D] <configfile>...

Provides an interactive CLI for editing a property list file.

Options:
   -?        = This help text.
   -D        = Debug on.
    """
    import os
    from pycopia import getopt

    try:
        optlist, longopts, args = getopt.getopt(argv[1:], "?")
    except getopt.GetoptError:
        print (plistcli.__doc__)
        return
    for opt, val in optlist:
        if opt == "-?":
            print (plistcli.__doc__)
            return
        if opt == "-D":
            from pycopia import autodebug

    io = CLI.ConsoleIO()
    ui = CLI.UserInterface(io)
    cmd = RootCommands(ui)
    for fname in args:
        root = plistconfig.get_config(fname)
        cmd._setup(root, fname, "%%Yplistconfig%%N:%s> " % (fname,))
        parser = CLI.CommandParser(cmd, historyfile=os.path.expandvars("$HOME/.hist_plistconfig"))
        parser.interact()

if __name__ == "__main__":
    import sys
    plistcli(sys.argv)
