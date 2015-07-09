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
    template_fo
       is a file object for the template file. This file contains unique
       strings that must match the keys in the subsititution dictionary
       (sustitutedict).
    dest_fo
        is a file object that will have the template file with substitutions written to it.
    subdict
        is a dictionary with keys that must match the tag strings in the
        template file. The value of that dictionary entry will be substituted
        for the tag in the destination file.

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

