#!/usr/bin/python2.6
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
Useful interactive functions for building simple user interfaces.

"""

from __future__ import print_function


__all__ = ['get_text', 'get_input', 'default_error', 'choose',
        'choose_multiple', 'choose_value', 'choose_key',
        'choose_multiple_from_map', 'print_list', 'yes_no', 'edit_text',
        'print_menu_list', 'print_menu_map']

import sys, os

COLUMNS, LINES = 132, 32 # TODO fetch from system

# python 3 compatibility
try:
    raw_input
except NameError:
    raw_input = input


def get_text(prompt="", msg=None, input=raw_input):
    """Prompt user to enter multiple lines of text."""

    print ((msg or "Enter text.") + " End with ^D or a '.' as first character.")
    lines = []
    while True:
        try:
            line = input(prompt)
        except EOFError:
            break
        if line == ".": #  dot on a line by itself also ends
            break
        lines.append(line)
    return "\n".join(lines)

def get_input(prompt="", default=None, input=raw_input):
    """Get user input with an optional default value."""
    if default is not None:
        ri = input("%s [%s]> " % (prompt, default))
        if not ri:
            return default
        else:
            return ri
    else:
        return input("%s> " % (prompt, ))

def default_error(text):
    print(text, file=sys.stderr)

def choose(somelist, defidx=0, prompt="choose", input=raw_input, error=default_error):
    """Select an item from a list. Returns the object selected from the
    list index.
    """
    assert len(list(somelist)) > 0, "list to choose from has no elements!"
    print_menu_list(somelist)
    defidx = int(defidx)
    assert defidx >=0 and defidx < len(somelist), "default index out of range."
    while 1:
        try:
            ri = get_input(prompt, defidx+1, input) # menu list starts at one
        except EOFError:
            return None
        try:
            idx = int(ri)-1
        except ValueError:
            error("Bad selection. Type in the number.")
            continue
        else:
            try:
                return somelist[idx]
            except IndexError:
                error("Bad selection. Selection out of range.")
                continue


def choose_multiple(somelist, chosen=None, prompt="choose multiple", input=raw_input, error=default_error):
    somelist = somelist[:]
    if chosen is None:
        chosen = []
    while 1:
        print( "Choose from list. Enter to end, negative index removes from chosen.")
        print_menu_list(somelist)
        if chosen:
            print ("You have: ")
            print_menu_list(chosen)
        try:
            ri = get_input(prompt, None, input) # menu list starts at one
        except EOFError:
            return chosen
        if not ri:
            return chosen
        try:
            idx = int(ri)
        except ValueError:
            error("Bad selection. Type in the number.")
            continue
        else:
            if idx < 0:
                idx = -idx - 1
                try:
                    somelist.append(chosen[idx])
                    del chosen[idx]
                except IndexError:
                    error("Selection out of range.")
            elif idx == 0:
                error("No zero.")
            else:
                try:
                    chosen.append(somelist[idx-1])
                    del somelist[idx-1]
                except IndexError:
                    error("Selection out of range.")


def choose_value(somemap, default=None, prompt="choose", input=raw_input, error=default_error):
    """Select an item from a mapping. Keys are indexes that are selected.
    Returns the value of the mapping key selected.
    """
    first = print_menu_map(somemap)
    while 1:
        try:
            ri = get_input(prompt, default, input)
        except EOFError:
            return default
        if not ri:
            return default
        try:
            idx = type(first)(ri)
        except ValueError:
            error("Not a valid entry. Please try again.")
            continue

        if idx not in somemap:
            error("Not a valid selection. Please try again.")
            continue
        return somemap[idx]


def choose_key(somemap, default=0, prompt="choose", input=raw_input, error=default_error):
    """Select a key from a mapping. 
    Returns the key selected.
    """
    keytype = type(print_menu_map(somemap))
    while 1:
        try:
            userinput = get_input(prompt, default, input)
        except EOFError:
            return default
        if not userinput:
            return default
        try:
            idx = keytype(userinput)
        except ValueError:
            error("Not a valid entry. Please try again.")
            continue
        if idx not in somemap:
            error("Not a valid selection. Please try again.")
            continue
        return idx


def choose_multiple_from_map(somemap, chosen=None, prompt="choose multiple", 
            input=raw_input, error=default_error):
    """Choose multiple items from a mapping. 
    Returns a mapping of items chosen. Type in the key to select the values.
    """
    somemap = somemap.copy()
    if chosen is None:
        chosen = {}
    while 1:
        print("Choose from list. Enter to end, negative index removes from chosen.")
        if somemap:
            first = print_menu_map(somemap)
        else:
            print("(You have selected all possible choices.)")
            first = 0
        if chosen:
            print ("You have: ")
            print_menu_map(chosen)
        try:
            ri = get_input(prompt, None, input) # menu list starts at one
        except EOFError:
            return chosen
        if not ri:
            return chosen
        try:
            idx = type(first)(ri)
        except ValueError:
            error("Bad selection. Please try again.")
            continue
        else:
            if idx < 0: # FIXME assumes numeric keys
                idx = -idx # FIXME handle zero index
                try:
                    somemap[idx] = chosen[idx]
                    del chosen[idx]
                except KeyError:
                    error("Selection out of range.")
            else:
                try:
                    chosen[idx] = somemap[idx]
                    del somemap[idx]
                except KeyError:
                    error("Selection out of range.")


def print_list(clist, indent=0, width=74):
    indent = min(max(indent,0),width-1)
    if indent:
        print(" " * indent, end="")
    col = indent + 2
    for c in clist[:-1]:
        ps = str(c) + ","
        col = col + len(ps) + 1
        if col > width:
            print()
            col = indent + len(ps) + 1
            if indent:
                print (" " * indent, end="")
        print (ps, end="")
    if col + len(clist[-1]) > width:
        print()
        if indent:
            print (" " * indent, end="")
    print (clist[-1])


def yes_no(prompt, default=True, input=raw_input):
    yesno = get_input(prompt, "Y" if default else "N", input)
    return yesno.upper().startswith("Y")

def edit_text(text, prompt="Edit text"):
    """Run $EDITOR on text."""
    fname = os.tempnam(os.environ["HOME"], prompt[:5])
    fo = open(fname, "w")
    fo.write(prompt + ":\n")
    fo.write(text)
    fo.close()
    os.system('%s "%s"' % (os.environ["EDITOR"], fname))
    fo = open(fname, "r")
    try:
        text = fo.read()
    finally:
        fo.close()
        os.unlink(fname)
    return text[text.find("\n")+1:]

def print_menu_list(clist, lines=LINES, columns=COLUMNS):
    """Print a list with leading numeric menu choices. Use two columns in necessary."""
    h = max((len(clist)/2)+1, lines)
    i1, i2 = 1, h+1
    fmt = "{{:3d}}: {{:{cols}.{cols}}}".format(cols=columns-6)
    if h != lines:
        fmt2 = "{{:3d}}: {{:{cols}.{cols}}} | {{:3d}}: {{:{cols}.{cols}}}".format(cols=(columns-14)/2)
    for c1, c2 in map(None, clist[:h], clist[h:]):
        if c2:
            print (fmt2.format(i1, str(c1)[-(columns/2)+7:], i2, str(c2)[-(columns/2)+7:]))
        else:
            print (fmt.format(i1, str(c1)[-columns+7:]))
        i1 += 1
        i2 += 1

def print_menu_map(mapping, lines=LINES, columns=COLUMNS):
    """Print a list with leading numeric menu choices. Use two columns in necessary."""
    keys = sorted(mapping.keys())
    first = keys[0]
    fmt  = "{{!s:>4s}}: {{:{cols}.{cols}}}".format(cols=columns-6)
    fmt2 = "{{!s:>4s}}: {{:{cols}.{cols}}} | {{!s:>4s}}: {{:{cols}.{cols}}}".format(cols=(columns-16)/2)
    h = max((len(mapping)/2)+1, lines)
    for k1, k2 in map(None, keys[:h], keys[h:]):
        if k2 is not None:
            print (fmt2.format(k1, mapping[k1], k2, mapping[k2]))
        else:
            print (fmt.format(k1, mapping[k1]))
    return first


def _test(argv):
    from pycopia import autodebug
    #from pycopia import autodebug
    #import string
    #l = list(string.ascii_letters)
    #c = choose(l)
    #print (c)
    #l1 = choose_multiple(l)
    #print (edit_text(__doc__))
    #sel = dict(enumerate("abcd"))
    #print (choose_multiple_from_map(sel))
    bs = "".join(map(chr, range(33,111)))
    l = [bs] * 100
    #print(bs)
    #print("----")
    #print(l)
    #print("----")
    print_menu_list(l)
    print_menu_map(dict(enumerate(l)))

if __name__ == "__main__":
    import sys
    _test(sys.argv)

