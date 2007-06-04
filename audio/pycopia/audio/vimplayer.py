#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

"""
Interface to alsaplayer from Vim! This module is meant to be used by vim's
embedded python interpreter.
"""

import sys, os
import atexit

from pycopia import timelib

from pycopia.audio import alsacontrol
from pycopia.audio import alsaplayer


try:
    import vim
except ImportError:
    from pycopia.vim import vimtest as vim

vim.command("set tm=2000")
vim.command("set backup")

current = None
players = {}
controllers = {}

def new_player():
    global players, current
    curp = players.keys()
    for ns in range(10):
        if ns not in curp:
            break
    else:
        print >>sys.stderr, "Too many players already."
        return
    players[ns] = alsaplayer.get_alsaplayer(ns)
    timelib.sleep(3)
    current = controllers[ns] = alsacontrol.get_session(ns)
    current.clear()
    print "new session: %d" % (ns,)

def switch_player():
    global controllers
    session = int(vim.eval("v:count"))
    apc = controllers.get(session, None)
    if apc is not None:
        current = apc
    else:
        print "no session", session

def remove_player(session=None):
    global players, controllers, current
    if session is None:
        session = int(vim.eval("v:count"))
    print "removing session %d..." % (session,),
    apc = controllers.get(session, None)
    if apc is not None:
        try:
            apc.quit()
        except:
            pass
        del controllers[session]
    timelib.sleep(2)
    p = players.get(session, None)
    if p:
        rv = p.wait()
        del players[session]
    if controllers:
        current = controllers.values()[0]
    else:
        current = None
    print rv

def print_sessions():
    global players
    for idx, s in players.items():
        print "%s: %s" % (idx, s)

def add_uri():
    global current
    try:
        path, pos = current.add_uri(vim.current.line)
    except:
        ex, val, tb = sys.exc_info()
        print >>sys.stderr, "could not add uri:", vim.current.line
        print >>sys.stderr, ex, val
    else:
        print "added: %s %s" % (path, pos and "(at %d secs)" % (pos,) or "")

def insert_uri():
    cp = vim.current.window.cursor[0]-1
    vim.current.buffer[cp:cp] = ["[%s]" % (current.get_uri())]

def seek_to():
    count = int(vim.eval("v:count"))
    if count == 0:
        count = int(vim.eval('inputdialog("Enter absolute Seconds:")'))
    print "seek to %d seconds, absolute." % (count,)
    current.set_position(count)

def cleanup():
    global current
    current = None
    for ns in controllers.keys():
        remove_player(ns)

def normalize():
    newbuf = [""]
    for line in vim.current.buffer:
        line = line.strip()
        if line:
            top = newbuf.pop()
            if top:
                top += " " + line
            else:
                top = "\t"+line
            newbuf.append(top)
        elif newbuf[-1]:
            newbuf.append("")
    vim.current.buffer[:] = newbuf
    vim.command("set ff=dos")


### initialization and setup ####

atexit.register(cleanup)

MAPPINGS = [
    r"menu <silent> Alsaplayer.New\ Player<Tab>(;np) :python vimplayer.new_player()<CR>",
    r"menu <silent> Alsaplayer.Remove\ Player<Tab>(;rp) :python vimplayer.remove_player()<CR>",
    r"menu <silent> Alsaplayer.Show\ Players<Tab>(;pp) :python vimplayer.print_sessions()<CR>",
    r"menu <silent> Alsaplayer.Add\ URI<Tab>(C-F2) :python vimplayer.add_uri()<CR>",
    r"menu <silent> Alsaplayer.Cleanup :python vimplayer.cleanup()<CR>",
    r"menu <silent> Alsaplayer.Normalize :python vimplayer.normalize()<CR>",

# alsaplayer session management
    "map ;np :python vimplayer.new_player()<CR>",
    "map ;rp :python vimplayer.remove_player()<CR>",
    "map ;pp :python vimplayer.print_sessions()<CR>",
    "map ;sp :python vimplayer.switch_player()<CR>",

# utility functions
    "map <silent> <Tab> :python vimplayer.seek_to()<CR>",
    "map <silent> <C-F1> :python print vimplayer.current<CR>",
    "map <silent> <F1> :python print vimplayer.insert_uri()<CR>",

# current player control
    "map <silent> <F2> :python vimplayer.current.play()<CR>",
    "map <silent> <C-F2> :python vimplayer.add_uri()<CR>",
    "map <silent> <F3> :python vimplayer.current.stop()<CR>",
    "map <silent> <F4> :python vimplayer.current.reverse()<CR>",

    "map <silent> <F5> :python vimplayer.current.pause()<CR>",
    "map <silent> <F6> :python vimplayer.current.unpause()<CR>",
    "map <silent> <F7> :python vimplayer.current.speedup()<CR>",
    "map <silent> <F8> :python vimplayer.current.speeddown()<CR>",

    "map <silent> <F9> :python vimplayer.current.backup(5)<CR>",
    "map <silent> <F10> :python vimplayer.current.backup(10)<CR>",
    "map <silent> <F11> :python vimplayer.current.backup(15)<CR>",
    "map <silent> <F12> :python vimplayer.current.backup(20)<CR>",
]


def mapkeys(MAPLIST):
    for mapping in MAPLIST:
        vim.command(mapping)

mapkeys(MAPPINGS)
del MAPPINGS
