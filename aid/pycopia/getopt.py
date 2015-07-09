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


