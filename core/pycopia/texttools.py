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
Utility methods that perform various manipulations on text files.

"""

import string

def sub_lists(lines, subdict):
    newlines = []
    for line in lines:
        for tag, value in subdict.items():
            newline = string.replace(line, tag, value)
        newlines.append(newline)
    return newlines


def sub_file(template_fo, dest_fo, subdict):
    """
subfile(template, destination, substitutiondict)
where:
    template         - is a file object for the template file. This file
                       contains unique strings that must match the keys in the
                       subsititution dictionary (sustitutedict).
    destination      - is a file object that will have the template file with
                       substitutions written to it.
    substitutiondict - is a dictionary with keys that must match the tag
                       strings in the template file. The value of that
                       dictionary entry will be substituted for the tag in the
                       destination file.

    """
    for line in template_fo.readlines():
        for tag, value in subdict.items():
            line = string.replace(line, tag, value)
        dest_fo.write(line)

def sub_file_by_name(templatefilename, destfilename, subdict):
    tf = open(templatefilename, "r")
    df = open(destfilename, "w")
    sub_file(tf, df, subdict)
    df.close()
    tf.close()

