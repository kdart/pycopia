#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
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
GRUB library. Used to read and write GRUB config files.

"""

from pycopia import dictlib
import re

BUILTIN_CMDLINE     = 0x1   # Run in the command-line.
BUILTIN_MENU        = 0x2   # Run in the menu.  
BUILTIN_TITLE       = 0x4   # Only for the command title.
BUILTIN_SCRIPT      = 0x8   # Run in the script.  
BUILTIN_NO_ECHO     = 0x10  # Don't print command on booting.
BUILTIN_HELP_LIST   = 0x20  # Show help in listing. 


class GrubCommand(object):
    def __init__(self, name, flags):
        self.name = name
        self.flags = flags

COMMANDS = dictlib.AttrDict()
COMMANDS.blocklist = GrubCommand("blocklist", BUILTIN_CMDLINE | BUILTIN_HELP_LIST)
COMMANDS.boot = GrubCommand("boot", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.bootp = GrubCommand("bootp", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.cat = GrubCommand("cat", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.chainloader = GrubCommand("chainloader", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.cmp = GrubCommand("cmp", BUILTIN_CMDLINE,)
COMMANDS.color = GrubCommand("color", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.configfile = GrubCommand("configfile", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.debug = GrubCommand("debug", BUILTIN_CMDLINE,)
COMMANDS.default = GrubCommand("default", BUILTIN_MENU,)
COMMANDS.device = GrubCommand("device", BUILTIN_MENU | BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.dhcp = GrubCommand("dhcp", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.displayapm = GrubCommand("displayapm", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.displaymem = GrubCommand("displaymem", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.dump = GrubCommand("dump", BUILTIN_CMDLINE,)
COMMANDS.embed = GrubCommand("embed", BUILTIN_CMDLINE,)
COMMANDS.fallback = GrubCommand("fallback", BUILTIN_MENU,)
COMMANDS.find = GrubCommand("find", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.fstest = GrubCommand("fstest", BUILTIN_CMDLINE,)
COMMANDS.geometry = GrubCommand("geometry", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.halt = GrubCommand("halt", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.help = GrubCommand("help", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.hiddenmenu = GrubCommand("hiddenmenu", BUILTIN_MENU,)
COMMANDS.hide = GrubCommand("hide", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.ifconfig = GrubCommand("ifconfig", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.impsprobe = GrubCommand("impsprobe", BUILTIN_CMDLINE,)
COMMANDS.initrd = GrubCommand("initrd", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.install = GrubCommand("install", BUILTIN_CMDLINE,)
COMMANDS.ioprobe = GrubCommand("ioprobe", BUILTIN_CMDLINE,)
COMMANDS.kernel = GrubCommand("kernel", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.lock = GrubCommand("lock", BUILTIN_CMDLINE,)
COMMANDS.makeactive = GrubCommand("makeactive", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.map = GrubCommand("map", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.md5crypt = GrubCommand("md5crypt", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.module = GrubCommand("module", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.modulenounzip = GrubCommand("modulenounzip", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.pager = GrubCommand("pager", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.partnew = GrubCommand("partnew", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.parttype = GrubCommand("parttype", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.password = GrubCommand("password", BUILTIN_MENU | BUILTIN_CMDLINE | BUILTIN_NO_ECHO,)
COMMANDS.pause = GrubCommand("pause", BUILTIN_CMDLINE | BUILTIN_NO_ECHO,)
COMMANDS.quit = GrubCommand("quit", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.rarp = GrubCommand("rarp", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.read = GrubCommand("read", BUILTIN_CMDLINE,)
COMMANDS.reboot = GrubCommand("reboot", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.root = GrubCommand("root", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.rootnoverify = GrubCommand("rootnoverify", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.savedefault = GrubCommand("savedefault", BUILTIN_CMDLINE,)
COMMANDS.serial = GrubCommand("serial", BUILTIN_MENU | BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.setkey = GrubCommand("setkey", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.setup = GrubCommand("setup", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.terminal = GrubCommand("terminal", BUILTIN_MENU | BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.terminfo = GrubCommand("terminfo", BUILTIN_MENU | BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.testload = GrubCommand("testload", BUILTIN_CMDLINE,)
COMMANDS.testvbe = GrubCommand("testvbe", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.tftpserver = GrubCommand("tftpserver", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.timeout = GrubCommand("timeout", BUILTIN_MENU,)
COMMANDS.title = GrubCommand("title", BUILTIN_TITLE,)
COMMANDS.unhide = GrubCommand("unhide", BUILTIN_CMDLINE | BUILTIN_MENU | BUILTIN_HELP_LIST,)
COMMANDS.uppermem = GrubCommand("uppermem", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)
COMMANDS.vbeprobe = GrubCommand("vbeprobe", BUILTIN_CMDLINE | BUILTIN_HELP_LIST,)



class GrubComment(object):
    def __init__(self, text):
        self.text = str(text)
    def __str__(self):
        return "#"+self.text

class GrubEntry(object):
    def __init__(self, cmd, params):
        self.cmd = cmd
        self.params = params
    def __str__(self):
        return "%s %s" % (self.cmd.name, self.params)

class GrubTitleEntry(object):
    def __init__(self, title):
        self.title = title
        self.lines = []
    def __str__(self):
        s = ["title %s" % (self.title,)]
        s.extend(map(lambda l: "    %s" % (l,), self.lines))
        return "\n".join(s)

class GrubConfig(object):
    def __init__(self, text=None):
        self.lines = []
        if text:
            self.parse(text)

    def __str__(self):
        return "\n".join(map(str, self.lines))

    def parse(self, text):
        linesplitter = re.compile(r"[ \t=]")
        self.lines = []
        state = 0
        currenttitle = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#"):
                self.lines.append(GrubComment(line[1:]))
                continue
            if not line:
                continue
            if state == 0:
                cmd, rest = linesplitter.split(line, 1)
                CMD = COMMANDS[cmd]
                if CMD.flags & BUILTIN_TITLE:
                    state = 1
                    currenttitle = GrubTitleEntry(rest)
                    self.lines.append(currenttitle)
                    continue
                elif CMD.flags & BUILTIN_MENU:
                    self.lines.append(GrubEntry(CMD, rest))
            if state == 1:
                cmd, rest = linesplitter.split(line, 1)
                CMD = COMMANDS[cmd]
                if CMD.flags & BUILTIN_TITLE:
                    currenttitle = GrubTitleEntry(rest)
                    self.lines.append(currenttitle)
                elif CMD.flags & (BUILTIN_CMDLINE | BUILTIN_MENU):
                    currenttitle.lines.append(GrubEntry(CMD, rest))


    def add_comment(self, text):
        self.lines.append(GrubComment(text))



def _test(argv):
    text = open("/home/kdart/tmp/grub.conf").read()
    r = GrubConfig(text)
    print r
    return r

if __name__ == "__main__":
    import sys
    r = _test(sys.argv)

