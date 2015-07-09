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
Parser and generator for sendmail style email alias files.

"""

import sys
import re

class Aliases(list):
    def __str__(self):
        return ", ".join(map(str, self))
    def parse(self, line):
        parts = line.split(",")
        self.extend(map(lambda s: s.strip(), parts))

class AliasLine(object):
    matcher = None

class AliasEntry(AliasLine):
    matcher = re.compile(r"^(\S+):\s*(.+)$", re.M)
    def __init__(self, name=None, *aliases):
        self.name = name
        self._aliases = Aliases()
        for alias in aliases:
            self.add_alias(alias)

    def __str__(self):
        return "%s: %s" % (self.name, self._aliases)

    def parse(self, line):
        mo = self.matcher.search(line)
        if mo:
            self.name = mo.group(1)
            self._aliases = Aliases()
            self._aliases.parse(mo.group(2))

    def add_alias(self, alias):
        if type(alias) is list:
            self._aliases.extend(alias)
        elif type(alias) is str:
            self._aliases.append(alias)
        else:
            raise TypeError, "AliasEntr alias must be string or list."

class Blankline(AliasLine):
    matcher = re.compile(r"^\s+$", re.M)
    def __str__(self):
        return "\n"

class Comment(AliasLine):
    matcher = re.compile(r"#(.*)$", re.M)
    def __init__(self, comment=None):
        self.comment = comment
    def __str__(self):
        if self.comment:
            return "# %s" % (self.comment,)
        else:
            return ""
    def parse(self, line):
        mo = self.matcher.search(line)
        if mo:
            self.comment = mo.group(1).strip()
        else:
            self.comment = None

class VirtualDomain(AliasEntry):
    matcher = re.compile(r"^@(\S+):\s*(.+)$", re.M)
    def __str__(self):
        return "@%s: %s" % (self.name, self._aliases)


class AliasFile(list):
    def __init__(self, filename=""):
        super(AliasFile, self).__init__()
        self.name = str(filename)
        if filename:
            fo = open(filename)
            self.parse(fo)
            fo.close()

    def __str__(self):
        return "\n".join(map(str, self))

    def parse(self, fo):
        for line in fo:
            if Blankline.matcher.search(line):
                self.append(Blankline())
                continue
            elif Comment.matcher.search(line):
                cm = Comment()
                cm.parse(line)
                self.append(cm)
                continue
            elif VirtualDomain.matcher.search(line):
                vd = VirtualDomain()
                vd.parse(line)
                self.append(vd)
                continue
            elif AliasEntry.matcher.search(line):
                ae = AliasEntry()
                ae.parse(line)
                self.append(ae)
                continue
            else:
                raise ValueError, "no match for line: %r" % (line,)

    def writefile(self, filename=None):
        name = filename or self.name
        if name:
            fo = open(name, "w")
            self.emit(fo)
            fo.close()

    def emit(self, fo):
        for lineobj in self:
            fo.write("%s\n" % (lineobj,))

    def getall(self, klass):
        for el in self:
            if isinstance(el, klass):
                yield el
    
    def get_aliases(self):
        return self.getall(AliasEntry)

    def get_alias_names(self):
        existing = []
        for entry in self.get_aliases():
            existing.append(entry.name)
        return existing

    def add_alias(self, name, *aliases):
        new = AliasEntry(name, *aliases)
        self.append(new)
    
    def add_comment(self, comment):
        self.append(Comment(comment))
    
    def add_virtual_domain(self, dname, *aliases):
        new = VirtualDomain(dname, *aliases)
        self.append(new)

    def add_blankline(self):
        self.append(Blankline())
    
def get_aliases(fname=""):
    aliases = AliasFile(fname)
    return aliases

def _test(argv):
    af = get_aliases("/etc/mail/aliases")
    af.emit(sys.stdout)
    return af

if __name__ == "__main__":
    af = _test(sys.argv)

