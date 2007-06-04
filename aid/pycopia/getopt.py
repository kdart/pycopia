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
Special getopt function. It returns long options as a dictionary. Any
name-value pair may be given on the command line.

"""

import sys, os

class GetoptError(Exception):
    opt = ''
    msg = ''
    def __init__(self, msg, opt):
        self.msg = msg
        self.opt = opt
        Exception.__init__(self, msg, opt)

    def __str__(self):
        return self.msg


def getopt(args, shortopts):
    """getopt(args, options) -> opts, long_opts, args 
Returns options as list of tuples, long options as entries in a dictionary, and
the remaining arguments."""
    opts = []
    longopts = {}
    while args and args[0].startswith('-') and args[0] != '-':
        if args[0] == '--':
            args = args[1:]
            break
        if args[0].startswith('--'):
            arg = args.pop(0)
            _do_longs(longopts, arg)
        else:
            opts, args = _do_shorts(opts, args[0][1:], shortopts, args[1:])

    return opts, longopts, args

def _do_longs(longopts, opt):
    try:
        i = opt.index('=')
    except ValueError:
        raise GetoptError('long options require arguments in the form opt=arg.', opt)
    opt, optarg = opt[2:i], opt[i+1:]
    longopts[opt] = optarg
    return longopts

def _do_shorts(opts, optstring, shortopts, args):
    while optstring != '':
        opt, optstring = optstring[0], optstring[1:]
        if _short_has_arg(opt, shortopts):
            if optstring == '':
                if not args:
                    raise GetoptError('option -%s requires argument' % opt, opt)
                optstring, args = args[0], args[1:]
            optarg, optstring = optstring, ''
        else:
            optarg = ''
        opts.append(('-' + opt, optarg))
    return opts, args

def _short_has_arg(opt, shortopts):
    for i in range(len(shortopts)):
        if opt == shortopts[i] != ':':
            return shortopts.startswith(':', i+1)
    raise GetoptError('option -%s not recognized' % opt, opt)


