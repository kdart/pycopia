#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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

<http://www.w3.org/TR/2000/REC-xml-20001006#sec-prolog-dtd>

Enforces DOCTYPE rules.

XXX needs work

"""

#[28]    doctypedecl    ::=    '<!DOCTYPE' S Name (S ExternalID)? S? ('[' (markupdecl | DeclSep)* ']' S?)? '>'
#[28a]    DeclSep    ::=    PEReference | S [WFC: PE Between Declarations]
#[29]    markupdecl    ::=    elementdecl | AttlistDecl | EntityDecl | NotationDecl | PI | Comment

class _ExternalID(object):
    def __init__(self, *args):
        self.identifiers = args
    def __str__(self):
        s = [self.__class__.__name__]
        for it in self.identifiers:
            s.append('"%s"' % (it,))
        return " ".join(s)

class PUBLIC(_ExternalID):
    pass

class SYSTEM(_ExternalID):
    pass

class Doctype(object):
    def __init__(self, name, externalid=None, markupdecl=None):
        self.name = name
        self.externalid = externalid
        self.markupdecl = markupdecl or []
    def __str__(self):
        parts = [self.name]
        if self.externalid:
            parts.append(str(self.externalid))
        if self.markupdecl:
            parts.append("[%s]" % self.markupdecl)
        return '<!DOCTYPE %s>' % (" ".join(parts),)

    def add_system(self, *sysnames):
        self.externalid = SYSTEM(*sysnames)

    def add_public(self, *pubnames):
        self.externalid = PUBLIC(*pubnames)
    
    # TODO: DTD declaration syntax objects
    def add_declaration(self, decl):
        self.markupdecl.append(decl)


def get_doctype(name, public=None, system=None):
    if system:
        exid = SYSTEM(public)
    elif public:
        exid = PUBLIC(public)
    else:
        exid = None
    return Doctype(name, exid)


