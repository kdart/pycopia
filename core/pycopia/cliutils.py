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
Useful interactive functions for building simple user interfaces.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


__all__ = ['get_text', 'get_input', 'default_error', 'choose',
        'choose_multiple', 'choose_value', 'choose_key',
        'choose_multiple_from_map', 'print_list', 'yes_no', 'edit_text',
        'print_menu_list', 'print_menu_map']

import sys, os
import ast

# python 3 compatibility
try:
    raw_input
except NameError:
    raw_input = input


def _get_winsize(fd):
    if os.isatty(fd):
        import fcntl, struct, termios
        WINSIZEFMT = b"HHHH"
        winsize = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0"*struct.calcsize(WINSIZEFMT))
        l, c = struct.unpack(WINSIZEFMT, winsize)[:2] # row, col, xpix, ypix
        return max(l, 24), max(c, 80)
    else:
        return 24, 80

LINES, COLUMNS = _get_winsize(0)
del _get_winsize


def default_error(text):
    print(text, file=sys.stderr)


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

def get_type(atype, prompt="", default=None, input=raw_input, error=default_error):
    """Get user input of a particular base type."""
    while 1:
        if default is not None:
            text = input("%s [%s]> " % (prompt, default))
            if not text:
                return default
        else:
            text = input("%s> " % (prompt, ))
        try:
            val = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            error("Error in input. Please enter a {} value.".format(atype.__name__))
            continue
        if type(val) is atype:
            return val
        else:
            error("Please enter a {} value.".format(atype.__name__))

def get_int(prompt="", default=None, input=raw_input, error=default_error):
    return get_type(int, prompt, default, input, error)

def get_float(prompt="", default=None, input=raw_input, error=default_error):
    return get_type(float, prompt, default, input, error)

def get_bool(prompt="", default=None, input=raw_input, error=default_error):
    return get_type(bool, prompt, default, input, error)

def get_tuple(prompt="", default=None, input=raw_input, error=default_error):
    return get_type(tuple, prompt, default, input, error)

def get_list(prompt="", default=None, input=raw_input, error=default_error):
    return get_type(list, prompt, default, input, error)

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
    """Run $EDITOR on text. Defaults to vim."""
    fname = os.path.join(os.environ["HOME"], ".edit_text.txt")
    fo = open(fname, "w")
    fo.write(prompt + ":\n")
    fo.write(text)
    fo.close()
    os.system('%s "%s"' % (os.environ.get("EDITOR", "/usr/bin/vim"), fname))
    fo = open(fname, "r")
    try:
        text = fo.read()
    finally:
        fo.close()
        os.unlink(fname)
    return text[text.find("\n")+1:]


def print_menu_list(clist, lines=LINES, columns=COLUMNS):
    """Print a list with leading numeric menu choices. Use two columns in necessary."""
    fmt = "{{:3d}}: {{:{cols}.{cols}}}".format(cols=columns-6)
    if columns > 80:
        fmt2 = "{{:3d}}: {{:{cols}.{cols}}} | {{:3d}}: {{:{cols}.{cols}}}".format(cols=(columns-14)//2)
        h = (len(clist)+1)//2
        i1, i2 = 1, h+1
        for c1, c2 in map(None, clist[:h], clist[h:]):
            if c2:
                print (fmt2.format(i1, str(c1)[-(columns//2)+7:], i2, str(c2)[-(columns//2)+7:]))
            else:
                print (fmt.format(i1, str(c1)[-columns+7:]))
            i1 += 1
            i2 += 1
    else:
        for i, c1 in enumerate(clist):
            print (fmt.format(i+1, str(c1)[-columns+7:]))


def print_menu_map(mapping, lines=LINES, columns=COLUMNS):
    """Print a list with leading numeric menu choices. Use two columns in necessary."""
    keys = sorted(mapping.keys())
    first = keys[0]
    fmt  = "{{!s:>4s}}: {{:{cols}.{cols}}}".format(cols=columns-6)
    if columns > 80:
        fmt2 = "{{!s:>4s}}: {{:{cols}.{cols}}} | {{!s:>4s}}: {{:{cols}.{cols}}}".format(cols=(columns-16)//2)
        h = (len(mapping)+1)//2
        for k1, k2 in map(None, keys[:h], keys[h:]):
            if k2 is not None:
                print (fmt2.format(k1, mapping[k1], k2, mapping[k2]))
            else:
                print (fmt.format(k1, mapping[k1]))
    else:
        for key in keys:
            print (fmt.format(key, mapping[key]))
    return first


def _test(argv):
    from pycopia import autodebug
    print ("columns:", COLUMNS, "ines:", LINES)
    #from pycopia import autodebug
    #import string
    #l = list(string.ascii_letters)
    #c = choose(l)
    #print (c)
    #l1 = choose_multiple(l)
    #print (edit_text(__doc__))
    #sel = dict(enumerate("abcd"))
    #print (choose_multiple_from_map(sel))
    lsize = LINES
    l = []
    for i in range(lsize):
        l.append("{}_{}".format(i, "".join(map(chr, range(34,109)))))
    #print(bs)
    #print("----")
    #print(l)
    #print("----")
    choose_multiple(l, prompt="choose")
    #print_menu_map(dict(enumerate(l)))
    print(repr(get_int("age")))
    print(repr(get_int("age", 22)))
    print(repr(get_float("weight")))

if __name__ == "__main__":
    import sys
    _test(sys.argv)

